/**
 * PR creation helper functions.
 * Extracted from worktree-handlers.ts for modularity.
 */
import type { WorktreeCreatePROptions } from '../../../shared/types';
import { PythonEnvManager } from '../../python-env-manager';
import { getEffectiveSourcePath } from '../../updater/path-resolver';
import { GIT_BRANCH_REGEX, PRINTABLE_CHARS_REGEX } from './worktree-git-utils';

// Maximum PR title length (GitHub's limit is 256 characters)
export const MAX_PR_TITLE_LENGTH = 256;

// Timeout for PR creation operations (2 minutes for network operations)
export const PR_CREATION_TIMEOUT_MS = 120000;

/**
 * Result of parsing JSON output from the create-pr Python script
 */
export interface ParsedPRResult {
  success: boolean;
  prUrl?: string;
  alreadyExists?: boolean;
  error?: string;
}

/**
 * Validate that a URL is a valid GitHub PR URL.
 * Supports both github.com and GitHub Enterprise instances (custom domains).
 * Only requires HTTPS protocol and non-empty hostname to allow any GH Enterprise URL.
 * @returns true if the URL is a valid HTTPS URL with a non-empty hostname
 */
export function isValidGitHubUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' && parsed.hostname.length > 0;
  } catch {
    return false;
  }
}

/**
 * Parse JSON output from the create-pr Python script
 * Handles both snake_case and camelCase field names
 * @returns ParsedPRResult if valid JSON found, null otherwise
 */
export function parsePRJsonOutput(stdout: string): ParsedPRResult | null {
  // Find the last complete JSON object in stdout (non-greedy, handles multiple objects)
  const jsonMatches = stdout.match(/\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}/g);
  const jsonMatch = jsonMatches && jsonMatches.length > 0 ? jsonMatches[jsonMatches.length - 1] : null;

  if (!jsonMatch) {
    return null;
  }

  try {
    const parsed = JSON.parse(jsonMatch);

    // Validate parsed JSON has expected shape
    if (typeof parsed !== 'object' || parsed === null) {
      return null;
    }

    // Extract and validate fields with proper type checking
    // Handle both snake_case (from Python) and camelCase field names
    // Default success to false to avoid masking failures when field is missing
    const rawPrUrl = typeof parsed.pr_url === 'string' ? parsed.pr_url :
                     typeof parsed.prUrl === 'string' ? parsed.prUrl : undefined;

    // Validate PR URL is a valid GitHub URL for robustness
    const validatedPrUrl = rawPrUrl && isValidGitHubUrl(rawPrUrl) ? rawPrUrl : undefined;

    return {
      success: typeof parsed.success === 'boolean' ? parsed.success : false,
      prUrl: validatedPrUrl,
      alreadyExists: typeof parsed.already_exists === 'boolean' ? parsed.already_exists :
                     typeof parsed.alreadyExists === 'boolean' ? parsed.alreadyExists : undefined,
      error: typeof parsed.error === 'string' ? parsed.error : undefined
    };
  } catch {
    return null;
  }
}

/**
 * Initialize Python environment for PR creation
 * @returns Error message if initialization fails, undefined on success
 */
export async function initializePythonEnvForPR(
  pythonEnvManager: PythonEnvManager
): Promise<string | undefined> {
  if (pythonEnvManager.isEnvReady()) {
    return undefined;
  }

  const autoBuildSource = getEffectiveSourcePath();
  if (!autoBuildSource) {
    return 'Python environment not ready and Auto Claude source not found';
  }

  const status = await pythonEnvManager.initialize(autoBuildSource);
  if (!status.ready) {
    return `Python environment not ready: ${status.error || 'Unknown error'}`;
  }

  return undefined;
}

/**
 * Generic retry wrapper with exponential backoff
 * @param operation - Async function to execute with retry
 * @param options - Retry configuration options
 * @returns Result of the operation or throws after all retries
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number;
    baseDelayMs?: number;
    onRetry?: (attempt: number, error: unknown) => void;
    shouldRetry?: (error: unknown) => boolean;
  } = {}
): Promise<T> {
  const { maxRetries: rawMaxRetries = 3, baseDelayMs = 100, onRetry, shouldRetry } = options;

  // Ensure at least one attempt is made (clamp to minimum of 1)
  const maxRetries = Math.max(1, rawMaxRetries);

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      const isLastAttempt = attempt === maxRetries;

      // Check if we should retry this error
      if (shouldRetry && !shouldRetry(error)) {
        throw error;
      }

      if (isLastAttempt) {
        throw error;
      }

      // Notify about retry
      onRetry?.(attempt, error);

      // Wait before retry (exponential backoff)
      await new Promise(r => setTimeout(r, baseDelayMs * 2 ** (attempt - 1)));
    }
  }

  // This should never be reached, but TypeScript needs it
  throw new Error('Retry loop exited unexpectedly');
}

/**
 * Build arguments for the create-pr Python script
 */
export function buildCreatePRArgs(
  runScript: string,
  specId: string,
  projectPath: string,
  options: WorktreeCreatePROptions | undefined,
  taskBaseBranch: string | undefined
): { args: string[]; validationError?: string } {
  const args = [
    runScript,
    '--spec', specId,
    '--project-dir', projectPath,
    '--create-pr'
  ];

  // Add optional arguments with validation
  if (options?.targetBranch) {
    // Validate branch name to prevent malformed git commands
    if (!GIT_BRANCH_REGEX.test(options.targetBranch)) {
      return { args: [], validationError: 'Invalid target branch name' };
    }
    args.push('--pr-target', options.targetBranch);
  }
  if (options?.title) {
    // Validate title for printable characters and length limit
    if (options.title.length > MAX_PR_TITLE_LENGTH) {
      return { args: [], validationError: `PR title exceeds maximum length of ${MAX_PR_TITLE_LENGTH} characters` };
    }
    if (!PRINTABLE_CHARS_REGEX.test(options.title)) {
      return { args: [], validationError: 'PR title contains invalid characters' };
    }
    // Reject titles starting with '-' to prevent argparse flag injection
    if (options.title.startsWith('-')) {
      return { args: [], validationError: 'PR title cannot start with a dash' };
    }
    args.push('--pr-title', options.title);
  }
  if (options?.draft) {
    args.push('--pr-draft');
  }

  // Add --base-branch if task was created with a specific base branch
  if (taskBaseBranch) {
    if (!GIT_BRANCH_REGEX.test(taskBaseBranch)) {
      return { args: [], validationError: 'Invalid base branch name' };
    }
    args.push('--base-branch', taskBaseBranch);
  }

  return { args };
}
