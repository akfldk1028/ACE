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
        const response = await fetch(`${url}/decisions/${key}`, {
          headers: { Accept: 'application/json' },
        });

        if (response.status === 404) {
          return { success: true, data: null };
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        return { success: true, data: result.data };
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

  console.log('[A2A] A2A handlers registered (including SharedMemory sync)');
}
