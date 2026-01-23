import { IPC_CHANNELS } from '../../../shared/constants';
import type { A2ASyncStatus, A2AAgent, IPCResult } from '../../../shared/types';
import { invokeIpc } from './ipc-utils';

/**
 * A2A (Agent-to-Agent) Protocol API operations
 *
 * Connects to AG-ACE-BRIDGE A2A agents via Google ADK protocol.
 * Agents run on ports 8003-8120.
 */
export interface A2AAPI {
  // Discovery and health operations
  discoverA2AAgents: (projectId: string) => Promise<IPCResult<A2ASyncStatus>>;
  checkA2AAgentHealth: (projectId: string, agentUrl: string) => Promise<IPCResult<{ online: boolean; error?: string }>>;

  // Messaging operations
  sendA2AMessage: (
    projectId: string,
    agentUrl: string,
    message: string
  ) => Promise<IPCResult<{ response: string; raw?: unknown }>>;

  // SharedMemory synchronization (Auto-Claude ↔ AG sync)
  sharedMemoryHealth: (projectId?: string) => Promise<IPCResult<{ online: boolean; url: string }>>;
  sharedMemoryGet: (key: string, projectId?: string) => Promise<IPCResult<unknown>>;
  sharedMemoryStore: (key: string, data: unknown, projectId?: string) => Promise<IPCResult<{ stored: boolean }>>;
  sharedMemoryListKeys: (projectId?: string) => Promise<IPCResult<string[]>>;
  sharedMemoryGetA2AHistory: (
    agentName?: string,
    limit?: number,
    projectId?: string
  ) => Promise<IPCResult<Array<{ agent: string; message: string; result: unknown; timestamp: string }>>>;
}

/**
 * Create A2A API implementation
 */
export function createA2AAPI(): A2AAPI {
  return {
    // A2A agent operations
    discoverA2AAgents: (projectId: string): Promise<IPCResult<A2ASyncStatus>> =>
      invokeIpc(IPC_CHANNELS.A2A_DISCOVER_AGENTS, projectId),

    checkA2AAgentHealth: (projectId: string, agentUrl: string): Promise<IPCResult<{ online: boolean; error?: string }>> =>
      invokeIpc(IPC_CHANNELS.A2A_CHECK_AGENT_HEALTH, projectId, agentUrl),

    sendA2AMessage: (projectId: string, agentUrl: string, message: string): Promise<IPCResult<{ response: string; raw?: unknown }>> =>
      invokeIpc(IPC_CHANNELS.A2A_SEND_MESSAGE, projectId, agentUrl, message),

    // SharedMemory synchronization operations
    sharedMemoryHealth: (projectId?: string): Promise<IPCResult<{ online: boolean; url: string }>> =>
      invokeIpc(IPC_CHANNELS.SHARED_MEMORY_HEALTH, projectId),

    sharedMemoryGet: (key: string, projectId?: string): Promise<IPCResult<unknown>> =>
      invokeIpc(IPC_CHANNELS.SHARED_MEMORY_GET, key, projectId),

    sharedMemoryStore: (key: string, data: unknown, projectId?: string): Promise<IPCResult<{ stored: boolean }>> =>
      invokeIpc(IPC_CHANNELS.SHARED_MEMORY_STORE, key, data, projectId),

    sharedMemoryListKeys: (projectId?: string): Promise<IPCResult<string[]>> =>
      invokeIpc(IPC_CHANNELS.SHARED_MEMORY_LIST_KEYS, projectId),

    sharedMemoryGetA2AHistory: (
      agentName?: string,
      limit = 10,
      projectId?: string
    ): Promise<IPCResult<Array<{ agent: string; message: string; result: unknown; timestamp: string }>>> =>
      invokeIpc(IPC_CHANNELS.SHARED_MEMORY_GET_A2A_HISTORY, agentName, limit, projectId),
  };
}
