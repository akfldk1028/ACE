import { useState, useEffect, useCallback, useRef } from 'react';
import { Bot, ChevronDown, ChevronUp, X, Check, AlertCircle, Loader2, RefreshCw, Users } from 'lucide-react';
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

/**
 * AutogenResultsWidget Component
 *
 * A floating widget that shows AutoGen Studio execution results from SharedMemory.
 * Polls the SharedMemory every 3 seconds to fetch the latest autogen_latest key.
 * Appears in the bottom-left corner when there are results.
 *
 * ★ AutoGen Studio → SharedMemory → Auto-Claude UI 연동
 */
export function AutogenResultsWidget() {
  const [result, setResult] = useState<AutogenResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isPolling, setIsPolling] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [isNew, setIsNew] = useState(false);
  const lastTimestampRef = useRef<string | null>(null);

  const fetchLatest = useCallback(async () => {
    if (isPolling) return;
    setIsPolling(true);

    try {
      const response = await window.electronAPI.getAutogenLatest();

      // Debug: Log the actual response
      console.log('[AutogenWidget] Response:', JSON.stringify(response, null, 2));

      if (response.success && response.data) {
        const newResult = response.data;

        // Check if this is a new result
        if (lastTimestampRef.current !== newResult.timestamp) {
          setIsNew(true);
          lastTimestampRef.current = newResult.timestamp;
          setIsDismissed(false); // Re-show widget on new result
        }

        setResult(newResult);
        setError(null);
      } else if (!response.success && response.error) {
        // Only show error if we had a result before (connection was working)
        if (result) {
          setError(response.error);
        }
      }
    } catch (err) {
      // Silent failure - SharedMemory may not be running
      console.debug('[AutogenWidget] Fetch failed:', err);
    } finally {
      setIsPolling(false);
    }
  }, [isPolling, result]);

  // Poll every 3 seconds
  useEffect(() => {
    fetchLatest();
    const interval = setInterval(fetchLatest, 3000);
    return () => clearInterval(interval);
  }, [fetchLatest]);

  // Clear "new" badge after 5 seconds
  useEffect(() => {
    if (isNew) {
      const timeout = setTimeout(() => setIsNew(false), 5000);
      return () => clearTimeout(timeout);
    }
  }, [isNew]);

  // Don't render if no result or dismissed
  if (!result || isDismissed) {
    return null;
  }

  // Note: AutoGen Studio uses "complete" (no 'd'), so check both
  const isCompleted = result.status === 'completed' || result.status === 'complete';
  const isFailed = result.status === 'error' || result.status === 'failed';

  const statusIcon = isCompleted ? (
    <Check className="h-4 w-4 text-success" />
  ) : isFailed ? (
    <AlertCircle className="h-4 w-4 text-destructive" />
  ) : (
    <Loader2 className="h-4 w-4 animate-spin text-primary" />
  );

  const formatTimestamp = (ts: string) => {
    try {
      const date = new Date(ts);
      return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts;
    }
  };

  return (
    <div className="fixed bottom-4 left-4 z-50 max-w-md">
      <div className={cn(
        'rounded-lg border shadow-lg overflow-hidden transition-colors',
        isNew ? 'border-primary bg-primary/5' : 'border-border bg-card'
      )}>
        {/* Header */}
        <button
          type="button"
          className={cn(
            'flex items-center justify-between px-3 py-2 cursor-pointer w-full text-left',
            isNew ? 'bg-primary/10' : 'bg-muted/50'
          )}
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-label="Toggle AutoGen results"
        >
          <div className="flex items-center gap-2">
            <Bot className={cn('h-4 w-4', isNew ? 'text-primary' : 'text-muted-foreground')} />
            <span className="text-sm font-medium">
              AutoGen Studio
              {isNew && (
                <span className="ml-2 px-1.5 py-0.5 text-[10px] bg-primary text-primary-foreground rounded-full">
                  NEW
                </span>
              )}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                fetchLatest();
              }}
              className="p-1 hover:bg-muted rounded"
              aria-label="Refresh"
            >
              <RefreshCw className={cn('h-3.5 w-3.5 text-muted-foreground', isPolling && 'animate-spin')} />
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsDismissed(true);
              }}
              className="p-1 hover:bg-muted rounded"
              aria-label="Dismiss"
            >
              <X className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </button>

        {/* Content (expanded) */}
        {isExpanded && (
          <div className="px-3 py-2 space-y-2">
            {/* Workflow name and status */}
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-foreground truncate max-w-[250px]">
                {result.workflow_name}
              </span>
              <div className="flex items-center gap-1.5">
                {statusIcon}
                <span className="text-[10px] text-muted-foreground">
                  {formatTimestamp(result.timestamp)}
                </span>
              </div>
            </div>

            {/* Task */}
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Task</span>
              <p className="text-xs text-foreground bg-muted/50 rounded px-2 py-1 line-clamp-2">
                {result.task}
              </p>
            </div>

            {/* Result */}
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Result</span>
              <p className="text-xs text-foreground bg-success/10 rounded px-2 py-1 line-clamp-3 whitespace-pre-wrap">
                {result.result}
              </p>
            </div>

            {/* Agents used */}
            {result.agents_used && result.agents_used.length > 0 && (
              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <Users className="h-3 w-3" />
                <span className="truncate">
                  {result.agents_used.join(', ')}
                </span>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="flex items-center gap-1 text-[10px] text-destructive">
                <AlertCircle className="h-3 w-3" />
                <span>{error}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
