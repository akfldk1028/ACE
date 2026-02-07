/**
 * Browser mock for window.electronAPI
 * This allows the app to run in a regular browser for UI development/testing
 *
 * This module aggregates all mock implementations from separate modules
 * for better code organization and maintainability.
 */

import type { ElectronAPI } from '../../shared/types';
import {
  projectMock,
  taskMock,
  workspaceMock,
  terminalMock,
  claudeProfileMock,
  contextMock,
  integrationMock,
  changelogMock,
  insightsMock,
  infrastructureMock,
  settingsMock
} from './mocks';

// Check if we're in a browser (not Electron)
const isElectron = typeof window !== 'undefined' && window.electronAPI !== undefined;

/**
 * Create mock electronAPI for browser
 * Aggregates all mock implementations from separate modules
 */
const browserMockAPI: ElectronAPI = {
  // Project Operations
  ...projectMock,

  // Task Operations
  ...taskMock,

  // Workspace Management
  ...workspaceMock,

  // Terminal Operations
  ...terminalMock,

  // Claude Profile Management
  ...claudeProfileMock,

  // Settings
  ...settingsMock,

  // Roadmap Operations
  getRoadmap: async () => ({
    success: true,
    data: null
  }),

  getRoadmapStatus: async () => ({
    success: true,
    data: { isRunning: false }
  }),

  saveRoadmap: async () => ({
    success: true
  }),

  generateRoadmap: (_projectId: string, _enableCompetitorAnalysis?: boolean, _refreshCompetitorAnalysis?: boolean) => {
    console.warn('[Browser Mock] generateRoadmap called');
  },

  refreshRoadmap: (_projectId: string, _enableCompetitorAnalysis?: boolean, _refreshCompetitorAnalysis?: boolean) => {
    console.warn('[Browser Mock] refreshRoadmap called');
  },

  updateFeatureStatus: async () => ({ success: true }),

  convertFeatureToSpec: async (projectId: string, _featureId: string) => ({
    success: true,
    data: {
      id: `task-${Date.now()}`,
      specId: '',
      projectId,
      title: 'Converted Feature',
      description: 'Feature converted from roadmap',
      status: 'backlog' as const,
      subtasks: [],
      logs: [],
      createdAt: new Date(),
      updatedAt: new Date()
    }
  }),

  stopRoadmap: async () => ({ success: true }),

  // Roadmap Event Listeners
  onRoadmapProgress: () => () => {},
  onRoadmapComplete: () => () => {},
  onRoadmapError: () => () => {},
  onRoadmapStopped: () => () => {},
  // Context Operations
  ...contextMock,

  // Environment Configuration & Integration Operations
  ...integrationMock,

  // Changelog & Release Operations
  ...changelogMock,

  // Insights Operations
  ...insightsMock,

  // Infrastructure & Docker Operations
  ...infrastructureMock,

  // API Profile Management (custom Anthropic-compatible endpoints)
  getAPIProfiles: async () => ({
    success: true,
    data: {
      profiles: [],
      activeProfileId: null,
      version: 1
    }
  }),

  saveAPIProfile: async (profile) => ({
    success: true,
    data: {
      id: `mock-profile-${Date.now()}`,
      ...profile,
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
  }),

  updateAPIProfile: async (profile) => ({
    success: true,
    data: {
      ...profile,
      updatedAt: Date.now()
    }
  }),

  deleteAPIProfile: async (_profileId: string) => ({
    success: true
  }),

  setActiveAPIProfile: async (_profileId: string | null) => ({
    success: true
  }),

  testConnection: async (_baseUrl: string, _apiKey: string, _signal?: AbortSignal) => ({
    success: true,
    data: {
      success: true,
      message: 'Connection successful (mock)'
    }
  }),

  discoverModels: async (_baseUrl: string, _apiKey: string, _signal?: AbortSignal) => ({
    success: true,
    data: {
      models: []
    }
  }),

  // GitHub API
  github: {
    getGitHubRepositories: async () => ({ success: true, data: [] }),
    getGitHubIssues: async () => ({ success: true, data: { issues: [], hasMore: false } }),
    getGitHubIssue: async () => ({ success: true, data: null as any }),
    getIssueComments: async () => ({ success: true, data: [] }),
    checkGitHubConnection: async () => ({ success: true, data: { connected: false, repoFullName: undefined, error: undefined } }),
    investigateGitHubIssue: () => {},
    importGitHubIssues: async () => ({ success: true, data: { success: true, imported: 0, failed: 0, issues: [] } }),
    createGitHubRelease: async () => ({ success: true, data: { url: '' } }),
    suggestReleaseVersion: async () => ({ success: true, data: { suggestedVersion: '1.0.0', currentVersion: '0.0.0', bumpType: 'minor' as const, commitCount: 0, reason: 'Initial' } }),
    checkGitHubCli: async () => ({ success: true, data: { installed: false } }),
    checkGitHubAuth: async () => ({ success: true, data: { authenticated: false } }),
    startGitHubAuth: async () => ({ success: true, data: { success: false } }),
    getGitHubToken: async () => ({ success: true, data: { token: '' } }),
    getGitHubUser: async () => ({ success: true, data: { username: '' } }),
    listGitHubUserRepos: async () => ({ success: true, data: { repos: [] } }),
    detectGitHubRepo: async () => ({ success: true, data: '' }),
    getGitHubBranches: async () => ({ success: true, data: [] }),
    createGitHubRepo: async () => ({ success: true, data: { fullName: '', url: '' } }),
    addGitRemote: async () => ({ success: true, data: { remoteUrl: '' } }),
    listGitHubOrgs: async () => ({ success: true, data: { orgs: [] } }),
    onGitHubAuthDeviceCode: () => () => {},
    onGitHubInvestigationProgress: () => () => {},
    onGitHubInvestigationComplete: () => () => {},
    onGitHubInvestigationError: () => () => {},
    getAutoFixConfig: async () => null,
    saveAutoFixConfig: async () => true,
    getAutoFixQueue: async () => [],
    checkAutoFixLabels: async () => [],
    checkNewIssues: async () => [],
    startAutoFix: () => {},
    onAutoFixProgress: () => () => {},
    onAutoFixComplete: () => () => {},
    onAutoFixError: () => () => {},
    listPRs: async () => [],
    getPR: async () => null,
    runPRReview: () => {},
    cancelPRReview: async () => true,
    postPRReview: async () => true,
    postPRComment: async () => true,
    mergePR: async () => true,
    assignPR: async () => true,
    markReviewPosted: async () => true,
    getPRReview: async () => null,
    getPRReviewsBatch: async () => ({}),
    deletePRReview: async () => true,
    checkNewCommits: async () => ({ hasNewCommits: false, newCommitCount: 0 }),
    checkMergeReadiness: async () => ({ isDraft: false, mergeable: 'UNKNOWN' as const, isBehind: false, ciStatus: 'none' as const, blockers: [] }),
    updatePRBranch: async () => ({ success: true }),
    runFollowupReview: () => {},
    getPRLogs: async () => null,
    getWorkflowsAwaitingApproval: async () => ({ awaiting_approval: 0, workflow_runs: [], can_approve: false }),
    approveWorkflow: async () => true,
    onPRReviewProgress: () => () => {},
    onPRReviewComplete: () => () => {},
    onPRReviewError: () => () => {},
    batchAutoFix: () => {},
    getBatches: async () => [],
    onBatchProgress: () => () => {},
    onBatchComplete: () => () => {},
    onBatchError: () => () => {},
    // Analyze & Group Issues (proactive workflow)
    analyzeIssuesPreview: () => {},
    approveBatches: async () => ({ success: true, batches: [] }),
    onAnalyzePreviewProgress: () => () => {},
    onAnalyzePreviewComplete: () => () => {},
    onAnalyzePreviewError: () => () => {}
  },

  // Claude Code Operations
  checkClaudeCodeVersion: async () => ({
    success: true,
    data: {
      installed: '1.0.0',
      latest: '1.0.0',
      isOutdated: false,
      path: '/usr/local/bin/claude',
      detectionResult: {
        found: true,
        version: '1.0.0',
        path: '/usr/local/bin/claude',
        source: 'system-path' as const,
        message: 'Claude Code CLI found'
      }
    }
  }),
  installClaudeCode: async () => ({
    success: true,
    data: { command: 'npm install -g @anthropic-ai/claude-code' }
  }),
  getClaudeCodeVersions: async () => ({
    success: true,
    data: {
      versions: ['1.0.5', '1.0.4', '1.0.3', '1.0.2', '1.0.1', '1.0.0']
    }
  }),
  installClaudeCodeVersion: async (version: string) => ({
    success: true,
    data: { command: `npm install -g @anthropic-ai/claude-code@${version}`, version }
  }),
  getClaudeCodeInstallations: async () => ({
    success: true,
    data: {
      installations: [
        {
          path: '/usr/local/bin/claude',
          version: '1.0.0',
          source: 'system-path' as const,
          isActive: true,
        }
      ],
      activePath: '/usr/local/bin/claude',
    }
  }),
  setClaudeCodeActivePath: async (cliPath: string) => ({
    success: true,
    data: { path: cliPath }
  }),

  // Terminal Worktree Operations
  createTerminalWorktree: async () => ({
    success: false,
    error: 'Not available in browser mode'
  }),
  listTerminalWorktrees: async () => ({
    success: true,
    data: []
  }),
  removeTerminalWorktree: async () => ({
    success: false,
    error: 'Not available in browser mode'
  }),
  listOtherWorktrees: async () => ({
    success: true,
    data: []
  }),

  // MCP Server Health Check Operations
  checkMcpHealth: async (server) => ({
    success: true,
    data: {
      serverId: server.id,
      status: 'unknown' as const,
      message: 'Health check not available in browser mode',
      checkedAt: new Date().toISOString()
    }
  }),
  testMcpConnection: async (server) => ({
    success: true,
    data: {
      serverId: server.id,
      success: false,
      message: 'Connection test not available in browser mode'
    }
  }),

  // Debug Operations
  getDebugInfo: async () => ({
    systemInfo: {
      appVersion: '0.0.0-browser-mock',
      platform: 'browser',
      isPackaged: 'false'
    },
    recentErrors: [],
    logsPath: '/mock/logs',
    debugReport: '[Browser Mock] Debug report not available in browser mode'
  }),
  openLogsFolder: async () => ({ success: false, error: 'Not available in browser mode' }),
  copyDebugInfo: async () => ({ success: false, error: 'Not available in browser mode' }),
  getRecentErrors: async () => [],
  listLogFiles: async () => [],

  // A2A Operations
  discoverA2AAgents: async () => ({
    success: true,
    data: {
      connected: false,
      autogenStudioOnline: false,
      agentCount: 0,
      onlineAgentCount: 0,
      agents: [],
      error: 'Not available in browser mode'
    }
  }),
  checkA2AAgentHealth: async () => ({ success: true, data: { online: false, error: 'Not available in browser mode' } }),
  sendA2AMessage: async () => ({ success: false, error: 'Not available in browser mode' }),

  // ★ SharedMemory (8101) 사용 안함! - 2026-01-25 확정
  // 모든 SharedMemory 함수는 빈 값 반환 (호출해도 8101에 연결 안 함)
  sharedMemoryHealth: async () => ({ success: true, data: { online: false, url: 'DISABLED' } }),
  sharedMemoryGet: async (_key: string) => ({ success: true, data: null }),
  sharedMemoryStore: async () => ({ success: false, error: 'SharedMemory disabled' }),
  sharedMemoryListKeys: async () => ({ success: true, data: [] }),
  sharedMemoryGetA2AHistory: async () => ({ success: true, data: [] }),

  // AutoGen Studio sync (★ Vite 프록시 사용)
  // ★ 2026-01-25: Vite 프록시 사용 (/api/autogen → 8081) - CORS 회피
  getAutogenLatest: async () => {
    try {
      // ★ Vite 프록시 사용 (electron.vite.config.ts: /api/autogen → 8081/api)
      const sessionsResponse = await fetch('/api/autogen/sessions/?user_id=guestuser@gmail.com', {
        headers: { Accept: 'application/json' }
      });

      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        const sessions = sessionsData.data || [];

        // 최신 세션에서 완료된 run 찾기
        for (const session of sessions.slice(0, 5)) {
          const runsResponse = await fetch(`/api/autogen/sessions/${session.id}/runs?user_id=guestuser@gmail.com`, {
            headers: { Accept: 'application/json' }
          });

          if (runsResponse.ok) {
            const runsData = await runsResponse.json();
            const runs = runsData.data?.runs || [];

            // 완료된 run 찾기
            const completedRun = runs.find((r: { status: string }) => r.status?.toUpperCase() === 'COMPLETE');
            if (completedRun) {
              // 결과 파싱
              let taskContent = '';
              let resultContent = '';
              const agentsUsed: string[] = [];

              // 태스크 추출
              const taskMsgs = completedRun.task?.content || [];
              for (const msg of taskMsgs) {
                if (msg.source === 'user') {
                  taskContent = msg.content || '';
                  break;
                }
              }

              // 결과 메시지 추출
              const messages = completedRun.team_result?.task_result?.messages || [];
              for (const msg of messages) {
                const source = msg.source || '';
                if (source && source !== 'user') {
                  if (!agentsUsed.includes(source)) agentsUsed.push(source);
                  let content = msg.content || '';
                  if (Array.isArray(content)) {
                    for (const item of content) {
                      if (typeof item === 'object' && item.type === 'text') {
                        content = item.text || '';
                        break;
                      } else if (typeof item === 'string') {
                        content = item;
                        break;
                      }
                    }
                  }
                  if (content && typeof content === 'string' && !content.startsWith('{')) {
                    resultContent = content;
                  }
                }
              }

              if (resultContent) {
                const data = {
                  workflow_name: `session_${session.id}`,
                  task: taskContent || 'Unknown task',
                  result: resultContent.length > 500 ? resultContent.slice(0, 500) + '...' : resultContent,
                  agents_used: agentsUsed.length > 0 ? agentsUsed : ['unknown'],
                  status: completedRun.status,
                  timestamp: new Date().toISOString(),
                  source: 'autogen-studio-direct'
                };
                console.log('[Browser Mock] getAutogenLatest (direct 8081):', data.workflow_name);
                return { success: true, data };
              }
            }
          }
        }
      }

      // No completed runs found in recent sessions
      return { success: true, data: null };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.warn('[Browser Mock] getAutogenLatest failed:', message);
      return { success: false, error: `AutoGen Studio not reachable: ${message}` };
    }
  },

  // AutoGen runs with messages (for Collab panel)
  // ★ 2026-01-25: Vite 프록시 사용 (/api/autogen → 8081) - CORS 회피
  // Note: projectId filtering not supported in browser mode (Bridge may not be accessible)
  getAutogenRunsDetailed: async (_projectId?: string) => {
    try {
      const sessionsResponse = await fetch('/api/autogen/sessions/?user_id=guestuser@gmail.com', {
        headers: { Accept: 'application/json' }
      });

      if (!sessionsResponse.ok) {
        return { success: false, error: 'AutoGen Studio not connected' };
      }

      const sessionsData = await sessionsResponse.json();
      const sessions = sessionsData.data || [];
      const allRuns: Array<{
        sessionId: number;
        runId: number;
        status: string;
        task: string;
        messages: Array<{
          id: string;
          source: string;
          content: string;
          timestamp: string;
          type: 'text' | 'code' | 'function_call';
        }>;
        timestamp: string;
      }> = [];

      for (const session of sessions.slice(0, 10)) {
        try {
          const runsResponse = await fetch(`/api/autogen/sessions/${session.id}/runs?user_id=guestuser@gmail.com`, {
            headers: { Accept: 'application/json' }
          });

          if (runsResponse.ok) {
            const runsData = await runsResponse.json();
            const runs = runsData.data?.runs || [];

            for (const run of runs.slice(0, 5)) {
              const messages: Array<{
                id: string;
                source: string;
                content: string;
                timestamp: string;
                type: 'text' | 'code' | 'function_call';
              }> = [];

              // Extract task content
              const taskMsgs = run.task?.content || [];
              for (const msg of taskMsgs) {
                if (msg.source === 'user' && msg.content) {
                  messages.push({
                    id: `task_${run.id}_${messages.length}`,
                    source: 'user',
                    content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content),
                    timestamp: run.created_at || new Date().toISOString(),
                    type: 'text' as const,
                  });
                }
              }

              // Extract result messages
              const resultMsgs = run.team_result?.task_result?.messages || [];
              for (const msg of resultMsgs) {
                const source = msg.source || 'unknown';
                let content = msg.content || '';
                let type: 'text' | 'code' | 'function_call' = 'text';

                if (Array.isArray(content)) {
                  for (const item of content) {
                    if (typeof item === 'object' && item.type === 'text') {
                      content = item.text || '';
                      break;
                    } else if (typeof item === 'object' && item.type === 'tool_use') {
                      content = `[Tool: ${item.name}]\n${JSON.stringify(item.input, null, 2)}`;
                      type = 'function_call';
                      break;
                    } else if (typeof item === 'string') {
                      content = item;
                      break;
                    }
                  }
                }

                if (typeof content === 'string' && (content.includes('```') || content.startsWith('{'))) {
                  type = 'code';
                }

                if (content && typeof content === 'string' && source !== 'user') {
                  messages.push({
                    id: `msg_${run.id}_${messages.length}`,
                    source,
                    content: content.length > 1000 ? content.slice(0, 1000) + '...' : content,
                    timestamp: new Date().toISOString(),
                    type,
                  });
                }
              }

              if (messages.length > 0) {
                allRuns.push({
                  sessionId: session.id,
                  runId: run.id,
                  status: run.status,
                  task: messages[0]?.content || 'Unknown task',
                  messages,
                  timestamp: run.created_at || new Date().toISOString(),
                });
              }
            }
          }
        } catch {
          // Skip failed session fetches
        }
      }

      return { success: true, data: allRuns };
    } catch (err) {
      console.debug('[Browser Mock] getAutogenRunsDetailed failed:', err);
      return { success: false, error: 'Failed to fetch runs' };
    }
  },

  // AutoGen session binding (★ Project Binding - browser mode stubs)
  autogenBindSession: async (projectId: string, projectPath: string, sessionId: number, _teamId?: number) => {
    console.log('[Browser Mock] autogenBindSession:', { projectId, projectPath, sessionId });
    try {
      const response = await fetch('http://localhost:8080/bridge/bindings/bind', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, project_path: projectPath, session_id: sessionId, bound_by: 'manual' }),
      });
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: { success: true, message: result.message || 'Session bound' } };
    } catch (err) {
      console.debug('[Browser Mock] autogenBindSession failed:', err);
      return { success: false, error: 'Bridge not available' };
    }
  },

  autogenUnbindSession: async (projectId: string, sessionId: number) => {
    console.log('[Browser Mock] autogenUnbindSession:', { projectId, sessionId });
    try {
      const response = await fetch('http://localhost:8080/bridge/bindings/unbind', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, session_id: sessionId }),
      });
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: { success: true, message: result.message || 'Session unbound' } };
    } catch (err) {
      console.debug('[Browser Mock] autogenUnbindSession failed:', err);
      return { success: false, error: 'Bridge not available' };
    }
  },

  autogenGetUnboundSessions: async (allSessionIds: number[]) => {
    console.log('[Browser Mock] autogenGetUnboundSessions:', { count: allSessionIds.length });
    try {
      const response = await fetch(`http://localhost:8080/bridge/bindings/unbound?session_ids=${allSessionIds.join(',')}`, {
        headers: { Accept: 'application/json' },
      });
      if (!response.ok) {
        return { success: true, data: { unbound_session_ids: allSessionIds, count: allSessionIds.length } };
      }
      const result = await response.json();
      return { success: true, data: { unbound_session_ids: result.unbound_session_ids || [], count: result.count || 0 } };
    } catch (err) {
      console.debug('[Browser Mock] autogenGetUnboundSessions failed:', err);
      // Return all as unbound if Bridge is down
      return { success: true, data: { unbound_session_ids: allSessionIds, count: allSessionIds.length } };
    }
  },

  // AG-ACE-BRIDGE Workflow operations (★ Bridge Module)
  workflowExecute: async (task: string, complexity: 'simple' | 'standard' | 'complex' = 'standard', autoMerge = false, projectPath?: string) => {
    console.log('[Browser Mock] workflowExecute:', { task, complexity, autoMerge, projectPath });
    try {
      const response = await fetch('http://localhost:8080/workflow/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, complexity, auto_merge: autoMerge, ...(projectPath ? { project_path: projectPath } : {}) }),
      });
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      const execIdMatch = result.message?.match(/Execution ID: (exec_\d+_\d+)/);
      return {
        success: true,
        data: {
          success: result.success,
          status: result.status,
          message: result.message,
          exec_id: execIdMatch ? execIdMatch[1] : undefined,
        },
      };
    } catch (err) {
      console.debug('[Browser Mock] workflowExecute failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  workflowGetExecution: async (execId: string) => {
    console.log('[Browser Mock] workflowGetExecution:', execId);
    try {
      const response = await fetch(`http://localhost:8080/workflow/executions/${execId}`);
      if (response.status === 404) {
        return { success: false, error: 'Execution not found' };
      }
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] workflowGetExecution failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  workflowListExecutions: async () => {
    console.log('[Browser Mock] workflowListExecutions');
    try {
      const response = await fetch('http://localhost:8080/workflow/executions');
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] workflowListExecutions failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  workflowListSpecs: async () => {
    console.log('[Browser Mock] workflowListSpecs');
    try {
      const response = await fetch('http://localhost:8080/workflow/specs');
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] workflowListSpecs failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  workflowReview: async (specId: string) => {
    console.log('[Browser Mock] workflowReview:', specId);
    try {
      const response = await fetch(`http://localhost:8080/workflow/review/${specId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] workflowReview failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  workflowMerge: async (specId: string) => {
    console.log('[Browser Mock] workflowMerge:', specId);
    try {
      const response = await fetch(`http://localhost:8080/workflow/merge/${specId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] workflowMerge failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  // ──────────────────────────────────────────────
  // AG-ACE-BRIDGE Pipeline API (★ E2E Project Pipeline)
  // Uses Vite proxy: /api/bridge → http://localhost:8080
  // ──────────────────────────────────────────────

  bridgePipelineInit: async (path: string, name: string, description = '') => {
    console.log('[Browser Mock] bridgePipelineInit:', { path, name });
    try {
      const response = await fetch('/api/bridge/pipeline/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, name, description }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        return { success: false, error: err.detail || `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] bridgePipelineInit failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  bridgePipelinePlan: async (projectId: string, sessionId?: number) => {
    console.log('[Browser Mock] bridgePipelinePlan:', { projectId, sessionId });
    try {
      const response = await fetch('/api/bridge/pipeline/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, session_id: sessionId ?? null }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        return { success: false, error: err.detail || `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] bridgePipelinePlan failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  bridgePipelineStatus: async (projectId: string) => {
    try {
      const response = await fetch(`/api/bridge/pipeline/status/${projectId}`);
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] bridgePipelineStatus failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  bridgePipelineTasks: async (projectId: string) => {
    try {
      const response = await fetch(`/api/bridge/pipeline/tasks/${projectId}`);
      if (!response.ok) {
        return { success: false, error: `HTTP ${response.status}` };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      console.debug('[Browser Mock] bridgePipelineTasks failed:', err);
      return { success: false, error: 'AG-ACE-BRIDGE not connected' };
    }
  },

  // Open external URL in browser
  openExternal: async (url: string): Promise<void> => {
    window.open(url, '_blank');
  }
};

/**
 * Initialize browser mock if not running in Electron
 */
export function initBrowserMock(): void {
  if (!isElectron) {
    console.warn('%c[Browser Mock] Initializing mock electronAPI for browser preview', 'color: #f0ad4e; font-weight: bold;');
    (window as Window & { electronAPI: ElectronAPI }).electronAPI = browserMockAPI;
  }
}

// Auto-initialize
initBrowserMock();
