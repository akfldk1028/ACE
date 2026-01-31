import { useState, useEffect, useCallback } from 'react';
import { Bot, Check, X, Loader2, RefreshCw, ExternalLink, Wifi, WifiOff } from 'lucide-react';
import { Button } from './ui/button';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { cn } from '../lib/utils';

interface AutogenResult {
  workflow_name: string;
  task: string;
  result: string;
  agents_used: string[];
  status: string;
  timestamp: string;
  source?: string;  // 'autogen-studio-direct' or 'shared-memory'
}

interface AutogenStatusBadgeProps {
  className?: string;
}

type StatusType = 'loading' | 'connected' | 'disconnected' | 'has-data';

/**
 * AutoGen Studio status badge for the sidebar.
 * ★ 8081 직접 연결 - SharedMemory(8101) 없이도 동작!
 */
export function AutogenStatusBadge({ className }: AutogenStatusBadgeProps) {
  const [status, setStatus] = useState<StatusType>('loading');
  const [isOpen, setIsOpen] = useState(false);
  const [latestResult, setLatestResult] = useState<AutogenResult | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [autogenOnline, setAutogenOnline] = useState(false);
  // ★ SharedMemory (8101) 제거됨 - 2026-01-25

  // ★ AutoGen Studio (8081)만 체크 - SharedMemory (8101) 사용 안함!
  const checkStatus = useCallback(async () => {
    if (isPolling) return;
    setIsPolling(true);

    try {
      // AutoGen Studio(8081) 체크 - getAutogenLatest() 사용
      const response = await window.electronAPI.getAutogenLatest();
      if (response.success && response.data) {
        setLatestResult(response.data);
        setStatus('has-data');
        setAutogenOnline(true);
        return;
      }

      // 데이터 없으면 version API로 연결 상태만 확인
      try {
        const autogenCheck = await fetch('/api/autogen/version', {
          method: 'GET',
          headers: { Accept: 'application/json' }
        });
        setAutogenOnline(autogenCheck.ok);
        setStatus(autogenCheck.ok ? 'connected' : 'disconnected');
      } catch {
        setAutogenOnline(false);
        setStatus('disconnected');
      }

      setLatestResult(null);
    } catch (err) {
      console.debug('[AutogenStatusBadge] Check failed:', err);
      setStatus('disconnected');
      setAutogenOnline(false);
    } finally {
      setIsPolling(false);
    }
  }, [isPolling]);

  // Initial check and periodic polling
  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [checkStatus]);

  // Force refresh when popover opens
  useEffect(() => {
    if (isOpen) {
      checkStatus();
    }
  }, [isOpen, checkStatus]);

  const getStatusColor = () => {
    switch (status) {
      case 'has-data':
        return 'bg-green-500';
      case 'connected':
        return 'bg-blue-500';
      case 'disconnected':
        return 'bg-destructive';
      default:
        return 'bg-muted-foreground';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'loading':
        return <Loader2 className="h-3 w-3 animate-spin" />;
      case 'has-data':
        return <Check className="h-3 w-3" />;
      case 'connected':
        return <Wifi className="h-3 w-3" />;
      case 'disconnected':
        return <WifiOff className="h-3 w-3" />;
    }
  };

  const getTooltipText = () => {
    switch (status) {
      case 'loading':
        return 'Checking AutoGen Studio...';
      case 'has-data':
        return 'AutoGen Studio connected (has data)';
      case 'connected':
        return 'SharedMemory connected (no data yet)';
      case 'disconnected':
        return 'SharedMemory disconnected';
    }
  };

  const formatTimestamp = (ts: string) => {
    try {
      const date = new Date(ts);
      return date.toLocaleString('ko-KR', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return ts;
    }
  };

  const isCompleted = latestResult?.status === 'completed' || latestResult?.status === 'complete';

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                'w-full justify-start gap-2 text-xs',
                status === 'disconnected' ? 'text-destructive' : '',
                status === 'has-data' ? 'text-green-600 dark:text-green-500' : '',
                className
              )}
            >
              <div className="relative">
                <Bot className="h-4 w-4" />
                <span
                  className={cn(
                    'absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full',
                    getStatusColor()
                  )}
                />
              </div>
              <span className="truncate">AutoGen Studio</span>
              {status === 'has-data' && (
                <span className="ml-auto text-[10px] bg-green-500/20 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded">
                  NEW
                </span>
              )}
              {status === 'disconnected' && (
                <span className="ml-auto text-[10px] bg-destructive/20 text-destructive px-1.5 py-0.5 rounded">
                  Offline
                </span>
              )}
            </Button>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent side="right">{getTooltipText()}</TooltipContent>
      </Tooltip>

      <PopoverContent side="right" align="end" className="w-80">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h4 className="text-sm font-medium">AutoGen Studio</h4>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  {getStatusIcon()}
                  {status === 'has-data' && 'Connected (has data)'}
                  {status === 'connected' && 'Connected (no data)'}
                  {status === 'disconnected' && 'Disconnected'}
                  {status === 'loading' && 'Checking...'}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => checkStatus()}
              disabled={isPolling}
            >
              <RefreshCw className={cn('h-4 w-4', isPolling && 'animate-spin')} />
            </Button>
          </div>

          {/* Connection Status - ★ 8081만 사용! */}
          <div className="text-xs space-y-1 p-2 bg-muted rounded-md">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">AutoGen Studio (8081):</span>
              <span className={cn('font-medium', autogenOnline ? 'text-green-600' : 'text-destructive')}>
                {autogenOnline ? 'Connected' : 'Offline'}
              </span>
            </div>
          </div>

          {/* Latest Result */}
          {latestResult ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium">Latest Result</span>
                <span className={cn(
                  'text-[10px] px-1.5 py-0.5 rounded',
                  isCompleted ? 'bg-green-500/20 text-green-600' : 'bg-yellow-500/20 text-yellow-600'
                )}>
                  {latestResult.status}
                </span>
              </div>

              <div className="text-xs space-y-2 p-2 bg-muted rounded-md">
                <div>
                  <span className="text-muted-foreground">Workflow: </span>
                  <span className="font-medium">{latestResult.workflow_name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Task: </span>
                  <span className="line-clamp-2">{latestResult.task}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Result: </span>
                  <span className="line-clamp-3 text-green-600 dark:text-green-400">
                    {latestResult.result}
                  </span>
                </div>
                {latestResult.agents_used?.length > 0 && (
                  <div>
                    <span className="text-muted-foreground">Agents: </span>
                    <span>{latestResult.agents_used.join(', ')}</span>
                  </div>
                )}
                <div className="text-muted-foreground">
                  {formatTimestamp(latestResult.timestamp)}
                </div>
              </div>
            </div>
          ) : autogenOnline ? (
            <div className="text-xs text-center text-muted-foreground py-4">
              <p>No AutoGen results yet.</p>
              <p className="mt-1">Run a workflow in AutoGen Studio to see results here.</p>
            </div>
          ) : (
            <div className="text-xs text-center text-muted-foreground py-4">
              <p className="text-destructive font-medium">AutoGen Studio not running</p>
              <p className="mt-2">Start AutoGen Studio:</p>
              <code className="block mt-1 p-2 bg-muted rounded text-[10px]">
                autogenstudio ui --port 8081
              </code>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 gap-1 text-xs"
              onClick={() => window.electronAPI?.openExternal?.('http://localhost:8081')}
            >
              <ExternalLink className="h-3 w-3" />
              Open AutoGen Studio
            </Button>
          </div>

          {/* ★ SharedMemory (8101) 제거됨 - 2026-01-25 */}
        </div>
      </PopoverContent>
    </Popover>
  );
}
