/**
 * A2A (Agent-to-Agent) Protocol IPC Handlers
 *
 * Handles communication with AG-ACE-BRIDGE A2A agents via Google ADK protocol.
 * Agents run on ports 8003-8120.
 */

import { ipcMain } from 'electron';
import { existsSync, readFileSync } from 'fs';
import path from 'path';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult, A2ASyncStatus, A2AAgent } from '../../shared/types';
import { projectStore } from '../project-store';
import { parseEnvFile } from './utils';

// Debug logging helper
const DEBUG = process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development';

function debugLog(message: string, data?: unknown): void {
  if (DEBUG) {
    if (data !== undefined) {
      console.debug(`[A2A] ${message}`, data);
    } else {
      console.debug(`[A2A] ${message}`);
    }
  }
}

// Default A2A agent configurations from AG-ACE-BRIDGE
const DEFAULT_A2A_AGENTS: Array<{ name: string; displayName: string; port: number; description: string }> = [
  { name: 'poetry_agent', displayName: 'Poetry Agent', port: 8003, description: 'Poetry and literary analysis' },
  { name: 'philosophy_agent', displayName: 'Philosophy Agent', port: 8004, description: 'Philosophical reasoning' },
  { name: 'history_agent', displayName: 'History Agent', port: 8005, description: 'Historical context analysis' },
  { name: 'calculator_agent', displayName: 'Calculator Agent', port: 8006, description: 'Mathematical calculations' },
  { name: 'gui_test_agent', displayName: 'GUI Test Agent', port: 8120, description: 'GUI automation testing' },
];

// SharedMemory server configuration (AG-CLI sync hub)
const SHARED_MEMORY_DEFAULT_URL = 'http://localhost:8101';

/**
 * Check if an A2A agent is online by fetching its agent card
 */
async function checkAgentOnline(baseUrl: string, timeout = 5000): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(`${baseUrl}/.well-known/agent.json`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Discover available A2A agents
 */
export function registerDiscoverAgents(): void {
  ipcMain.handle(
    IPC_CHANNELS.A2A_DISCOVER_AGENTS,
    async (_event, projectId: string): Promise<IPCResult<A2ASyncStatus>> => {
      debugLog('discoverA2AAgents handler called', { projectId });

      const project = projectStore.getProject(projectId);
      if (!project) {
        return { success: false, error: 'Project not found' };
      }

      if (!project.autoBuildPath) {
        return { success: false, error: 'Project not initialized' };
      }

      // Read A2A configuration from project .env file
      const envPath = path.join(project.path, project.autoBuildPath, '.env');
      let envVars: Record<string, string> = {};
      if (existsSync(envPath)) {
        try {
          const content = readFileSync(envPath, 'utf-8');
          envVars = parseEnvFile(content);
        } catch {
          // Continue with empty vars
        }
      }

      const a2aEnabled = envVars['A2A_ENABLED']?.toLowerCase() === 'true';
      if (!a2aEnabled) {
        return {
          success: true,
          data: {
            connected: false,
            autogenStudioOnline: false,
            agentCount: 0,
            onlineAgentCount: 0,
            agents: [],
            error: 'A2A integration not enabled',
          },
        };
      }

      const baseHost = envVars['A2A_AUTOGEN_STUDIO_URL'] || 'http://127.0.0.1';

      try {
        // Check each default agent
        const agentPromises = DEFAULT_A2A_AGENTS.map(async (agentDef) => {
          const url = `${baseHost.replace(/:\d+$/, '')}:${agentDef.port}`;
          const isOnline = await checkAgentOnline(url);

          const agent: A2AAgent = {
            name: agentDef.name,
            displayName: agentDef.displayName,
            url,
            description: agentDef.description,
            skills: [],
            isOnline,
            lastChecked: new Date().toISOString(),
            timeout: 60000,
          };

          return agent;
        });

        const agents = await Promise.all(agentPromises);
        const onlineAgentCount = agents.filter((a) => a.isOnline).length;

        debugLog(`Discovered ${agents.length} agents, ${onlineAgentCount} online`);

        return {
          success: true,
          data: {
            connected: onlineAgentCount > 0,
            autogenStudioOnline: onlineAgentCount > 0,
            agentCount: agents.length,
            onlineAgentCount,
            agents,
            lastSyncedAt: new Date().toISOString(),
          },
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to discover A2A agents';
        debugLog('Discovery failed:', errorMessage);
        return {
          success: true,
          data: {
            connected: false,
            autogenStudioOnline: false,
            agentCount: 0,
            onlineAgentCount: 0,
            agents: [],
            error: errorMessage,
          },
        };
      }
    }
  );
}

/**
 * Check individual A2A agent health
 */
export function registerCheckAgentHealth(): void {
  ipcMain.handle(
    IPC_CHANNELS.A2A_CHECK_AGENT_HEALTH,
    async (
      _event,
      projectId: string,
      agentUrl: string
    ): Promise<IPCResult<{ online: boolean; error?: string }>> => {
      debugLog('checkA2AAgentHealth handler called', { projectId, agentUrl });

      try {
        const isOnline = await checkAgentOnline(agentUrl);
        return {
          success: true,
          data: { online: isOnline },
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Health check failed';
        return {
          success: true,
          data: { online: false, error: errorMessage },
        };
      }
    }
  );
}

/**
 * Extract agent name from URL (port-based mapping)
 */
function extractAgentName(url: string): string {
  const portToAgent: Record<string, string> = {
    '8003': 'poetry_agent',
    '8004': 'philosophy_agent',
    '8005': 'history_agent',
    '8006': 'calculator_agent',
    '8120': 'gui_test_agent',
  };
  for (const [port, name] of Object.entries(portToAgent)) {
    if (url.includes(`:${port}`)) return name;
  }
  return 'unknown_agent';
}

/**
 * Sync A2A result to SharedMemory (★ Auto-Claude ↔ AG 동기화)
 */
async function syncToSharedMemory(
  agentUrl: string,
  message: string,
  responseText: string,
  success: boolean,
  projectId?: string
): Promise<void> {
  const sharedMemoryUrl = getSharedMemoryUrl(projectId);
  const agentName = extractAgentName(agentUrl);
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const key = `a2a_${agentName}_${requestId}`;

  const data = {
    agent_name: agentName,
    message,
    result: { success, text: responseText },
    request_id: requestId,
    timestamp: new Date().toISOString(),
    source: 'auto-claude',
  };

  try {
    // Store result
    await fetch(`${sharedMemoryUrl}/decisions/${key}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, data, source: 'auto-claude' }),
    });

    // Update latest
    const latestKey = `a2a_${agentName}_latest`;
    await fetch(`${sharedMemoryUrl}/decisions/${latestKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: latestKey, data, source: 'auto-claude' }),
    });

    // Publish event
    await fetch(`${sharedMemoryUrl}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'a2a_call_completed',
        data: { agent_name: agentName, request_id: requestId, success },
        source: 'auto-claude',
      }),
    });

    debugLog(`[SharedMemory] Synced A2A result: ${agentName}`);
  } catch (err) {
    // Don't fail the A2A call if SharedMemory sync fails
    debugLog(`[SharedMemory] Sync failed (non-blocking):`, err);
  }
}

/**
 * Send message to A2A agent
 */
export function registerSendMessage(): void {
  ipcMain.handle(
    IPC_CHANNELS.A2A_SEND_MESSAGE,
    async (
      _event,
      projectId: string,
      agentUrl: string,
      message: string
    ): Promise<IPCResult<{ response: string; raw?: unknown }>> => {
      debugLog('sendA2AMessage handler called', { projectId, agentUrl, messageLength: message.length });

      try {
        const payload = {
          jsonrpc: '2.0',
          method: 'message/send',
          params: {
            message: {
              messageId: `msg-${Date.now()}`,
              role: 'user',
              parts: [{ type: 'text', text: message }],
            },
          },
          id: `req-${Date.now()}`,
        };

        const response = await fetch(agentUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // Parse A2A response
        let responseText = '';
        if (result.result) {
          // Handle artifacts format (Google ADK style)
          if (result.result.artifacts) {
            for (const artifact of result.result.artifacts) {
              for (const part of artifact.parts || []) {
                if (part.text) {
                  responseText = part.text;
                  break;
                }
              }
              if (responseText) break;
            }
          }
          // Handle message parts format
          else if (result.result.message?.parts) {
            const textParts = result.result.message.parts
              .filter((p: { type?: string }) => p.type === 'text')
              .map((p: { text?: string }) => p.text || '');
            responseText = textParts.join('\n');
          }
        }

        // ★ Auto-Claude ↔ AG 동기화: SharedMemory에 결과 저장
        await syncToSharedMemory(agentUrl, message, responseText, true, projectId);

        return {
          success: true,
          data: {
            response: responseText || JSON.stringify(result),
            raw: result,
          },
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
        debugLog('Send message failed:', errorMessage);

        // ★ 실패해도 SharedMemory에 기록 (디버깅용)
        await syncToSharedMemory(agentUrl, message, errorMessage, false, projectId);

        return {
          success: false,
          error: errorMessage,
        };
      }
    }
  );
}

// ============================================================================
// SharedMemory IPC Handlers (Auto-Claude ↔ AG Synchronization)
// ============================================================================

/**
 * Get SharedMemory URL from project config or use default
 */
function getSharedMemoryUrl(projectId?: string): string {
  if (projectId) {
    const project = projectStore.getProject(projectId);
    if (project?.autoBuildPath) {
      const envPath = path.join(project.path, project.autoBuildPath, '.env');
      if (existsSync(envPath)) {
        try {
          const content = readFileSync(envPath, 'utf-8');
          const envVars = parseEnvFile(content);
          if (envVars['SHARED_MEMORY_URL']) {
            return envVars['SHARED_MEMORY_URL'];
          }
        } catch {
          // Use default
        }
      }
    }
  }
  return SHARED_MEMORY_DEFAULT_URL;
}

/**
 * Check SharedMemory server health
 */
export function registerSharedMemoryHealth(): void {
  ipcMain.handle(
    IPC_CHANNELS.SHARED_MEMORY_HEALTH,
    async (_event, projectId?: string): Promise<IPCResult<{ online: boolean; url: string }>> => {
      const url = getSharedMemoryUrl(projectId);
      debugLog('SharedMemory health check', { url });

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${url}/health`, {
          signal: controller.signal,
          headers: { Accept: 'application/json' },
        });

        clearTimeout(timeoutId);
        return {
          success: true,
          data: { online: response.ok, url },
        };
      } catch {
        return {
          success: true,
          data: { online: false, url },
        };
      }
    }
  );
}

/**
 * Get state from SharedMemory
 */
export function registerSharedMemoryGet(): void {
  ipcMain.handle(
    IPC_CHANNELS.SHARED_MEMORY_GET,
    async (_event, key: string, projectId?: string): Promise<IPCResult<unknown>> => {
      const url = getSharedMemoryUrl(projectId);
      debugLog('SharedMemory get', { key, url });

      try {
        // AG-CLI SharedMemory API: GET /decision/{key}
        const response = await fetch(`${url}/decision/${key}`, {
          headers: { Accept: 'application/json' },
        });

        if (response.status === 404) {
          return { success: true, data: null };
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // AG-CLI returns the value directly, not wrapped in {data: ...}
        const result = await response.json();
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to get from SharedMemory';
        debugLog('SharedMemory get failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Store state to SharedMemory
 */
export function registerSharedMemoryStore(): void {
  ipcMain.handle(
    IPC_CHANNELS.SHARED_MEMORY_STORE,
    async (
      _event,
      key: string,
      data: unknown,
      projectId?: string
    ): Promise<IPCResult<{ stored: boolean }>> => {
      const url = getSharedMemoryUrl(projectId);
      debugLog('SharedMemory store', { key, url });

      try {
        const payload = {
          key,
          data,
          source: 'auto-claude',
        };

        const response = await fetch(`${url}/decisions/${key}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return { success: true, data: { stored: true } };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to store to SharedMemory';
        debugLog('SharedMemory store failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * List all keys in SharedMemory
 */
export function registerSharedMemoryListKeys(): void {
  ipcMain.handle(
    IPC_CHANNELS.SHARED_MEMORY_LIST_KEYS,
    async (_event, projectId?: string): Promise<IPCResult<string[]>> => {
      const url = getSharedMemoryUrl(projectId);
      debugLog('SharedMemory listKeys', { url });

      try {
        const response = await fetch(`${url}/decisions`, {
          headers: { Accept: 'application/json' },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        return { success: true, data: result.keys || [] };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to list keys from SharedMemory';
        debugLog('SharedMemory listKeys failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Get A2A call history from SharedMemory
 */
export function registerSharedMemoryGetA2AHistory(): void {
  ipcMain.handle(
    IPC_CHANNELS.SHARED_MEMORY_GET_A2A_HISTORY,
    async (
      _event,
      agentName?: string,
      limit = 10,
      projectId?: string
    ): Promise<IPCResult<Array<{ agent: string; message: string; result: unknown; timestamp: string }>>> => {
      const url = getSharedMemoryUrl(projectId);
      debugLog('SharedMemory getA2AHistory', { agentName, limit, url });

      try {
        // First get all keys
        const keysResponse = await fetch(`${url}/decisions`, {
          headers: { Accept: 'application/json' },
        });

        if (!keysResponse.ok) {
          throw new Error(`HTTP ${keysResponse.status}: ${keysResponse.statusText}`);
        }

        const keysResult = await keysResponse.json();
        const allKeys: string[] = keysResult.keys || [];

        // Filter A2A keys (format: a2a_{agent}_{id})
        let a2aKeys = allKeys.filter((k: string) => k.startsWith('a2a_') && !k.endsWith('_latest'));
        if (agentName) {
          a2aKeys = a2aKeys.filter((k: string) => k.includes(agentName));
        }

        // Get recent ones (last N)
        a2aKeys = a2aKeys.slice(-limit);

        // Fetch each key's data
        const history: Array<{ agent: string; message: string; result: unknown; timestamp: string }> = [];
        for (const key of a2aKeys) {
          try {
            const dataResponse = await fetch(`${url}/decisions/${key}`, {
              headers: { Accept: 'application/json' },
            });
            if (dataResponse.ok) {
              const dataResult = await dataResponse.json();
              if (dataResult.data) {
                history.push({
                  agent: dataResult.data.agent_name || 'unknown',
                  message: dataResult.data.message || '',
                  result: dataResult.data.result,
                  timestamp: dataResult.data.timestamp || '',
                });
              }
            }
          } catch {
            // Skip failed fetches
          }
        }

        return { success: true, data: history };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to get A2A history';
        debugLog('SharedMemory getA2AHistory failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Get AutoGen Studio latest result
 * (★ AutoGen Studio(8081) 직접 조회 우선 → SharedMemory(8101) 폴백)
 */
export function registerGetAutogenLatest(): void {
  ipcMain.handle(
    IPC_CHANNELS.SHARED_MEMORY_GET_AUTOGEN_LATEST,
    async (_event, projectId?: string): Promise<IPCResult<{
      workflow_name: string;
      task: string;
      result: string;
      agents_used: string[];
      status: string;
      timestamp: string;
      source?: string;
    } | null>> => {
      debugLog('getAutogenLatest called', { projectId });

      // ★ 1차: AutoGen Studio(8081) 직접 조회
      try {
        const autogenUrl = 'http://localhost:8081';
        const sessionsResponse = await fetch(`${autogenUrl}/api/sessions/?user_id=guestuser@gmail.com`, {
          headers: { Accept: 'application/json' },
        });

        if (sessionsResponse.ok) {
          const sessionsData = await sessionsResponse.json();
          const sessions = sessionsData.data || [];

          // 최신 5개 세션에서 완료된 run 찾기
          for (const session of sessions.slice(0, 5)) {
            try {
              const runsResponse = await fetch(`${autogenUrl}/api/sessions/${session.id}/runs/?user_id=guestuser@gmail.com`, {
                headers: { Accept: 'application/json' },
              });

              if (runsResponse.ok) {
                const runsData = await runsResponse.json();
                const runs = runsData.data?.runs || [];

                // 완료된 run 찾기
                const completedRun = runs.find((r: { status: string }) => r.status === 'complete');
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

                  // 결과 메시지 추출 (messages[].config.content 또는 team_result.task_result.messages[].content)
                  const detailedMessages = completedRun.messages || [];
                  const taskResultMessages = completedRun.team_result?.task_result?.messages || [];

                  // 1차: detailedMessages (config.content에 실제 데이터 있음)
                  for (const msg of detailedMessages) {
                    const config = msg.config || msg;
                    const source = config.source || '';
                    if (source && source !== 'user' && source !== 'llm_call_event') {
                      if (!agentsUsed.includes(source)) agentsUsed.push(source);
                      let content = config.content || '';
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
                      if (content && typeof content === 'string' && !content.startsWith('{') && config.type === 'TextMessage') {
                        resultContent = content;
                      }
                    }
                  }

                  // 2차 폴백: team_result.task_result.messages (기존 호환)
                  if (!resultContent) {
                    for (const msg of taskResultMessages) {
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
                  }

                  if (resultContent) {
                    const data = {
                      workflow_name: `session_${session.id}`,
                      task: taskContent || 'Unknown task',
                      result: resultContent.length > 500 ? resultContent.slice(0, 500) + '...' : resultContent,
                      agents_used: agentsUsed.length > 0 ? agentsUsed : ['unknown'],
                      status: completedRun.status,
                      timestamp: completedRun.created_at || new Date().toISOString(),
                      source: 'autogen-studio-direct',
                    };
                    debugLog('AutoGen direct result:', data.workflow_name);
                    return { success: true, data };
                  }
                }
              }
            } catch {
              // 개별 세션 조회 실패는 무시
            }
          }
        }
      } catch (err) {
        debugLog('AutoGen Studio direct fetch failed:', err);
      }

      // ★ 2차 폴백: SharedMemory(8101) 조회
      const url = getSharedMemoryUrl(projectId);
      debugLog('Fallback to SharedMemory', { url });

      try {
        const response = await fetch(`${url}/decision/autogen_latest`, {
          headers: { Accept: 'application/json' },
        });

        if (response.status === 404) {
          return { success: true, data: null };
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        if (result) {
          result.source = 'shared-memory';
        }
        debugLog('SharedMemory fallback result:', result?.workflow_name);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to get AutoGen latest';
        debugLog('SharedMemory getAutogenLatest failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Get AutoGen Studio runs with full messages (for Collab panel)
 * ★ 중앙화된 8081 호출 - Renderer에서 직접 호출 금지
 */
export function registerGetAutogenRunsDetailed(): void {
  ipcMain.handle(
    IPC_CHANNELS.AUTOGEN_GET_RUNS_DETAILED,
    async (): Promise<IPCResult<Array<{
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
    }>>> => {
      debugLog('getAutogenRunsDetailed called');

      const autogenUrl = 'http://localhost:8081';
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

      try {
        // Fetch sessions
        const sessionsRes = await fetch(`${autogenUrl}/api/sessions/?user_id=guestuser@gmail.com`, {
          headers: { Accept: 'application/json' },
        });

        if (!sessionsRes.ok) {
          return { success: false, error: 'AutoGen Studio not connected' };
        }

        const sessionsData = await sessionsRes.json();
        const sessions = sessionsData.data || [];

        // Fetch runs for each recent session (max 10 for large projects)
        for (const session of sessions.slice(0, 10)) {
          try {
            const runsRes = await fetch(`${autogenUrl}/api/sessions/${session.id}/runs/?user_id=guestuser@gmail.com`, {
              headers: { Accept: 'application/json' },
            });

            if (runsRes.ok) {
              const runsData = await runsRes.json();
              const sessionRuns = runsData.data?.runs || [];

              for (const run of sessionRuns.slice(0, 5)) {
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
                      type: 'text',
                    });
                  }
                }

                // Extract result messages (use run.messages[].config for actual content)
                const detailedMsgs = run.messages || [];
                const fallbackMsgs = run.team_result?.task_result?.messages || [];
                const resultMsgs = detailedMsgs.length > 0
                  ? detailedMsgs.map((m: { config?: Record<string, unknown> }) => m.config || m)
                  : fallbackMsgs;
                for (const msg of resultMsgs) {
                  const source = (msg.source as string) || 'unknown';
                  let content = (msg.content as string | unknown[]) || '';
                  let type: 'text' | 'code' | 'function_call' = 'text';

                  // Handle array content
                  if (Array.isArray(content)) {
                    for (const item of content) {
                      if (item && typeof item === 'object' && (item as Record<string, unknown>).type === 'text') {
                        content = ((item as Record<string, unknown>).text as string) || '';
                        break;
                      } else if (item && typeof item === 'object' && (item as Record<string, unknown>).type === 'tool_use') {
                        const rec = item as Record<string, unknown>;
                        content = `[Tool: ${rec.name}]\n${JSON.stringify(rec.input, null, 2)}`;
                        type = 'function_call';
                        break;
                      } else if (typeof item === 'string') {
                        content = item;
                        break;
                      }
                    }
                  }

                  // Detect code blocks
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

        debugLog(`getAutogenRunsDetailed: ${allRuns.length} runs found`);
        return { success: true, data: allRuns };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch AutoGen runs';
        debugLog('getAutogenRunsDetailed failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

// ============================================================================
// AG-ACE-BRIDGE Workflow IPC Handlers (★ Bridge Module - 2026-01-24)
// ============================================================================

const AG_ACE_BRIDGE_URL = 'http://localhost:8080';

/**
 * Execute workflow via AG-ACE-BRIDGE
 */
export function registerWorkflowExecute(): void {
  ipcMain.handle(
    IPC_CHANNELS.WORKFLOW_EXECUTE,
    async (
      _event,
      task: string,
      complexity: 'simple' | 'standard' | 'complex' = 'standard',
      autoMerge = false
    ): Promise<IPCResult<{
      success: boolean;
      status: string;
      message: string;
      exec_id?: string;
    }>> => {
      debugLog('workflowExecute called', { task, complexity, autoMerge });

      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/workflow/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task,
            complexity,
            auto_merge: autoMerge,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        debugLog('Workflow execute result:', result);

        // Extract exec_id from message if available
        const execIdMatch = result.message?.match(/Execution ID: (exec_\d+_\d+)/);
        const execId = execIdMatch ? execIdMatch[1] : undefined;

        return {
          success: true,
          data: {
            success: result.success,
            status: result.status,
            message: result.message,
            exec_id: execId,
          },
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to execute workflow';
        debugLog('Workflow execute failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Get workflow execution status
 */
export function registerWorkflowGetExecution(): void {
  ipcMain.handle(
    IPC_CHANNELS.WORKFLOW_GET_EXECUTION,
    async (
      _event,
      execId: string
    ): Promise<IPCResult<{
      task: string;
      complexity: string;
      status: string;
      started_at: string;
      spec_id: string | null;
      result: unknown | null;
      error?: string;
    }>> => {
      debugLog('workflowGetExecution called', { execId });

      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/workflow/executions/${execId}`, {
          headers: { Accept: 'application/json' },
        });

        if (response.status === 404) {
          return { success: false, error: 'Execution not found' };
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        debugLog('Workflow execution status:', result);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to get execution status';
        debugLog('Workflow getExecution failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * List all workflow executions
 */
export function registerWorkflowListExecutions(): void {
  ipcMain.handle(
    IPC_CHANNELS.WORKFLOW_LIST_EXECUTIONS,
    async (): Promise<IPCResult<{
      executions: Array<{
        task: string;
        complexity: string;
        status: string;
        started_at: string;
        spec_id: string | null;
      }>;
      total: number;
    }>> => {
      debugLog('workflowListExecutions called');

      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/workflow/executions`, {
          headers: { Accept: 'application/json' },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        debugLog('Workflow executions list:', result.total);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to list executions';
        debugLog('Workflow listExecutions failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * List all specs
 */
export function registerWorkflowListSpecs(): void {
  ipcMain.handle(
    IPC_CHANNELS.WORKFLOW_LIST_SPECS,
    async (): Promise<IPCResult<{
      specs: Array<{
        id: string;
        name: string;
        status?: string;
      }>;
      total: number;
    }>> => {
      debugLog('workflowListSpecs called');

      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/workflow/specs`, {
          headers: { Accept: 'application/json' },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        debugLog('Workflow specs list:', result.total);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to list specs';
        debugLog('Workflow listSpecs failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Review a spec
 */
export function registerWorkflowReview(): void {
  ipcMain.handle(
    IPC_CHANNELS.WORKFLOW_REVIEW,
    async (
      _event,
      specId: string
    ): Promise<IPCResult<{
      spec_id: string;
      success: boolean;
      output?: string;
      error?: string;
    }>> => {
      debugLog('workflowReview called', { specId });

      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/workflow/review/${specId}`, {
          method: 'POST',
          headers: { Accept: 'application/json' },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        debugLog('Workflow review result:', result);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to review spec';
        debugLog('Workflow review failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

/**
 * Merge a completed spec
 */
export function registerWorkflowMerge(): void {
  ipcMain.handle(
    IPC_CHANNELS.WORKFLOW_MERGE,
    async (
      _event,
      specId: string
    ): Promise<IPCResult<{
      spec_id: string;
      success: boolean;
      error?: string;
    }>> => {
      debugLog('workflowMerge called', { specId });

      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/workflow/merge/${specId}`, {
          method: 'POST',
          headers: { Accept: 'application/json' },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        debugLog('Workflow merge result:', result);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to merge spec';
        debugLog('Workflow merge failed:', errorMessage);
        return { success: false, error: errorMessage };
      }
    }
  );
}

// ──────────────────────────────────────────────
// AG-ACE-BRIDGE Pipeline handlers (★ E2E Project Pipeline)
// ──────────────────────────────────────────────

export function registerPipelineInit(): void {
  ipcMain.handle(
    IPC_CHANNELS.PIPELINE_INIT,
    async (_event, path: string, name: string, description = '') => {
      debugLog('pipelineInit called', { path, name });
      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/pipeline/init`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path, name, description }),
        });
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
          throw new Error(err.detail || `HTTP ${response.status}`);
        }
        const result = await response.json();
        return { success: true, data: result };
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Pipeline init failed';
        debugLog('pipelineInit failed:', msg);
        return { success: false, error: msg };
      }
    }
  );
}

export function registerPipelinePlan(): void {
  ipcMain.handle(
    IPC_CHANNELS.PIPELINE_PLAN,
    async (_event, projectId: string, sessionId?: number) => {
      debugLog('pipelinePlan called', { projectId, sessionId });
      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/pipeline/plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_id: projectId, session_id: sessionId ?? null }),
        });
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
          throw new Error(err.detail || `HTTP ${response.status}`);
        }
        const result = await response.json();
        return { success: true, data: result };
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Pipeline plan failed';
        debugLog('pipelinePlan failed:', msg);
        return { success: false, error: msg };
      }
    }
  );
}

export function registerPipelineStatus(): void {
  ipcMain.handle(
    IPC_CHANNELS.PIPELINE_STATUS,
    async (_event, projectId: string) => {
      debugLog('pipelineStatus called', { projectId });
      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/pipeline/status/${projectId}`);
        if (!response.ok) {
          return { success: false, error: `HTTP ${response.status}` };
        }
        const result = await response.json();
        return { success: true, data: result };
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Pipeline status failed';
        return { success: false, error: msg };
      }
    }
  );
}

export function registerPipelineTasks(): void {
  ipcMain.handle(
    IPC_CHANNELS.PIPELINE_TASKS,
    async (_event, projectId: string) => {
      try {
        const response = await fetch(`${AG_ACE_BRIDGE_URL}/pipeline/tasks/${projectId}`);
        if (!response.ok) {
          return { success: false, error: `HTTP ${response.status}` };
        }
        const result = await response.json();
        return { success: true, data: result };
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Pipeline tasks failed';
        return { success: false, error: msg };
      }
    }
  );
}

/**
 * Register all A2A handlers
 */
export function registerA2AHandlers(): void {
  console.log('[A2A] Registering A2A handlers');

  // A2A agent handlers
  registerDiscoverAgents();
  registerCheckAgentHealth();
  registerSendMessage();

  // SharedMemory sync handlers
  registerSharedMemoryHealth();
  registerSharedMemoryGet();
  registerSharedMemoryStore();
  registerSharedMemoryListKeys();
  registerSharedMemoryGetA2AHistory();

  // AutoGen Studio sync handlers
  registerGetAutogenLatest();
  registerGetAutogenRunsDetailed();

  // AG-ACE-BRIDGE Workflow handlers (★ Bridge Module)
  registerWorkflowExecute();
  registerWorkflowGetExecution();
  registerWorkflowListExecutions();
  registerWorkflowListSpecs();
  registerWorkflowReview();
  registerWorkflowMerge();

  // AG-ACE-BRIDGE Pipeline handlers (★ E2E Project Pipeline)
  registerPipelineInit();
  registerPipelinePlan();
  registerPipelineStatus();
  registerPipelineTasks();

  console.log('[A2A] A2A handlers registered (including SharedMemory, AutoGen sync, Workflow & Pipeline)');
}
