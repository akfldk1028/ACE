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

  // AutoGen Studio sync (★ AutoGen → SharedMemory → Auto-Claude UI)
  getAutogenLatest: (projectId?: string) => Promise<IPCResult<{
    workflow_name: string;
    task: string;
    result: string;
    agents_used: string[];
    status: string;
    timestamp: string;
  } | null>>;

  // AutoGen Studio runs with messages (for Collab panel - IPC를 통해 Main Process에서 8081 호출)
  getAutogenRunsDetailed: () => Promise<IPCResult<Array<{
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
  }>>>;

  // AG-ACE-BRIDGE Workflow operations (★ Bridge Module - Auto-Claude trigger from AutoGen)
  workflowExecute: (
    task: string,
    complexity?: 'simple' | 'standard' | 'complex',
    autoMerge?: boolean
  ) => Promise<IPCResult<{
    success: boolean;
    status: string;
    message: string;
    exec_id?: string;
  }>>;

  workflowGetExecution: (execId: string) => Promise<IPCResult<{
    task: string;
    complexity: string;
    status: string;
    started_at: string;
    spec_id: string | null;
    result: unknown | null;
    error?: string;
  }>>;

  workflowListExecutions: () => Promise<IPCResult<{
    executions: Array<{
      task: string;
      complexity: string;
      status: string;
      started_at: string;
      spec_id: string | null;
    }>;
    total: number;
  }>>;

  workflowListSpecs: () => Promise<IPCResult<{
    specs: Array<{
      id: string;
      name: string;
      status?: string;
    }>;
    total: number;
  }>>;

  workflowReview: (specId: string) => Promise<IPCResult<{
    spec_id: string;
    success: boolean;
    output?: string;
    error?: string;
  }>>;

  workflowMerge: (specId: string) => Promise<IPCResult<{
    spec_id: string;
    success: boolean;
    error?: string;
  }>>;
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

    // AutoGen Studio sync
    getAutogenLatest: (projectId?: string): Promise<IPCResult<{
      workflow_name: string;
      task: string;
      result: string;
      agents_used: string[];
      status: string;
      timestamp: string;
    } | null>> =>
      invokeIpc(IPC_CHANNELS.SHARED_MEMORY_GET_AUTOGEN_LATEST, projectId),

    // AutoGen Studio runs with messages (for Collab panel)
    getAutogenRunsDetailed: (): Promise<IPCResult<Array<{
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
    }>>> =>
      invokeIpc(IPC_CHANNELS.AUTOGEN_GET_RUNS_DETAILED),

    // AG-ACE-BRIDGE Workflow operations (★ Bridge Module)
    workflowExecute: (
      task: string,
      complexity: 'simple' | 'standard' | 'complex' = 'standard',
      autoMerge = false
    ): Promise<IPCResult<{
      success: boolean;
      status: string;
      message: string;
      exec_id?: string;
    }>> =>
      invokeIpc(IPC_CHANNELS.WORKFLOW_EXECUTE, task, complexity, autoMerge),

    workflowGetExecution: (execId: string): Promise<IPCResult<{
      task: string;
      complexity: string;
      status: string;
      started_at: string;
      spec_id: string | null;
      result: unknown | null;
      error?: string;
    }>> =>
      invokeIpc(IPC_CHANNELS.WORKFLOW_GET_EXECUTION, execId),

    workflowListExecutions: (): Promise<IPCResult<{
      executions: Array<{
        task: string;
        complexity: string;
        status: string;
        started_at: string;
        spec_id: string | null;
      }>;
      total: number;
    }>> =>
      invokeIpc(IPC_CHANNELS.WORKFLOW_LIST_EXECUTIONS),

    workflowListSpecs: (): Promise<IPCResult<{
      specs: Array<{
        id: string;
        name: string;
        status?: string;
      }>;
      total: number;
    }>> =>
      invokeIpc(IPC_CHANNELS.WORKFLOW_LIST_SPECS),

    workflowReview: (specId: string): Promise<IPCResult<{
      spec_id: string;
      success: boolean;
      output?: string;
      error?: string;
    }>> =>
      invokeIpc(IPC_CHANNELS.WORKFLOW_REVIEW, specId),

    workflowMerge: (specId: string): Promise<IPCResult<{
      spec_id: string;
      success: boolean;
      error?: string;
    }>> =>
      invokeIpc(IPC_CHANNELS.WORKFLOW_MERGE, specId),
  };
}
