/**
 * AutoGen Collaboration Panel
 *
 * Real-time streaming view of AutoGen Studio agent conversations and outputs.
 * Shows what agents are doing in AutoGen Studio for collaboration visibility.
 *
 * ★ 중요: 직접 fetch(8081) 호출 금지!
 * IPC를 통해 Main Process(a2a-handlers.ts)에서 8081 호출
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Bot, User, Code, RefreshCw, X, Minimize2, Terminal, Play, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../lib/utils';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface AutogenMessage {
  id: string;
  source: string; // 'user' | agent name
  content: string;
  timestamp: string;
  type: 'text' | 'code' | 'function_call';
}

interface AutogenRun {
  sessionId: number;
  runId: number;
  status: string;
  task: string;
  messages: AutogenMessage[];
  timestamp: string;
}

interface AutogenCollabPanelProps {
  isOpen: boolean;
  onClose: () => void;
  fullWidth?: boolean; // When true, renders as main content instead of sidebar
}

export function AutogenCollabPanel({ isOpen, onClose, fullWidth = false }: AutogenCollabPanelProps) {
  const [runs, setRuns] = useState<AutogenRun[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Workflow execution state (★ Bridge Module)
  const [showWorkflowForm, setShowWorkflowForm] = useState(true);
  const [workflowTask, setWorkflowTask] = useState('');
  const [workflowComplexity, setWorkflowComplexity] = useState<'simple' | 'standard' | 'complex'>('standard');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<{
    success: boolean;
    message: string;
    execId?: string;
  } | null>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  // Execute workflow via AG-ACE-BRIDGE (★ Bridge Module)
  const executeWorkflow = useCallback(async () => {
    if (!workflowTask.trim()) return;

    setIsExecuting(true);
    setExecutionResult(null);

    try {
      const response = await window.electronAPI.workflowExecute(
        workflowTask.trim(),
        workflowComplexity,
        false // auto_merge
      );

      if (response.success && response.data) {
        setExecutionResult({
          success: response.data.success,
          message: response.data.message,
          execId: response.data.exec_id,
        });
        if (response.data.success) {
          setWorkflowTask(''); // Clear on success
        }
      } else {
        setExecutionResult({
          success: false,
          message: response.error || 'Failed to execute workflow',
        });
      }
    } catch (error) {
      setExecutionResult({
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsExecuting(false);
    }
  }, [workflowTask, workflowComplexity]);

  // Fetch AutoGen Studio runs via IPC (not direct fetch!)
  const fetchRuns = useCallback(async () => {
    try {
      // ★ IPC를 통해 Main Process에서 8081 호출
      const response = await window.electronAPI.getAutogenRunsDetailed();

      if (response.success && response.data) {
        setIsConnected(true);
        setRuns(response.data);
        setTimeout(scrollToBottom, 100);
      } else {
        setIsConnected(false);
      }
    } catch (error) {
      console.debug('[AutogenCollab] Fetch error:', error);
      setIsConnected(false);
    }
  }, [scrollToBottom]);

  // Start/stop polling
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setIsLoading(true);
      fetchRuns().finally(() => setIsLoading(false));

      // Poll every 2 seconds for real-time updates
      pollIntervalRef.current = setInterval(fetchRuns, 2000);

      return () => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      };
    }
  }, [isOpen, isMinimized, fetchRuns]);

  if (!isOpen) return null;

  // Minimized state (only for sidebar mode)
  if (isMinimized && !fullWidth) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          variant="default"
          size="sm"
          onClick={() => setIsMinimized(false)}
          className="gap-2 shadow-lg"
        >
          <Bot className="h-4 w-4" />
          AutoGen Collab
          {isConnected && <span className="h-2 w-2 rounded-full bg-green-500" />}
        </Button>
      </div>
    );
  }

  return (
    <div className={cn(
      "flex h-full flex-col bg-card/50 backdrop-blur-sm",
      fullWidth ? "w-full" : "w-80 border-l border-border"
    )}>
      {/* Header - simpler when fullWidth */}
      {!fullWidth && (
        <div className="flex h-10 items-center justify-between border-b border-border px-3">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">AutoGen Collab</span>
            {isConnected ? (
              <span className="h-2 w-2 rounded-full bg-green-500" title="Connected" />
            ) : (
              <span className="h-2 w-2 rounded-full bg-red-500" title="Disconnected" />
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={fetchRuns}
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setIsMinimized(true)}
            >
              <Minimize2 className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={onClose}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}

      {/* Content */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className={cn("space-y-4", fullWidth ? "p-6" : "p-3")}>
          {/* Connection status for fullWidth mode */}
          {fullWidth && (
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Terminal className="h-5 w-5 text-primary" />
                <span className="font-medium">AutoGen Studio Live</span>
                {isConnected ? (
                  <span className="flex items-center gap-1 text-xs text-green-500">
                    <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    Connected (8081)
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-red-500">
                    <span className="h-2 w-2 rounded-full bg-red-500" />
                    Disconnected
                  </span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchRuns}
                disabled={isLoading}
                className="gap-1.5"
              >
                <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
                Refresh
              </Button>
            </div>
          )}

          {/* Workflow Execution Form (★ Bridge Module) */}
          {fullWidth && (
            <div className="mb-6 rounded-lg border border-border bg-card/50 overflow-hidden">
              <button
                onClick={() => setShowWorkflowForm(!showWorkflowForm)}
                className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Play className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">Create Spec from AutoGen</span>
                </div>
                {showWorkflowForm ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </button>

              {showWorkflowForm && (
                <div className="p-4 pt-0 space-y-3 border-t border-border">
                  <div className="text-xs text-muted-foreground mb-2">
                    Design in AutoGen Studio, then execute via Auto-Claude pipeline
                  </div>

                  {/* Task input */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium">Task Description</label>
                    <Input
                      placeholder="e.g., Create a calculator app with basic operations"
                      value={workflowTask}
                      onChange={(e) => setWorkflowTask(e.target.value)}
                      disabled={isExecuting}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          executeWorkflow();
                        }
                      }}
                    />
                  </div>

                  {/* Complexity selector */}
                  <div className="flex items-center gap-3">
                    <div className="space-y-1.5 flex-1">
                      <label className="text-xs font-medium">Complexity</label>
                      <Select
                        value={workflowComplexity}
                        onValueChange={(v) => setWorkflowComplexity(v as 'simple' | 'standard' | 'complex')}
                        disabled={isExecuting}
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="simple">Simple (3 phases)</SelectItem>
                          <SelectItem value="standard">Standard (6-7 phases)</SelectItem>
                          <SelectItem value="complex">Complex (8 phases)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Execute button */}
                    <Button
                      onClick={executeWorkflow}
                      disabled={isExecuting || !workflowTask.trim()}
                      className="mt-5 gap-2"
                    >
                      {isExecuting ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Executing...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          Execute
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Execution result */}
                  {executionResult && (
                    <div className={cn(
                      "text-xs p-2 rounded border",
                      executionResult.success
                        ? "bg-green-500/10 border-green-500/30 text-green-600"
                        : "bg-red-500/10 border-red-500/30 text-red-600"
                    )}>
                      {executionResult.message}
                      {executionResult.execId && (
                        <div className="mt-1 font-mono text-[10px] opacity-70">
                          Execution ID: {executionResult.execId}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {!isConnected && (
            <div className={cn(
              "text-center text-muted-foreground",
              fullWidth ? "py-16" : "py-8"
            )}>
              <Bot className={cn("mx-auto mb-4", fullWidth ? "h-12 w-12" : "h-8 w-8")} />
              <p className={fullWidth ? "text-lg" : "text-sm"}>AutoGen Studio not connected</p>
              <p className="text-xs mt-1">Start AutoGen Studio at http://localhost:8081</p>
              {fullWidth && (
                <p className="text-xs mt-4 text-muted-foreground/70">
                  Run tasks in AutoGen Studio to see agent conversations here
                </p>
              )}
            </div>
          )}

          {isConnected && runs.length === 0 && (
            <div className={cn(
              "text-center text-muted-foreground",
              fullWidth ? "py-16" : "py-8"
            )}>
              <Terminal className={cn("mx-auto mb-4", fullWidth ? "h-12 w-12" : "h-8 w-8")} />
              <p className={fullWidth ? "text-lg" : "text-sm"}>No recent runs</p>
              <p className="text-xs mt-1">Run a task in AutoGen Studio to see it here</p>
            </div>
          )}

          {/* Runs list */}
          <div className={cn(
            fullWidth ? "grid grid-cols-1 lg:grid-cols-2 gap-4" : "space-y-4"
          )}>
            {runs.map((run) => (
              <div
                key={`${run.sessionId}_${run.runId}`}
                className={cn(
                  "space-y-2 rounded-lg border border-border p-3",
                  fullWidth && "bg-card/30"
                )}
              >
                {/* Run header */}
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-mono">Session {run.sessionId} / Run {run.runId}</span>
                  <span className={cn(
                    "px-1.5 py-0.5 rounded text-[10px] font-medium",
                    run.status === 'complete' && "bg-green-500/20 text-green-500",
                    run.status === 'running' && "bg-blue-500/20 text-blue-500 animate-pulse",
                    run.status === 'error' && "bg-red-500/20 text-red-500",
                    run.status === 'pending' && "bg-yellow-500/20 text-yellow-500"
                  )}>
                    {run.status}
                  </span>
                </div>

                {/* Messages - terminal style */}
                <div className="space-y-2 font-mono text-xs">
                  {run.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={cn(
                        "rounded p-2",
                        msg.source === 'user'
                          ? "bg-primary/10 border-l-2 border-primary"
                          : "bg-muted/50 border-l-2 border-muted-foreground/30"
                      )}
                    >
                      {/* Message header */}
                      <div className="flex items-center gap-1.5 mb-1 text-[10px] text-muted-foreground">
                        {msg.source === 'user' ? (
                          <>
                            <User className="h-3 w-3 text-primary" />
                            <span className="text-primary font-semibold">user</span>
                          </>
                        ) : (
                          <>
                            <Bot className="h-3 w-3" />
                            <span className="font-semibold">{msg.source}</span>
                          </>
                        )}
                        {msg.type === 'code' && (
                          <Code className="h-3 w-3 ml-auto" />
                        )}
                      </div>

                      {/* Message content */}
                      <div className={cn(
                        "text-[11px] leading-relaxed break-words whitespace-pre-wrap",
                        msg.type === 'code' && "bg-background/80 p-2 rounded border border-border overflow-x-auto"
                      )}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
