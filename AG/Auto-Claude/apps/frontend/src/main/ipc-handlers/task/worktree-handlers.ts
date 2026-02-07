import { ipcMain, BrowserWindow, app } from 'electron';
import { IPC_CHANNELS, AUTO_BUILD_PATHS, DEFAULT_APP_SETTINGS, DEFAULT_FEATURE_MODELS, DEFAULT_FEATURE_THINKING, MODEL_ID_MAP, THINKING_BUDGET_MAP, getSpecsDir } from '../../../shared/constants';
import type { IPCResult, WorktreeStatus, WorktreeDiff, WorktreeDiffFile, WorktreeMergeResult, WorktreeDiscardResult, WorktreeListResult, WorktreeListItem, WorktreeCreatePROptions, WorktreeCreatePRResult, SupportedIDE, SupportedTerminal, AppSettings } from '../../../shared/types';
import path from 'path';
import { existsSync, readdirSync, statSync, readFileSync } from 'fs';
import { execFileSync, spawn, spawnSync } from 'child_process';
import { projectStore } from '../../project-store';
import { getConfiguredPythonPath, PythonEnvManager, pythonEnvManager as pythonEnvManagerSingleton } from '../../python-env-manager';
import { getEffectiveSourcePath } from '../../updater/path-resolver';
import { getProfileEnv } from '../../rate-limit-detector';
import { findTaskAndProject, isEphemeralTaskId } from './shared';
import { parsePythonCommand } from '../../python-detector';
import { getToolPath } from '../../cli-tool-manager';
import {
  getTaskWorktreeDir,
  findTaskWorktree,
} from '../../worktree-paths';
import { persistPlanStatus, updateTaskMetadataPrUrl } from './plan-file-utils';
import { getIsolatedGitEnv } from '../../utils/git-isolation';
import { killProcessGracefully } from '../../platform';

// Import from extracted modules
import { detectInstalledTools, openInIDE, openInTerminal } from './worktree-ide-tools';
import type { DetectedTools } from './worktree-ide-tools';
import { fixMisconfiguredBareRepo, isGitWorkTree, GIT_BRANCH_REGEX, getTaskBaseBranch, getEffectiveBaseBranch } from './worktree-git-utils';
import { PR_CREATION_TIMEOUT_MS, parsePRJsonOutput, initializePythonEnvForPR, withRetry, buildCreatePRArgs } from './worktree-pr-utils';

// Mutex: prevent concurrent merge operations on the same task
const activeMerges = new Set<string>();

/**
 * Read utility feature settings (for commit message, merge resolver) from settings file
 */
function getUtilitySettings(): { model: string; modelId: string; thinkingLevel: string; thinkingBudget: number | null } {
  const settingsPath = path.join(app.getPath('userData'), 'settings.json');

  try {
    if (existsSync(settingsPath)) {
      const content = readFileSync(settingsPath, 'utf-8');
      const settings: AppSettings = { ...DEFAULT_APP_SETTINGS, ...JSON.parse(content) };

      // Get utility-specific settings
      const featureModels = settings.featureModels || DEFAULT_FEATURE_MODELS;
      const featureThinking = settings.featureThinking || DEFAULT_FEATURE_THINKING;

      const model = featureModels.utility || DEFAULT_FEATURE_MODELS.utility;
      const thinkingLevel = featureThinking.utility || DEFAULT_FEATURE_THINKING.utility;

      return {
        model,
        modelId: MODEL_ID_MAP[model] || MODEL_ID_MAP.haiku,
        thinkingLevel,
        thinkingBudget: thinkingLevel in THINKING_BUDGET_MAP ? THINKING_BUDGET_MAP[thinkingLevel] : THINKING_BUDGET_MAP.low
      };
    }
  } catch (error) {
    // Log parse errors to help diagnose corrupted settings
    console.warn('[getUtilitySettings] Failed to parse settings.json:', error);
  }

  // Return defaults if settings file doesn't exist or fails to parse
  return {
    model: DEFAULT_FEATURE_MODELS.utility,
    modelId: MODEL_ID_MAP[DEFAULT_FEATURE_MODELS.utility],
    thinkingLevel: DEFAULT_FEATURE_THINKING.utility,
    thinkingBudget: THINKING_BUDGET_MAP[DEFAULT_FEATURE_THINKING.utility]
  };
}

/**
 * Result of updating task status after PR creation
 */
interface TaskStatusUpdateResult {
  mainProjectStatus: boolean;
  mainProjectMetadata: boolean;
  worktreeStatus: boolean;
  worktreeMetadata: boolean;
}

/**
 * Update task status and metadata after PR creation
 * Updates both main project and worktree locations
 * @returns Result object indicating which updates succeeded/failed
 */
async function updateTaskStatusAfterPRCreation(
  specDir: string,
  worktreePath: string | null,
  prUrl: string,
  autoBuildPath: string | undefined,
  specId: string,
  debug: (...args: unknown[]) => void
): Promise<TaskStatusUpdateResult> {
  const result: TaskStatusUpdateResult = {
    mainProjectStatus: false,
    mainProjectMetadata: false,
    worktreeStatus: false,
    worktreeMetadata: false
  };

  const planPath = path.join(specDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);
  const metadataPath = path.join(specDir, 'task_metadata.json');

  // Await status persistence to ensure completion before resolving
  try {
    const persisted = await persistPlanStatus(planPath, 'pr_created');
    result.mainProjectStatus = persisted;
    debug('Main project status persisted to pr_created:', persisted);
  } catch (err) {
    debug('Failed to persist main project status:', err);
  }

  // Update metadata with prUrl in main project
  result.mainProjectMetadata = updateTaskMetadataPrUrl(metadataPath, prUrl);
  debug('Main project metadata updated with prUrl:', result.mainProjectMetadata);

  // Also persist to WORKTREE location (worktree takes priority when loading tasks)
  // This ensures the status persists after refresh since getTasks() prefers worktree version
  if (worktreePath) {
    const specsBaseDir = getSpecsDir(autoBuildPath);
    const worktreePlanPath = path.join(worktreePath, specsBaseDir, specId, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);
    const worktreeMetadataPath = path.join(worktreePath, specsBaseDir, specId, 'task_metadata.json');

    try {
      const persisted = await persistPlanStatus(worktreePlanPath, 'pr_created');
      result.worktreeStatus = persisted;
      debug('Worktree status persisted to pr_created:', persisted);
    } catch (err) {
      debug('Failed to persist worktree status:', err);
    }

    result.worktreeMetadata = updateTaskMetadataPrUrl(worktreeMetadataPath, prUrl);
    debug('Worktree metadata updated with prUrl:', result.worktreeMetadata);
  }

  return result;
}

/**
 * Register worktree management handlers
 */
export function registerWorktreeHandlers(
  pythonEnvManager: PythonEnvManager,
  getMainWindow: () => BrowserWindow | null
): void {
  /**
   * Get the worktree status for a task
   * Per-spec architecture: Each spec has its own worktree at .auto-claude/worktrees/tasks/{spec-name}/
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_STATUS,
    async (_, taskId: string): Promise<IPCResult<WorktreeStatus>> => {
      try {
        if (isEphemeralTaskId(taskId)) {
          return { success: false, error: 'Ephemeral task has no worktree' };
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          return { success: false, error: 'Task not found' };
        }

        // Find worktree at .auto-claude/worktrees/tasks/{spec-name}/
        const worktreePath = findTaskWorktree(project.path, task.specId);

        if (!worktreePath) {
          return {
            success: true,
            data: { exists: false }
          };
        }

        // Get branch info from git
        try {
          // Get current branch in worktree
          const branch = execFileSync(getToolPath('git'), ['rev-parse', '--abbrev-ref', 'HEAD'], {
            cwd: worktreePath,
            encoding: 'utf-8'
          }).trim();

          // Get base branch using proper fallback chain:
          // 1. Task metadata baseBranch, 2. Project settings mainBranch, 3. main/master detection
          const baseBranch = getEffectiveBaseBranch(project.path, task.specId, project.settings?.mainBranch, project.autoBuildPath);

          // Get user's current branch in main project (this is where changes will merge INTO)
          let currentProjectBranch: string | undefined;
          try {
            currentProjectBranch = execFileSync(getToolPath('git'), ['rev-parse', '--abbrev-ref', 'HEAD'], {
              cwd: project.path,
              encoding: 'utf-8'
            }).trim();
          } catch {
            // Ignore - might be in detached HEAD or git error
          }

          // Get commit count (cross-platform - no shell syntax)
          let commitCount = 0;
          try {
            const countOutput = execFileSync(getToolPath('git'), ['rev-list', '--count', `${baseBranch}..HEAD`], {
              cwd: worktreePath,
              encoding: 'utf-8',
              stdio: ['pipe', 'pipe', 'pipe']
            }).trim();
            commitCount = parseInt(countOutput, 10) || 0;
          } catch {
            commitCount = 0;
          }

          // Get diff stats
          let filesChanged = 0;
          let additions = 0;
          let deletions = 0;

          let diffStat = '';
          try {
            diffStat = execFileSync(getToolPath('git'), ['diff', '--stat', `${baseBranch}...HEAD`], {
              cwd: worktreePath,
              encoding: 'utf-8',
              stdio: ['pipe', 'pipe', 'pipe']
            }).trim();

            // Parse the summary line (e.g., "3 files changed, 50 insertions(+), 10 deletions(-)")
            const summaryMatch = diffStat.match(/(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?/);
            if (summaryMatch) {
              filesChanged = parseInt(summaryMatch[1], 10) || 0;
              additions = parseInt(summaryMatch[2], 10) || 0;
              deletions = parseInt(summaryMatch[3], 10) || 0;
            }
          } catch {
            // Ignore diff errors
          }

          return {
            success: true,
            data: {
              exists: true,
              worktreePath,
              branch,
              baseBranch,
              currentProjectBranch,
              commitCount,
              filesChanged,
              additions,
              deletions
            }
          };
        } catch (gitError) {
          console.error('Git error getting worktree status:', gitError);
          return {
            success: true,
            data: { exists: true, worktreePath }
          };
        }
      } catch (error) {
        console.error('Failed to get worktree status:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to get worktree status'
        };
      }
    }
  );

  /**
   * Get the diff for a task's worktree
   * Per-spec architecture: Each spec has its own worktree at .auto-claude/worktrees/tasks/{spec-name}/
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_DIFF,
    async (_, taskId: string): Promise<IPCResult<WorktreeDiff>> => {
      try {
        if (isEphemeralTaskId(taskId)) {
          return { success: false, error: 'Ephemeral task has no worktree' };
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          return { success: false, error: 'Task not found' };
        }

        // Find worktree at .auto-claude/worktrees/tasks/{spec-name}/
        const worktreePath = findTaskWorktree(project.path, task.specId);

        if (!worktreePath) {
          return { success: false, error: 'No worktree found for this task' };
        }

        // Get base branch using proper fallback chain:
        // 1. Task metadata baseBranch, 2. Project settings mainBranch, 3. main/master detection
        // Note: We do NOT use current HEAD as that may be a feature branch
        const baseBranch = getEffectiveBaseBranch(project.path, task.specId, project.settings?.mainBranch, project.autoBuildPath);

        // Get the diff with file stats
        const files: WorktreeDiffFile[] = [];

        let numstat = '';
        let nameStatus = '';
        try {
          // Get numstat for additions/deletions per file (cross-platform)
          numstat = execFileSync(getToolPath('git'), ['diff', '--numstat', `${baseBranch}...HEAD`], {
            cwd: worktreePath,
            encoding: 'utf-8',
            stdio: ['pipe', 'pipe', 'pipe']
          }).trim();

          // Get name-status for file status (cross-platform)
          nameStatus = execFileSync(getToolPath('git'), ['diff', '--name-status', `${baseBranch}...HEAD`], {
            cwd: worktreePath,
            encoding: 'utf-8',
            stdio: ['pipe', 'pipe', 'pipe']
          }).trim();

          // Parse name-status to get file statuses
          const statusMap: Record<string, 'added' | 'modified' | 'deleted' | 'renamed'> = {};
          nameStatus.split('\n').filter(Boolean).forEach((line: string) => {
            const [status, ...pathParts] = line.split('\t');
            const filePath = pathParts.join('\t'); // Handle files with tabs in name
            switch (status[0]) {
              case 'A': statusMap[filePath] = 'added'; break;
              case 'M': statusMap[filePath] = 'modified'; break;
              case 'D': statusMap[filePath] = 'deleted'; break;
              case 'R': statusMap[pathParts[1] || filePath] = 'renamed'; break;
              default: statusMap[filePath] = 'modified';
            }
          });

          // Parse numstat for additions/deletions
          numstat.split('\n').filter(Boolean).forEach((line: string) => {
            const [adds, dels, filePath] = line.split('\t');
            files.push({
              path: filePath,
              status: statusMap[filePath] || 'modified',
              additions: parseInt(adds, 10) || 0,
              deletions: parseInt(dels, 10) || 0
            });
          });
        } catch (diffError) {
          console.error('Error getting diff:', diffError);
        }

        // Generate summary
        const totalAdditions = files.reduce((sum, f) => sum + f.additions, 0);
        const totalDeletions = files.reduce((sum, f) => sum + f.deletions, 0);
        const summary = `${files.length} files changed, ${totalAdditions} insertions(+), ${totalDeletions} deletions(-)`;

        return {
          success: true,
          data: { files, summary }
        };
      } catch (error) {
        console.error('Failed to get worktree diff:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to get worktree diff'
        };
      }
    }
  );

  /**
   * Merge the worktree changes into the main branch
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_MERGE,
    async (_, taskId: string, options?: { noCommit?: boolean }): Promise<IPCResult<WorktreeMergeResult>> => {
      const isDebugMode = process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development';
      const debug = (...args: unknown[]) => {
        if (isDebugMode) {
          console.warn('[MERGE DEBUG]', ...args);
        }
      };

      // Prevent concurrent merge operations on the same task
      if (activeMerges.has(taskId)) {
        return { success: false, error: 'Merge already in progress for this task' };
      }
      activeMerges.add(taskId);

      try {
        debug('Handler called with taskId:', taskId, 'options:', options);

        if (isEphemeralTaskId(taskId)) {
          return { success: false, error: 'Ephemeral task has no worktree to merge' };
        }

        // Ensure Python environment is ready
        if (!pythonEnvManager.isEnvReady()) {
          const autoBuildSource = getEffectiveSourcePath();
          if (autoBuildSource) {
            const status = await pythonEnvManager.initialize(autoBuildSource);
            if (!status.ready) {
              return { success: false, error: `Python environment not ready: ${status.error || 'Unknown error'}` };
            }
          } else {
            return { success: false, error: 'Python environment not ready and Auto Claude source not found' };
          }
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          debug('Task or project not found');
          return { success: false, error: 'Task not found' };
        }

        debug('Found task:', task.specId, 'project:', project.path);

        // Auto-fix any misconfigured bare repo before merge operation
        // This prevents issues where git operations fail due to incorrect bare=true config
        if (fixMisconfiguredBareRepo(project.path)) {
          debug('Fixed misconfigured bare repository at:', project.path);
        }

        // Use run.py --merge to handle the merge
        const sourcePath = getEffectiveSourcePath();
        if (!sourcePath) {
          return { success: false, error: 'Auto Claude source not found' };
        }

        const runScript = path.join(sourcePath, 'run.py');
        const specDir = path.join(project.path, project.autoBuildPath || '.auto-claude', 'specs', task.specId);

        if (!existsSync(specDir)) {
          debug('Spec directory not found:', specDir);
          return { success: false, error: 'Spec directory not found' };
        }

        // Check worktree exists before merge
        const worktreePath = findTaskWorktree(project.path, task.specId);
        debug('Worktree path:', worktreePath, 'exists:', !!worktreePath);

        // Check if changes are already staged (for stage-only mode)
        if (options?.noCommit) {
          const stagedResult = spawnSync(getToolPath('git'), ['diff', '--staged', '--name-only'], {
            cwd: project.path,
            encoding: 'utf-8',
            env: getIsolatedGitEnv()
          });

          if (stagedResult.status === 0 && stagedResult.stdout?.trim()) {
            const stagedFiles = stagedResult.stdout.trim().split('\n');
            debug('Changes already staged:', stagedFiles.length, 'files');
            // Return success - changes are already staged
            return {
              success: true,
              data: {
                success: true,
                merged: false,
                message: `Changes already staged (${stagedFiles.length} files). Review with git diff --staged.`,
                staged: true,
                alreadyStaged: true,
                projectPath: project.path
              }
            };
          }
        }

        // Get git status before merge (only if project is a working tree, not a bare repo)
        if (isGitWorkTree(project.path)) {
          try {
            const gitStatusBefore = execFileSync(getToolPath('git'), ['status', '--short'], { cwd: project.path, encoding: 'utf-8' });
            debug('Git status BEFORE merge in main project:\n', gitStatusBefore || '(clean)');
            const gitBranch = execFileSync(getToolPath('git'), ['branch', '--show-current'], { cwd: project.path, encoding: 'utf-8' }).trim();
            debug('Current branch:', gitBranch);
          } catch (e) {
            debug('Failed to get git status before:', e);
          }
        } else {
          debug('Project is a bare repository - skipping pre-merge git status check');
        }

        const args = [
          runScript,
          '--spec', task.specId,
          '--project-dir', project.path,
          '--merge'
        ];

        // Add --no-commit flag if requested (stage changes without committing)
        if (options?.noCommit) {
          args.push('--no-commit');
        }

        // Add --base-branch with proper priority:
        // 1. Task metadata baseBranch (explicit task-level override)
        // 2. Project settings mainBranch (project-level default)
        // This matches the logic in execution-handlers.ts
        const taskBaseBranch = getTaskBaseBranch(specDir);
        const projectMainBranch = project.settings?.mainBranch;
        const effectiveBaseBranch = taskBaseBranch || projectMainBranch;

        if (effectiveBaseBranch) {
          args.push('--base-branch', effectiveBaseBranch);
          debug('Using base branch:', effectiveBaseBranch,
            `(source: ${taskBaseBranch ? 'task metadata' : 'project settings'})`);
        }

        // Use configured Python path (venv if ready, otherwise bundled/system)
        const pythonPath = getConfiguredPythonPath();
        debug('Running command:', pythonPath, args.join(' '));
        debug('Working directory:', sourcePath);

        // Get profile environment with OAuth token for AI merge resolution
        const profileEnv = getProfileEnv();
        debug('Profile env for merge:', {
          hasOAuthToken: !!profileEnv.CLAUDE_CODE_OAUTH_TOKEN,
          hasConfigDir: !!profileEnv.CLAUDE_CONFIG_DIR
        });

        return new Promise((resolve) => {
          const MERGE_TIMEOUT_MS = 600000; // 10 minutes timeout for AI merge operations with many files
          let timeoutId: NodeJS.Timeout | null = null;
          let resolved = false;

          // Get Python environment for bundled packages
          const pythonEnv = pythonEnvManagerSingleton.getPythonEnv();

          // Get utility settings for merge resolver
          const utilitySettings = getUtilitySettings();
          debug('Utility settings for merge:', utilitySettings);

          // Parse Python command to handle space-separated commands like "py -3"
          const [pythonCommand, pythonBaseArgs] = parsePythonCommand(pythonPath);
          const mergeProcess = spawn(pythonCommand, [...pythonBaseArgs, ...args], {
            cwd: sourcePath,
            env: {
              ...getIsolatedGitEnv(),
              ...pythonEnv,
              ...profileEnv,
              PYTHONUNBUFFERED: '1',
              PYTHONUTF8: '1',
              UTILITY_MODEL: utilitySettings.model,
              UTILITY_MODEL_ID: utilitySettings.modelId,
              UTILITY_THINKING_BUDGET: utilitySettings.thinkingBudget === null ? '' : (utilitySettings.thinkingBudget?.toString() || '')
            },
            stdio: ['ignore', 'pipe', 'pipe']
          });

          let stdout = '';
          let stderr = '';

          // Set up timeout to kill hung processes
          timeoutId = setTimeout(() => {
            if (!resolved) {
              debug('TIMEOUT: Merge process exceeded', MERGE_TIMEOUT_MS, 'ms, killing...');
              resolved = true;

              // Platform-specific process termination with fallback
              killProcessGracefully(mergeProcess, {
                debugPrefix: '[MERGE]',
                debug: isDebugMode
              });

              // Check if merge might have succeeded before the hang
              // Look for success indicators in the output
              const mayHaveSucceeded = stdout.includes('staged') ||
                                       stdout.includes('Successfully merged') ||
                                       stdout.includes('Changes from');

              if (mayHaveSucceeded) {
                debug('TIMEOUT: Process hung but merge may have succeeded based on output');
                const isStageOnly = options?.noCommit === true;
                resolve({
                  success: true,
                  data: {
                    success: true,
                    message: 'Changes staged (process timed out but merge appeared successful)',
                    staged: isStageOnly,
                    projectPath: isStageOnly ? project.path : undefined
                  }
                });
              } else {
                resolve({
                  success: false,
                  error: 'Merge process timed out. Check git status to see if merge completed.'
                });
              }
            }
          }, MERGE_TIMEOUT_MS);

          const MAX_BUFFER_SIZE = 5 * 1024 * 1024; // 5MB limit per stream
          mergeProcess.stdout.on('data', (data: Buffer) => {
            const chunk = data.toString();
            if (stdout.length < MAX_BUFFER_SIZE) {
              stdout += chunk.slice(0, MAX_BUFFER_SIZE - stdout.length);
            }
            debug('STDOUT:', chunk);
          });

          mergeProcess.stderr.on('data', (data: Buffer) => {
            const chunk = data.toString();
            if (stderr.length < MAX_BUFFER_SIZE) {
              stderr += chunk.slice(0, MAX_BUFFER_SIZE - stderr.length);
            }
            debug('STDERR:', chunk);
          });

          // Handler for when process exits
          const handleProcessExit = async (code: number | null, signal: string | null = null) => {
            if (resolved) return; // Prevent double-resolution
            resolved = true;
            if (timeoutId) clearTimeout(timeoutId);

            debug('Process exited with code:', code, 'signal:', signal);
            debug('Full stdout:', stdout);
            debug('Full stderr:', stderr);

            // Get git status after merge (only if project is a working tree, not a bare repo)
            if (isGitWorkTree(project.path)) {
              try {
                const gitStatusAfter = execFileSync(getToolPath('git'), ['status', '--short'], { cwd: project.path, encoding: 'utf-8' });
                debug('Git status AFTER merge in main project:\n', gitStatusAfter || '(clean)');
                const gitDiffStaged = execFileSync(getToolPath('git'), ['diff', '--staged', '--stat'], { cwd: project.path, encoding: 'utf-8' });
                debug('Staged changes:\n', gitDiffStaged || '(none)');
              } catch (e) {
                debug('Failed to get git status after:', e);
              }
            } else {
              debug('Project is a bare repository - skipping git status check (this is normal for worktree-based projects)');
            }

            if (code === 0) {
              const isStageOnly = options?.noCommit === true;

              // Verify changes were actually staged when stage-only mode is requested
              // This prevents false positives when merge was already committed previously
              let hasActualStagedChanges = false;
              let mergeAlreadyCommitted = false;

              if (isStageOnly) {
                // Only check staged changes if project is a working tree (not bare repo)
                if (isGitWorkTree(project.path)) {
                  try {
                    const gitDiffStaged = execFileSync(getToolPath('git'), ['diff', '--staged', '--stat'], { cwd: project.path, encoding: 'utf-8' });
                    hasActualStagedChanges = gitDiffStaged.trim().length > 0;
                    debug('Stage-only verification: hasActualStagedChanges:', hasActualStagedChanges);

                    if (!hasActualStagedChanges) {
                      // Check if worktree branch was already merged (merge commit exists)
                      const specBranch = `auto-claude/${task.specId}`;
                      try {
                        // Check if current branch contains all commits from spec branch
                        // git merge-base --is-ancestor returns exit code 0 if true, 1 if false
                        execFileSync(
                          getToolPath('git'),
                          ['merge-base', '--is-ancestor', specBranch, 'HEAD'],
                          { cwd: project.path, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }
                        );
                        // If we reach here, the command succeeded (exit code 0) - branch is merged
                        mergeAlreadyCommitted = true;
                        debug('Merge already committed check:', mergeAlreadyCommitted);
                      } catch {
                        // Exit code 1 means not merged, or branch may not exist
                        mergeAlreadyCommitted = false;
                        debug('Could not check merge status, assuming not merged');
                      }
                    }
                  } catch (e) {
                    debug('Failed to verify staged changes:', e);
                  }
                } else {
                  // For bare repos, skip staging verification - merge happens in worktree
                  debug('Project is a bare repository - skipping staged changes verification');
                }
              }

              // Determine actual status based on verification
              let newStatus: string;
              let planStatus: string;
              let message: string;
              let staged: boolean;

              if (isStageOnly && !hasActualStagedChanges && mergeAlreadyCommitted) {
                // Stage-only was requested but merge was already committed previously
                // Keep in human_review and let user explicitly mark as done (which will trigger cleanup confirmation)
                // This ensures user is in control of when the worktree is deleted
                newStatus = 'human_review';
                planStatus = 'review';
                message = 'Changes were already merged and committed. You can mark this task as complete when ready.';
                staged = false;
                debug('Stage-only requested but merge already committed. Keeping in human_review for user to confirm completion.');
                // NOTE: We intentionally do NOT auto-clean the worktree here.
                // User can drag the task to "Done" column which will show a confirmation dialog
                // asking if they want to delete the worktree and mark complete.
              } else if (isStageOnly && !hasActualStagedChanges) {
                // Stage-only was requested but no changes to stage (and not committed)
                // This could mean nothing to merge or an error - keep in human_review for investigation
                newStatus = 'human_review';
                planStatus = 'review';
                message = 'No changes to stage. The worktree may have no differences from the current branch.';
                staged = false;
                debug('Stage-only requested but no changes to stage.');
              } else if (isStageOnly) {
                // Stage-only with actual staged changes - expected success case
                newStatus = 'human_review';
                planStatus = 'review';
                message = 'Changes staged in main project. Review with git status and commit when ready.';
                staged = true;
              } else {
                // Full merge (not stage-only)
                newStatus = 'done';
                planStatus = 'completed';
                message = 'Changes merged successfully';
                staged = false;

                // Clean up worktree after successful full merge (fixes #243)
                // This allows drag-to-Done workflow since TASK_UPDATE_STATUS blocks 'done' when worktree exists
                try {
                  if (worktreePath && existsSync(worktreePath)) {
                    execFileSync(getToolPath('git'), ['worktree', 'remove', '--force', worktreePath], {
                      cwd: project.path,
                      encoding: 'utf-8'
                    });
                    debug('Worktree cleaned up after full merge:', worktreePath);

                    // Also delete the task branch since we merged successfully
                    const taskBranch = `auto-claude/${task.specId}`;
                    try {
                      // Validate branch name before using in git command
                      if (!GIT_BRANCH_REGEX.test(taskBranch)) {
                        debug('Invalid branch name, skipping deletion:', taskBranch);
                      } else {
                      execFileSync(getToolPath('git'), ['branch', '-D', taskBranch], {
                        cwd: project.path,
                        encoding: 'utf-8'
                      });
                      debug('Task branch deleted:', taskBranch);
                      }
                    } catch {
                      // Branch might not exist or already deleted
                    }
                  }
                } catch (cleanupErr) {
                  debug('Worktree cleanup failed (non-fatal):', cleanupErr);
                  // Non-fatal - merge succeeded, cleanup can be done manually
                }
              }

              debug('Merge result. isStageOnly:', isStageOnly, 'newStatus:', newStatus, 'staged:', staged);

              // Read suggested commit message if staging succeeded
              // OPTIMIZATION: Use async I/O to prevent blocking
              let suggestedCommitMessage: string | undefined;
              if (staged) {
                const commitMsgPath = path.join(specDir, 'suggested_commit_message.txt');
                try {
                  if (existsSync(commitMsgPath)) {
                    const { promises: fsPromises } = require('fs');
                    suggestedCommitMessage = (await fsPromises.readFile(commitMsgPath, 'utf-8')).trim();
                    debug('Read suggested commit message:', suggestedCommitMessage?.substring(0, 100));
                  }
                } catch (e) {
                  debug('Failed to read suggested commit message:', e);
                }
              }

              // Persist the status change to implementation_plan.json
              // Issue #243: We must update BOTH the main project's plan AND the worktree's plan (if it exists)
              // because ProjectStore prefers the worktree version when deduplicating tasks.
              // OPTIMIZATION: Use async I/O and parallel updates to prevent UI blocking
              // NOTE: The worktree has the same directory structure as main project
              const planPaths: { path: string; isMain: boolean }[] = [
                { path: path.join(specDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN), isMain: true },
              ];
              // Add worktree plan path if worktree exists
              if (worktreePath) {
                const worktreeSpecDir = path.join(worktreePath, project.autoBuildPath || '.auto-claude', 'specs', task.specId);
                planPaths.push({ path: path.join(worktreeSpecDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN), isMain: false });
              }

              const { promises: fsPromises } = require('fs');

              // Update plan file with retry logic for transient failures
              // Uses EAFP pattern (try/catch) instead of LBYL (existsSync check) to avoid TOCTOU race conditions
              const updatePlanWithRetry = async (planPath: string, isMain: boolean): Promise<boolean> => {
                // Helper to check if error is ENOENT (file not found)
                const isFileNotFound = (err: unknown): boolean =>
                  !!(err && typeof err === 'object' && 'code' in err && err.code === 'ENOENT');

                try {
                  await withRetry(
                    async () => {
                      const planContent = await fsPromises.readFile(planPath, 'utf-8');
                      const plan = JSON.parse(planContent);
                      plan.status = newStatus;
                      plan.planStatus = planStatus;
                      plan.updated_at = new Date().toISOString();
                      if (staged) {
                        plan.stagedAt = new Date().toISOString();
                        plan.stagedInMainProject = true;
                      }
                      await fsPromises.writeFile(planPath, JSON.stringify(plan, null, 2));

                      // Verify the write succeeded by reading back
                      const verifyContent = await fsPromises.readFile(planPath, 'utf-8');
                      const verifyPlan = JSON.parse(verifyContent);
                      if (verifyPlan.status !== newStatus || verifyPlan.planStatus !== planStatus) {
                        throw new Error('Write verification failed - status mismatch');
                      }
                    },
                    {
                      maxRetries: 3,
                      baseDelayMs: 100,
                      shouldRetry: (err) => !isFileNotFound(err) // Don't retry if file doesn't exist
                    }
                  );
                  return true;
                } catch (err) {
                  // File doesn't exist - nothing to update (not an error)
                  if (isFileNotFound(err)) {
                    return true;
                  }
                  // Only log error if main plan fails; worktree plan might legitimately be missing or read-only
                  if (isMain) {
                    console.error('Failed to persist task status to main plan after retries:', err);
                  } else {
                    debug('Failed to persist task status to worktree plan (non-critical):', err);
                  }
                  return false;
                }
              };

              const updatePlans = async () => {
                const results = await Promise.all(
                  planPaths.map(({ path: planPath, isMain }) =>
                    updatePlanWithRetry(planPath, isMain)
                  )
                );
                // Log if main plan update failed (first element)
                if (!results[0]) {
                  console.warn('Background plan update: main plan write may not have persisted');
                }
              };

              // IMPORTANT: Wait for plan updates to complete before responding (fixes #243)
              // Previously this was "fire and forget" which caused a race condition:
              // resolve() would return before files were written, and UI refresh would read old status
              try {
                await updatePlans();
              } catch (err) {
                debug('Plan update failed:', err);
                // Non-fatal: UI will still update, but status may not persist across refresh
              }

              const mainWindow = getMainWindow();
              if (mainWindow) {
                mainWindow.webContents.send(IPC_CHANNELS.TASK_STATUS_CHANGE, taskId, newStatus);
              }

              resolve({
                success: true,
                data: {
                  success: true,
                  message,
                  staged,
                  projectPath: staged ? project.path : undefined,
                  suggestedCommitMessage
                }
              });
            } else {
              // Check if there were actual merge conflicts
              // More specific patterns to avoid false positives from debug output like "files_with_conflicts: 0"
              const conflictPatterns = [
                /CONFLICT \(/i,                         // Git merge conflict marker
                /merge conflict/i,                      // Explicit merge conflict message
                /\bconflict detected\b/i,               // Our own conflict detection message
                /\bconflicts? found\b/i,                // "conflicts found" or "conflict found"
                /Automatic merge failed/i,             // Git's automatic merge failure message
              ];
              const combinedOutput = stdout + stderr;
              const hasConflicts = conflictPatterns.some(pattern => pattern.test(combinedOutput));
              debug('Merge failed. hasConflicts:', hasConflicts);

              resolve({
                success: true,
                data: {
                  success: false,
                  message: hasConflicts ? 'Merge conflicts detected' : `Merge failed: ${stderr || stdout}`,
                  conflictFiles: hasConflicts ? [] : undefined
                }
              });
            }
          };

          mergeProcess.on('close', (code: number | null, signal: string | null) => {
            handleProcessExit(code, signal);
          });

          // Also listen to 'exit' event in case 'close' doesn't fire
          mergeProcess.on('exit', (code: number | null, signal: string | null) => {
            // Give close event a chance to fire first with complete output
            setTimeout(() => handleProcessExit(code, signal), 100);
          });

          mergeProcess.on('error', (err: Error) => {
            if (resolved) return;
            resolved = true;
            if (timeoutId) clearTimeout(timeoutId);
            console.error('[MERGE] Process spawn error:', err);
            resolve({
              success: false,
              error: `Failed to run merge: ${err.message}`
            });
          });
        }).finally(() => {
          activeMerges.delete(taskId);
        });
      } catch (error) {
        activeMerges.delete(taskId);
        console.error('[MERGE] Exception in merge handler:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to merge worktree'
        };
      }
    }
  );

  /**
   * Preview merge conflicts before actually merging
   * Uses the smart merge system to analyze potential conflicts
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_MERGE_PREVIEW,
    async (_, taskId: string): Promise<IPCResult<WorktreeMergeResult>> => {
      console.warn('[IPC] TASK_WORKTREE_MERGE_PREVIEW called with taskId:', taskId);
      try {
        if (isEphemeralTaskId(taskId)) {
          return { success: false, error: 'Ephemeral task has no worktree' };
        }

        // Ensure Python environment is ready
        if (!pythonEnvManager.isEnvReady()) {
          console.warn('[IPC] Python environment not ready, initializing...');
          const autoBuildSource = getEffectiveSourcePath();
          if (autoBuildSource) {
            const status = await pythonEnvManager.initialize(autoBuildSource);
            if (!status.ready) {
              console.error('[IPC] Python environment failed to initialize:', status.error);
              return { success: false, error: `Python environment not ready: ${status.error || 'Unknown error'}` };
            }
          } else {
            console.error('[IPC] Auto Claude source not found');
            return { success: false, error: 'Python environment not ready and Auto Claude source not found' };
          }
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          console.error('[IPC] Task not found:', taskId);
          return { success: false, error: 'Task not found' };
        }
        console.warn('[IPC] Found task:', task.specId, 'project:', project.name);

        // Check for uncommitted changes in the main project (only if not a bare repo)
        let hasUncommittedChanges = false;
        let uncommittedFiles: string[] = [];
        if (isGitWorkTree(project.path)) {
          try {
            const gitStatus = execFileSync(getToolPath('git'), ['status', '--porcelain'], {
              cwd: project.path,
              encoding: 'utf-8'
            });

            if (gitStatus && gitStatus.trim()) {
              // Parse the status output to get file names
              // Format: XY filename (where X and Y are status chars, then space, then filename)
              uncommittedFiles = gitStatus
                .split('\n')
                .filter(line => line.trim())
                .map(line => line.substring(3).trim()); // Skip 2 status chars + 1 space, trim any trailing whitespace

              hasUncommittedChanges = uncommittedFiles.length > 0;
            }
          } catch (e) {
            console.error('[IPC] Failed to check git status:', e);
          }
        } else {
          console.warn('[IPC] Project is a bare repository - skipping uncommitted changes check');
        }

        const sourcePath = getEffectiveSourcePath();
        if (!sourcePath) {
          console.error('[IPC] Auto Claude source not found');
          return { success: false, error: 'Auto Claude source not found' };
        }

        const runScript = path.join(sourcePath, 'run.py');
        const specDir = path.join(project.path, project.autoBuildPath || '.auto-claude', 'specs', task.specId);
        const args = [
          runScript,
          '--spec', task.specId,
          '--project-dir', project.path,
          '--merge-preview'
        ];

        // Add --base-branch with proper priority:
        // 1. Task metadata baseBranch (explicit task-level override)
        // 2. Project settings mainBranch (project-level default)
        // This matches the logic in execution-handlers.ts
        const taskBaseBranch = getTaskBaseBranch(specDir);
        const projectMainBranch = project.settings?.mainBranch;
        const effectiveBaseBranch = taskBaseBranch || projectMainBranch;

        if (effectiveBaseBranch) {
          args.push('--base-branch', effectiveBaseBranch);
          console.warn('[IPC] Using base branch for preview:', effectiveBaseBranch,
            `(source: ${taskBaseBranch ? 'task metadata' : 'project settings'})`);
        }

        // Use configured Python path (venv if ready, otherwise bundled/system)
        const pythonPath = getConfiguredPythonPath();
        console.warn('[IPC] Running merge preview:', pythonPath, args.join(' '));

        // Get profile environment for consistency
        const previewProfileEnv = getProfileEnv();
        // Get Python environment for bundled packages
        const previewPythonEnv = pythonEnvManagerSingleton.getPythonEnv();

        return new Promise((resolve) => {
          const PREVIEW_TIMEOUT_MS = 120000; // 2 minutes timeout for preview
          const PREVIEW_MAX_BUFFER = 5 * 1024 * 1024; // 5MB buffer limit
          let previewTimedOut = false;

          // Parse Python command to handle space-separated commands like "py -3"
          const [pythonCommand, pythonBaseArgs] = parsePythonCommand(pythonPath);
          const previewProcess = spawn(pythonCommand, [...pythonBaseArgs, ...args], {
            cwd: sourcePath,
            env: { ...getIsolatedGitEnv(), ...previewPythonEnv, ...previewProfileEnv, PYTHONUNBUFFERED: '1', PYTHONUTF8: '1', DEBUG: 'true' }
          });

          const previewTimeout = setTimeout(() => {
            previewTimedOut = true;
            previewProcess.kill('SIGTERM');
            setTimeout(() => {
              try { previewProcess.kill('SIGKILL'); } catch { /* already dead */ }
            }, 5000);
          }, PREVIEW_TIMEOUT_MS);

          let stdout = '';
          let stderr = '';
          let stdoutTruncated = false;

          previewProcess.stdout.on('data', (data: Buffer) => {
            const chunk = data.toString();
            if (stdout.length < PREVIEW_MAX_BUFFER) {
              stdout += chunk.slice(0, PREVIEW_MAX_BUFFER - stdout.length);
              if (stdout.length >= PREVIEW_MAX_BUFFER) stdoutTruncated = true;
            }
            console.warn('[IPC] merge-preview stdout:', chunk.slice(0, 500));
          });

          previewProcess.stderr.on('data', (data: Buffer) => {
            const chunk = data.toString();
            if (stderr.length < PREVIEW_MAX_BUFFER) {
              stderr += chunk.slice(0, PREVIEW_MAX_BUFFER - stderr.length);
            }
            console.warn('[IPC] merge-preview stderr:', chunk.slice(0, 500));
          });

          previewProcess.on('close', (code: number) => {
            clearTimeout(previewTimeout);
            if (previewTimedOut) {
              resolve({ success: false, error: 'Preview timed out after 2 minutes' });
              return;
            }
            console.warn('[IPC] merge-preview process exited with code:', code);
            if (code === 0) {
              try {
                // Parse JSON output from Python
                const result = JSON.parse(stdout.trim());
                console.warn('[IPC] merge-preview result:', JSON.stringify(result, null, 2));
                resolve({
                  success: true,
                  data: {
                    success: result.success,
                    message: result.error || 'Preview completed',
                    preview: {
                      files: result.files || [],
                      conflicts: result.conflicts || [],
                      summary: result.summary || {
                        totalFiles: 0,
                        conflictFiles: 0,
                        totalConflicts: 0,
                        autoMergeable: 0,
                        hasGitConflicts: false
                      },
                      gitConflicts: result.gitConflicts || null,
                      // Include uncommitted changes info for the frontend
                      uncommittedChanges: hasUncommittedChanges ? {
                        hasChanges: true,
                        files: uncommittedFiles,
                        count: uncommittedFiles.length
                      } : null
                    }
                  }
                });
              } catch (parseError) {
                console.error('[IPC] Failed to parse preview result:', parseError);
                console.error('[IPC] stdout:', stdout);
                console.error('[IPC] stderr:', stderr);
                resolve({
                  success: false,
                  error: `Failed to parse preview result: ${stderr || stdout}`
                });
              }
            } else {
              console.error('[IPC] Preview failed with exit code:', code);
              console.error('[IPC] stderr:', stderr);
              console.error('[IPC] stdout:', stdout);
              resolve({
                success: false,
                error: `Preview failed: ${stderr || stdout}`
              });
            }
          });

          previewProcess.on('error', (err: Error) => {
            clearTimeout(previewTimeout);
            console.error('[IPC] merge-preview spawn error:', err);
            resolve({
              success: false,
              error: `Failed to run preview: ${err.message}`
            });
          });
        });
      } catch (error) {
        console.error('[IPC] TASK_WORKTREE_MERGE_PREVIEW error:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to preview merge'
        };
      }
    }
  );

  /**
   * Discard the worktree changes
   * Per-spec architecture: Each spec has its own worktree at .auto-claude/worktrees/tasks/{spec-name}/
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_DISCARD,
    async (_, taskId: string, skipStatusChange?: boolean): Promise<IPCResult<WorktreeDiscardResult>> => {
      try {
        if (isEphemeralTaskId(taskId)) {
          return { success: false, error: 'Ephemeral task has no worktree to discard' };
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          return { success: false, error: 'Task not found' };
        }

        // Find worktree at .auto-claude/worktrees/tasks/{spec-name}/
        const worktreePath = findTaskWorktree(project.path, task.specId);

        if (!worktreePath) {
          return {
            success: true,
            data: {
              success: true,
              message: 'No worktree to discard'
            }
          };
        }

        try {
          // Get the branch name before removing
          const branch = execFileSync(getToolPath('git'), ['rev-parse', '--abbrev-ref', 'HEAD'], {
            cwd: worktreePath,
            encoding: 'utf-8'
          }).trim();

          // Remove the worktree
          execFileSync(getToolPath('git'), ['worktree', 'remove', '--force', worktreePath], {
            cwd: project.path,
            encoding: 'utf-8'
          });

          // Delete the branch (validate name to prevent injection)
          try {
            if (GIT_BRANCH_REGEX.test(branch)) {
              execFileSync(getToolPath('git'), ['branch', '-D', branch], {
                cwd: project.path,
                encoding: 'utf-8'
              });
            }
          } catch {
            // Branch might already be deleted or not exist
          }

          // Only send status change to backlog if not skipped
          // (skip when caller will set a different status, e.g., 'done')
          if (!skipStatusChange) {
            const mainWindow = getMainWindow();
            if (mainWindow) {
              mainWindow.webContents.send(IPC_CHANNELS.TASK_STATUS_CHANGE, taskId, 'backlog');
            }
          }

          return {
            success: true,
            data: {
              success: true,
              message: 'Worktree discarded successfully'
            }
          };
        } catch (gitError) {
          console.error('Git error discarding worktree:', gitError);
          return {
            success: false,
            error: `Failed to discard worktree: ${gitError instanceof Error ? gitError.message : 'Unknown error'}`
          };
        }
      } catch (error) {
        console.error('Failed to discard worktree:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to discard worktree'
        };
      }
    }
  );

  /**
   * List all spec worktrees for a project
   * Per-spec architecture: Each spec has its own worktree at .auto-claude/worktrees/tasks/{spec-name}/
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_LIST_WORKTREES,
    async (_, projectId: string): Promise<IPCResult<WorktreeListResult>> => {
      try {
        const project = projectStore.getProject(projectId);
        if (!project) {
          return { success: false, error: 'Project not found' };
        }

        const worktrees: WorktreeListItem[] = [];
        const worktreesDir = getTaskWorktreeDir(project.path);

        // Helper to process a single worktree entry
        const processWorktreeEntry = (entry: string, entryPath: string) => {

          try {
            // Get branch info
            const branch = execFileSync(getToolPath('git'), ['rev-parse', '--abbrev-ref', 'HEAD'], {
              cwd: entryPath,
              encoding: 'utf-8'
            }).trim();

            // Get base branch using proper fallback chain:
            // 1. Task metadata baseBranch, 2. Project settings mainBranch, 3. main/master detection
            // Note: We do NOT use current HEAD as that may be a feature branch
            const baseBranch = getEffectiveBaseBranch(project.path, entry, project.settings?.mainBranch, project.autoBuildPath);

            // Get commit count (cross-platform - no shell syntax)
            let commitCount = 0;
            try {
              const countOutput = execFileSync(getToolPath('git'), ['rev-list', '--count', `${baseBranch}..HEAD`], {
                cwd: entryPath,
                encoding: 'utf-8',
                stdio: ['pipe', 'pipe', 'pipe']
              }).trim();
              commitCount = parseInt(countOutput, 10) || 0;
            } catch {
              commitCount = 0;
            }

            // Get diff stats (cross-platform - no shell syntax)
            let filesChanged = 0;
            let additions = 0;
            let deletions = 0;
            let diffStat = '';

            try {
              diffStat = execFileSync(getToolPath('git'), ['diff', '--shortstat', `${baseBranch}...HEAD`], {
                cwd: entryPath,
                encoding: 'utf-8',
                stdio: ['pipe', 'pipe', 'pipe']
              }).trim();

              const filesMatch = diffStat.match(/(\d+) files? changed/);
              const addMatch = diffStat.match(/(\d+) insertions?/);
              const delMatch = diffStat.match(/(\d+) deletions?/);

              if (filesMatch) filesChanged = parseInt(filesMatch[1], 10) || 0;
              if (addMatch) additions = parseInt(addMatch[1], 10) || 0;
              if (delMatch) deletions = parseInt(delMatch[1], 10) || 0;
            } catch {
              // Ignore diff errors
            }

            worktrees.push({
              specName: entry,
              path: entryPath,
              branch,
              baseBranch,
              commitCount,
              filesChanged,
              additions,
              deletions
            });
          } catch (gitError) {
            console.error(`Error getting info for worktree ${entry}:`, gitError);
            // Skip this worktree if we can't get git info
          }
        };

        // Scan worktrees directory
        if (existsSync(worktreesDir)) {
          const entries = readdirSync(worktreesDir);
          for (const entry of entries) {
            const entryPath = path.join(worktreesDir, entry);
            try {
              const stat = statSync(entryPath);
              if (stat.isDirectory()) {
                processWorktreeEntry(entry, entryPath);
              }
            } catch {
              // Skip entries that can't be stat'd
            }
          }
        }

        return { success: true, data: { worktrees } };
      } catch (error) {
        console.error('Failed to list worktrees:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to list worktrees'
        };
      }
    }
  );

  /**
   * Detect installed IDEs and terminals on the system
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_DETECT_TOOLS,
    async (): Promise<IPCResult<DetectedTools>> => {
      try {
        const tools = await detectInstalledTools();
        return { success: true, data: tools };
      } catch (error) {
        console.error('Failed to detect tools:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to detect installed tools'
        };
      }
    }
  );

  /**
   * Open a worktree directory in the specified IDE
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_OPEN_IN_IDE,
    async (_, worktreePath: string, ide: SupportedIDE, customPath?: string): Promise<IPCResult<{ opened: boolean }>> => {
      try {
        if (!existsSync(worktreePath)) {
          return { success: false, error: 'Worktree path does not exist' };
        }

        const result = await openInIDE(worktreePath, ide, customPath);
        if (!result.success) {
          return { success: false, error: result.error };
        }

        return { success: true, data: { opened: true } };
      } catch (error) {
        console.error('Failed to open in IDE:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to open in IDE'
        };
      }
    }
  );

  /**
   * Open a worktree directory in the specified terminal
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_OPEN_IN_TERMINAL,
    async (_, worktreePath: string, terminal: SupportedTerminal, customPath?: string): Promise<IPCResult<{ opened: boolean }>> => {
      try {
        if (!existsSync(worktreePath)) {
          return { success: false, error: 'Worktree path does not exist' };
        }

        const result = await openInTerminal(worktreePath, terminal, customPath);
        if (!result.success) {
          return { success: false, error: result.error };
        }

        return { success: true, data: { opened: true } };
      } catch (error) {
        console.error('Failed to open in terminal:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to open in terminal'
        };
      }
    }
  );

  /**
   * Clear the staged state for a task
   * This allows the user to re-stage changes if needed
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_CLEAR_STAGED_STATE,
    async (_, taskId: string): Promise<IPCResult<{ cleared: boolean }>> => {
      try {
        if (isEphemeralTaskId(taskId)) {
          return { success: true, data: { cleared: true } };
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          return { success: false, error: 'Task not found' };
        }

        const specsBaseDir = getSpecsDir(project.autoBuildPath);
        const specDir = path.join(project.path, specsBaseDir, task.specId);
        const planPath = path.join(specDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);

        // Use EAFP pattern (try/catch) instead of LBYL (existsSync check) to avoid TOCTOU race conditions
        const { promises: fsPromises } = require('fs');
        const isFileNotFound = (err: unknown): boolean =>
          !!(err && typeof err === 'object' && 'code' in err && err.code === 'ENOENT');

        // Read, update, and write the plan file
        let planContent: string;
        try {
          planContent = await fsPromises.readFile(planPath, 'utf-8');
        } catch (readErr) {
          if (isFileNotFound(readErr)) {
            return { success: false, error: 'Implementation plan not found' };
          }
          throw readErr;
        }

        const plan = JSON.parse(planContent);

        // Clear the staged state flags
        delete plan.stagedInMainProject;
        delete plan.stagedAt;
        plan.updated_at = new Date().toISOString();

        await fsPromises.writeFile(planPath, JSON.stringify(plan, null, 2));

        // Also update worktree plan if it exists
        const worktreePath = findTaskWorktree(project.path, task.specId);
        if (worktreePath) {
          const worktreePlanPath = path.join(worktreePath, specsBaseDir, task.specId, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);
          try {
            const worktreePlanContent = await fsPromises.readFile(worktreePlanPath, 'utf-8');
            const worktreePlan = JSON.parse(worktreePlanContent);
            delete worktreePlan.stagedInMainProject;
            delete worktreePlan.stagedAt;
            worktreePlan.updated_at = new Date().toISOString();
            await fsPromises.writeFile(worktreePlanPath, JSON.stringify(worktreePlan, null, 2));
          } catch (e) {
            // Non-fatal - worktree plan update is best-effort
            // ENOENT is expected when worktree has no plan file
            if (!isFileNotFound(e)) {
              console.warn('[CLEAR_STAGED_STATE] Failed to update worktree plan:', e);
            }
          }
        }

        // Invalidate tasks cache to force reload
        projectStore.invalidateTasksCache(project.id);

        return { success: true, data: { cleared: true } };
      } catch (error) {
        console.error('Failed to clear staged state:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to clear staged state'
        };
      }
    }
  );

  /**
   * Create a Pull Request from the worktree branch
   * Pushes the branch to origin and creates a GitHub PR using gh CLI
   */
  ipcMain.handle(
    IPC_CHANNELS.TASK_WORKTREE_CREATE_PR,
    async (_, taskId: string, options?: WorktreeCreatePROptions): Promise<IPCResult<WorktreeCreatePRResult>> => {
      const isDebugMode = process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development';
      const debug = (...args: unknown[]) => {
        if (isDebugMode) {
          console.warn('[CREATE_PR DEBUG]', ...args);
        }
      };

      try {
        debug('Handler called with taskId:', taskId, 'options:', options);

        if (isEphemeralTaskId(taskId)) {
          return { success: false, error: 'Ephemeral task has no worktree for PR creation' };
        }

        // Ensure Python environment is ready
        const pythonEnvError = await initializePythonEnvForPR(pythonEnvManager);
        if (pythonEnvError) {
          return { success: false, error: pythonEnvError };
        }

        const { task, project } = findTaskAndProject(taskId);
        if (!task || !project) {
          debug('Task or project not found');
          return { success: false, error: 'Task not found' };
        }

        debug('Found task:', task.specId, 'project:', project.path);

        // Use run.py --create-pr to handle the PR creation
        const sourcePath = getEffectiveSourcePath();
        if (!sourcePath) {
          return { success: false, error: 'Auto Claude source not found' };
        }

        const runScript = path.join(sourcePath, 'run.py');
        const specDir = path.join(project.path, project.autoBuildPath || '.auto-claude', 'specs', task.specId);

        // Use EAFP pattern - try to read specDir and catch ENOENT
        try {
          statSync(specDir);
        } catch (err) {
          if (err && typeof err === 'object' && 'code' in err && err.code === 'ENOENT') {
            debug('Spec directory not found:', specDir);
            return { success: false, error: 'Spec directory not found' };
          }
          throw err; // Re-throw unexpected errors
        }

        // Check worktree exists before creating PR
        const worktreePath = findTaskWorktree(project.path, task.specId);
        if (!worktreePath) {
          debug('No worktree found for spec:', task.specId);
          return { success: false, error: 'No worktree found for this task' };
        }
        debug('Worktree path:', worktreePath);

        // Build arguments using helper function
        const taskBaseBranch = getTaskBaseBranch(specDir);
        const { args, validationError } = buildCreatePRArgs(
          runScript,
          task.specId,
          project.path,
          options,
          taskBaseBranch
        );
        if (validationError) {
          return { success: false, error: validationError };
        }
        if (taskBaseBranch) {
          debug('Using stored base branch:', taskBaseBranch);
        }

        // Use configured Python path
        const pythonPath = getConfiguredPythonPath();
        debug('Running command:', pythonPath, args.join(' '));
        debug('Working directory:', sourcePath);

        // Get profile environment with OAuth token
        const profileEnv = getProfileEnv();

        return new Promise((resolve) => {
          let timeoutId: NodeJS.Timeout | null = null;
          let resolved = false;

          // Get Python environment for bundled packages
          const pythonEnv = pythonEnvManagerSingleton.getPythonEnv();

          // Get gh CLI path to pass to Python backend
          const ghCliPath = getToolPath('gh');

          // Parse Python command to handle space-separated commands like "py -3"
          const [pythonCommand, pythonBaseArgs] = parsePythonCommand(pythonPath);
          const createPRProcess = spawn(pythonCommand, [...pythonBaseArgs, ...args], {
            cwd: sourcePath,
            env: {
              ...getIsolatedGitEnv(),
              ...pythonEnv,
              ...profileEnv,
              GITHUB_CLI_PATH: ghCliPath,
              PYTHONUNBUFFERED: '1',
              PYTHONUTF8: '1'
            },
            stdio: ['ignore', 'pipe', 'pipe']
          });

          let stdout = '';
          let stderr = '';

          // Set up timeout to kill hung processes
          timeoutId = setTimeout(() => {
            if (!resolved) {
              debug('TIMEOUT: Create PR process exceeded', PR_CREATION_TIMEOUT_MS, 'ms, killing...');
              resolved = true;

              // Platform-specific process termination with fallback
              killProcessGracefully(createPRProcess, {
                debugPrefix: '[PR_CREATION]',
                debug: isDebugMode
              });

              resolve({
                success: false,
                error: 'PR creation timed out. Check if the PR was created on GitHub.'
              });
            }
          }, PR_CREATION_TIMEOUT_MS);

          createPRProcess.stdout.on('data', (data: Buffer) => {
            const chunk = data.toString();
            stdout += chunk;
            debug('STDOUT:', chunk);
          });

          createPRProcess.stderr.on('data', (data: Buffer) => {
            const chunk = data.toString();
            stderr += chunk;
            debug('STDERR:', chunk);
          });

          /**
           * Handle process exit - shared logic for both 'close' and 'exit' events.
           * Parses JSON output, updates task status if PR was created, and resolves the promise.
           *
           * @param code - Process exit code (0 = success, non-zero = failure)
           * @param eventSource - Which event triggered this ('close' or 'exit') for debug logging
           */
          const handleCreatePRProcessExit = async (code: number | null, eventSource: 'close' | 'exit'): Promise<void> => {
            if (resolved) return;
            resolved = true;
            if (timeoutId) clearTimeout(timeoutId);

            debug(`Process exited via ${eventSource} event with code:`, code);
            debug('Full stdout:', stdout);
            debug('Full stderr:', stderr);

            if (code === 0) {
              // Parse JSON output using helper function
              const result = parsePRJsonOutput(stdout);
              if (result) {
                debug('Parsed result:', result);

                // Only update task status if a NEW PR was created (not if it already exists)
                if (result.success !== false && result.prUrl && !result.alreadyExists) {
                  await updateTaskStatusAfterPRCreation(
                    specDir,
                    worktreePath,
                    result.prUrl,
                    project.autoBuildPath,
                    task.specId,
                    debug
                  );
                } else if (result.alreadyExists) {
                  debug('PR already exists, not updating task status');
                }

                resolve({
                  success: true,
                  data: {
                    success: result.success,
                    prUrl: result.prUrl,
                    error: result.error,
                    alreadyExists: result.alreadyExists
                  }
                });
              } else {
                // No JSON found, but process succeeded
                debug('No JSON in output, assuming success');
                resolve({
                  success: true,
                  data: {
                    success: true,
                    prUrl: undefined
                  }
                });
              }
            } else {
              debug('Process failed with code:', code);

              // Try to parse JSON from stdout even on failure
              const result = parsePRJsonOutput(stdout);
              if (result) {
                debug('Parsed error result:', result);
                resolve({
                  success: false,
                  error: result.error || 'Failed to create PR'
                });
              } else {
                // Fallback to raw output if JSON parsing fails
                // Prefer stdout over stderr since stderr often contains debug messages
                resolve({
                  success: false,
                  error: stdout || stderr || 'Failed to create PR'
                });
              }
            }
          };

          createPRProcess.on('close', (code: number | null) => {
            handleCreatePRProcessExit(code, 'close');
          });

          // Also listen to 'exit' event in case 'close' doesn't fire
          createPRProcess.on('exit', (code: number | null) => {
            // Give close event a chance to fire first with complete output
            setTimeout(() => handleCreatePRProcessExit(code, 'exit'), 100);
          });

          createPRProcess.on('error', (err: Error) => {
            if (resolved) return;
            resolved = true;
            if (timeoutId) clearTimeout(timeoutId);
            debug('Process spawn error:', err);
            resolve({
              success: false,
              error: `Failed to run create-pr: ${err.message}`
            });
          });
        });
      } catch (error) {
        console.error('[CREATE_PR] Exception in handler:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to create PR'
        };
      }
    }
  );
}
