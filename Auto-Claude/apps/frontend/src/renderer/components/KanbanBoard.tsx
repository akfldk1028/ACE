import { useState, useMemo, memo, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useViewState } from '../contexts/ViewStateContext';
import { FolderPlus, Zap } from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy
} from '@dnd-kit/sortable';
import { Plus, Inbox, Loader2, Eye, CheckCircle2, Archive, RefreshCw, GitPullRequest, X } from 'lucide-react';
import { Checkbox } from './ui/checkbox';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { TaskCard } from './TaskCard';
import { SortableTaskCard } from './SortableTaskCard';
import { TASK_STATUS_COLUMNS, TASK_STATUS_LABELS } from '../../shared/constants';
import { cn } from '../lib/utils';
import { persistTaskStatus, forceCompleteTask, archiveTasks, useTaskStore } from '../stores/task-store';
import { useToast } from '../hooks/use-toast';
import { WorktreeCleanupDialog } from './WorktreeCleanupDialog';
import { BulkPRDialog } from './BulkPRDialog';
import type { Task, TaskStatus, TaskOrderState } from '../../shared/types';

// Type guard for valid drop column targets - preserves literal type from TASK_STATUS_COLUMNS
const VALID_DROP_COLUMNS = new Set<string>(TASK_STATUS_COLUMNS);
function isValidDropColumn(id: string): id is typeof TASK_STATUS_COLUMNS[number] {
  return VALID_DROP_COLUMNS.has(id);
}

/**
 * Get the visual column for a task status.
 * pr_created tasks are displayed in the 'done' column, so we map them accordingly.
 * This is used to compare visual positions during drag-and-drop operations.
 */
function getVisualColumn(status: TaskStatus): typeof TASK_STATUS_COLUMNS[number] {
  return status === 'pr_created' ? 'done' : status;
}

interface KanbanBoardProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  onNewTaskClick?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

interface DroppableColumnProps {
  status: TaskStatus;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  onStatusChange: (taskId: string, newStatus: TaskStatus) => unknown;
  isOver: boolean;
  onAddClick?: () => void;
  onArchiveAll?: () => void;
  archivedCount?: number;
  showArchived?: boolean;
  onToggleArchived?: () => void;
  // Selection props for human_review column
  selectedTaskIds?: Set<string>;
  onSelectAll?: () => void;
  onDeselectAll?: () => void;
  onToggleSelect?: (taskId: string) => void;
}

/**
 * Compare two tasks arrays for meaningful changes.
 * Returns true if tasks are equivalent (should skip re-render).
 */
function tasksAreEquivalent(prevTasks: Task[], nextTasks: Task[]): boolean {
  if (prevTasks.length !== nextTasks.length) return false;
  if (prevTasks === nextTasks) return true;

  // Compare by ID and fields that affect rendering
  for (let i = 0; i < prevTasks.length; i++) {
    const prev = prevTasks[i];
    const next = nextTasks[i];
    if (
      prev.id !== next.id ||
      prev.status !== next.status ||
      prev.executionProgress?.phase !== next.executionProgress?.phase ||
      // Use getTime() for Date comparison (avoid reference inequality on recreated Dates)
      prev.updatedAt?.getTime?.() !== next.updatedAt?.getTime?.() ||
      // AutoGen trigger status changes
      (prev.metadata as Record<string, unknown>)?.triggerStatus !== (next.metadata as Record<string, unknown>)?.triggerStatus
    ) {
      return false;
    }
  }
  return true;
}

/**
 * Custom comparator for DroppableColumn memo.
 */
function droppableColumnPropsAreEqual(
  prevProps: DroppableColumnProps,
  nextProps: DroppableColumnProps
): boolean {
  // Quick checks first
  if (prevProps.status !== nextProps.status) return false;
  if (prevProps.isOver !== nextProps.isOver) return false;
  if (prevProps.onTaskClick !== nextProps.onTaskClick) return false;
  if (prevProps.onStatusChange !== nextProps.onStatusChange) return false;
  if (prevProps.onAddClick !== nextProps.onAddClick) return false;
  if (prevProps.onArchiveAll !== nextProps.onArchiveAll) return false;
  if (prevProps.archivedCount !== nextProps.archivedCount) return false;
  if (prevProps.showArchived !== nextProps.showArchived) return false;
  if (prevProps.onToggleArchived !== nextProps.onToggleArchived) return false;
  if (prevProps.onSelectAll !== nextProps.onSelectAll) return false;
  if (prevProps.onDeselectAll !== nextProps.onDeselectAll) return false;
  if (prevProps.onToggleSelect !== nextProps.onToggleSelect) return false;

  // Compare selectedTaskIds Set
  if (prevProps.selectedTaskIds !== nextProps.selectedTaskIds) {
    // If one is undefined and other isn't, different
    if (!prevProps.selectedTaskIds || !nextProps.selectedTaskIds) return false;
    // Compare Set contents
    if (prevProps.selectedTaskIds.size !== nextProps.selectedTaskIds.size) return false;
    for (const id of prevProps.selectedTaskIds) {
      if (!nextProps.selectedTaskIds.has(id)) return false;
    }
  }

  // Deep compare tasks
  const tasksEqual = tasksAreEquivalent(prevProps.tasks, nextProps.tasks);

  // Only log when re-rendering (reduces noise)
  if (window.DEBUG && !tasksEqual) {
    console.log(`[DroppableColumn] Re-render: ${nextProps.status} column (${nextProps.tasks.length} tasks)`);
  }

  return tasksEqual;
}

// Empty state content for each column
const getEmptyStateContent = (status: TaskStatus, t: (key: string) => string): { icon: React.ReactNode; message: string; subtext?: string } => {
  switch (status) {
    case 'backlog':
      return {
        icon: <Inbox className="h-6 w-6 text-muted-foreground/50" />,
        message: t('kanban.emptyBacklog'),
        subtext: t('kanban.emptyBacklogHint')
      };
    case 'in_progress':
      return {
        icon: <Loader2 className="h-6 w-6 text-muted-foreground/50" />,
        message: t('kanban.emptyInProgress'),
        subtext: t('kanban.emptyInProgressHint')
      };
    case 'ai_review':
      return {
        icon: <Eye className="h-6 w-6 text-muted-foreground/50" />,
        message: t('kanban.emptyAiReview'),
        subtext: t('kanban.emptyAiReviewHint')
      };
    case 'human_review':
      return {
        icon: <Eye className="h-6 w-6 text-muted-foreground/50" />,
        message: t('kanban.emptyHumanReview'),
        subtext: t('kanban.emptyHumanReviewHint')
      };
    case 'done':
      return {
        icon: <CheckCircle2 className="h-6 w-6 text-muted-foreground/50" />,
        message: t('kanban.emptyDone'),
        subtext: t('kanban.emptyDoneHint')
      };
    default:
      return {
        icon: <Inbox className="h-6 w-6 text-muted-foreground/50" />,
        message: t('kanban.emptyDefault')
      };
  }
};

const DroppableColumn = memo(function DroppableColumn({ status, tasks, onTaskClick, onStatusChange, isOver, onAddClick, onArchiveAll, archivedCount, showArchived, onToggleArchived, selectedTaskIds, onSelectAll, onDeselectAll, onToggleSelect }: DroppableColumnProps) {
  const { t } = useTranslation(['tasks', 'common']);
  const { setNodeRef } = useDroppable({
    id: status
  });

  // Calculate selection state for human_review column
  const isHumanReview = status === 'human_review';
  const selectedCount = selectedTaskIds?.size ?? 0;
  const taskCount = tasks.length;
  const isAllSelected = isHumanReview && taskCount > 0 && selectedCount === taskCount;
  const isSomeSelected = isHumanReview && selectedCount > 0 && selectedCount < taskCount;

  // Determine checkbox checked state: true (all), 'indeterminate' (some), false (none)
  const selectAllCheckedState: boolean | 'indeterminate' = isAllSelected
    ? true
    : isSomeSelected
      ? 'indeterminate'
      : false;

  // Handle select all checkbox change
  const handleSelectAllChange = useCallback(() => {
    if (isAllSelected) {
      onDeselectAll?.();
    } else {
      onSelectAll?.();
    }
  }, [isAllSelected, onSelectAll, onDeselectAll]);

  // Memoize taskIds to prevent SortableContext from re-rendering unnecessarily
  const taskIds = useMemo(() => tasks.map((t) => t.id), [tasks]);

  // Create stable onClick handlers for each task to prevent unnecessary re-renders
  const onClickHandlers = useMemo(() => {
    const handlers = new Map<string, () => void>();
    tasks.forEach((task) => {
      handlers.set(task.id, () => onTaskClick(task));
    });
    return handlers;
  }, [tasks, onTaskClick]);

  // Create stable onStatusChange handlers for each task
  const onStatusChangeHandlers = useMemo(() => {
    const handlers = new Map<string, (newStatus: TaskStatus) => unknown>();
    tasks.forEach((task) => {
      handlers.set(task.id, (newStatus: TaskStatus) => onStatusChange(task.id, newStatus));
    });
    return handlers;
  }, [tasks, onStatusChange]);

  // Create stable onToggleSelect handlers for each task (only for human_review column)
  const onToggleSelectHandlers = useMemo(() => {
    if (!onToggleSelect) return null;
    const handlers = new Map<string, () => void>();
    tasks.forEach((task) => {
      handlers.set(task.id, () => onToggleSelect(task.id));
    });
    return handlers;
  }, [tasks, onToggleSelect]);

  // Memoize task card elements to prevent recreation on every render
  const taskCards = useMemo(() => {
    if (tasks.length === 0) return null;
    const isSelectable = !!onToggleSelectHandlers;
    return tasks.map((task) => (
      <SortableTaskCard
        key={task.id}
        task={task}
        onClick={onClickHandlers.get(task.id)!}
        onStatusChange={onStatusChangeHandlers.get(task.id)}
        isSelectable={isSelectable}
        isSelected={isSelectable ? selectedTaskIds?.has(task.id) : undefined}
        onToggleSelect={onToggleSelectHandlers?.get(task.id)}
      />
    ));
  }, [tasks, onClickHandlers, onStatusChangeHandlers, onToggleSelectHandlers, selectedTaskIds]);

  const getColumnBorderColor = (): string => {
    switch (status) {
      case 'backlog':
        return 'column-backlog';
      case 'in_progress':
        return 'column-in-progress';
      case 'ai_review':
        return 'column-ai-review';
      case 'human_review':
        return 'column-human-review';
      case 'done':
        return 'column-done';
      default:
        return 'border-t-muted-foreground/30';
    }
  };

  const emptyState = getEmptyStateContent(status, t);

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex min-w-72 max-w-[30rem] flex-1 flex-col rounded-xl border border-white/5 bg-linear-to-b from-secondary/30 to-transparent backdrop-blur-sm transition-all duration-200',
        getColumnBorderColor(),
        'border-t-2',
        isOver && 'drop-zone-highlight'
      )}
    >
      {/* Column header - enhanced styling */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div className="flex items-center gap-2.5">
          {/* Select All checkbox for human_review column */}
          {isHumanReview && onSelectAll && onDeselectAll && (
            <Tooltip delayDuration={200}>
              <TooltipTrigger asChild>
                <div className="flex items-center">
                  <Checkbox
                    checked={selectAllCheckedState}
                    onCheckedChange={handleSelectAllChange}
                    disabled={taskCount === 0}
                    aria-label={isAllSelected ? t('kanban.deselectAll') : t('kanban.selectAll')}
                    className="h-4 w-4"
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                {isAllSelected ? t('kanban.deselectAll') : t('kanban.selectAll')}
              </TooltipContent>
            </Tooltip>
          )}
          <h2 className="font-semibold text-sm text-foreground">
            {t(TASK_STATUS_LABELS[status])}
          </h2>
          <span className="column-count-badge">
            {tasks.length}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {status === 'backlog' && onAddClick && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 hover:bg-primary/10 hover:text-primary transition-colors"
              onClick={onAddClick}
              aria-label={t('kanban.addTaskAriaLabel')}
            >
              <Plus className="h-4 w-4" />
            </Button>
          )}
          {status === 'done' && onArchiveAll && tasks.length > 0 && !showArchived && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 hover:bg-muted-foreground/10 hover:text-muted-foreground transition-colors"
              onClick={onArchiveAll}
              aria-label={t('tooltips.archiveAllDone')}
            >
              <Archive className="h-4 w-4" />
            </Button>
          )}
          {status === 'done' && archivedCount !== undefined && archivedCount > 0 && onToggleArchived && (
            <Tooltip delayDuration={200}>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    'h-7 w-7 transition-colors relative',
                    showArchived
                      ? 'text-primary bg-primary/10 hover:bg-primary/20'
                      : 'hover:bg-muted-foreground/10 hover:text-muted-foreground'
                  )}
                  onClick={onToggleArchived}
                  aria-pressed={showArchived}
                  aria-label={t('common:accessibility.toggleShowArchivedAriaLabel')}
                >
                  <Archive className="h-4 w-4" />
                  <span className="absolute -top-1 -right-1 text-[10px] font-medium bg-muted rounded-full min-w-[14px] h-[14px] flex items-center justify-center">
                    {archivedCount}
                  </span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {showArchived ? t('common:projectTab.hideArchived') : t('common:projectTab.showArchived')}
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>

      {/* Task list */}
      <div className="flex-1 min-h-0">
        <ScrollArea className="h-full px-3 pb-3 pt-2">
          <SortableContext
            items={taskIds}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-3 min-h-[120px]">
              {tasks.length === 0 ? (
                <div
                  className={cn(
                    'empty-column-dropzone flex flex-col items-center justify-center py-6',
                    isOver && 'active'
                  )}
                >
                  {isOver ? (
                    <>
                      <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center mb-2">
                        <Plus className="h-4 w-4 text-primary" />
                      </div>
                      <span className="text-sm font-medium text-primary">{t('kanban.dropHere')}</span>
                    </>
                  ) : (
                    <>
                      {emptyState.icon}
                      <span className="mt-2 text-sm font-medium text-muted-foreground/70">
                        {emptyState.message}
                      </span>
                      {emptyState.subtext && (
                        <span className="mt-0.5 text-xs text-muted-foreground/50">
                          {emptyState.subtext}
                        </span>
                      )}
                    </>
                  )}
                </div>
              ) : (
                taskCards
              )}
            </div>
          </SortableContext>
        </ScrollArea>
      </div>
    </div>
  );
}, droppableColumnPropsAreEqual);

// ★ Agent name → Kanban column mapping (역할 기반)
function agentToColumn(agentName: string): TaskStatus {
  const name = agentName.toLowerCase();
  if (name.includes('insight') || name.includes('plan') || name.includes('architect'))
    return 'backlog';        // Planning
  if (name.includes('code') || name.includes('implement') || name.includes('develop'))
    return 'in_progress';    // In Progress
  if (name.includes('review') || name.includes('qa') || name.includes('test') || name.includes('critic'))
    return 'ai_review';      // AI Review
  if (name === 'user')
    return 'backlog';        // User input = Planning
  return 'in_progress';      // Default
}

// ★ Convert a single AutoGen run → multiple Task cards (header + per-agent)
function autogenRunToTasks(run: {
  sessionId: number | string;
  runId?: number;
  status: string;
  task: string;
  messages: Array<{
    id: string;
    source: string;
    content: string;
    timestamp: string;
    type: string;
  }>;
  timestamp: string;
}): Task[] {
  const tasks: Task[] = [];
  const messages = run.messages || [];
  const runStatus = (run.status || '').toUpperCase();
  const sessionId = run.sessionId;
  const timestamp = run.timestamp ? new Date(run.timestamp) : new Date();
  const ageMs = Date.now() - timestamp.getTime();
  const isRecent = ageMs < 5 * 60 * 1000; // 5분 이내

  // Count non-user agents
  const agentMessages = messages.filter(m => m.source && m.source !== 'user');
  const agentCount = agentMessages.length;

  // Determine header status
  let headerStatus: TaskStatus = 'in_progress';
  if (runStatus === 'COMPLETE' || runStatus === 'COMPLETED') {
    headerStatus = 'done';
  } else if (runStatus === 'ERROR' || runStatus === 'FAILED') {
    headerStatus = 'human_review';
  } else if (runStatus === 'PENDING' || runStatus === 'QUEUED') {
    headerStatus = 'backlog';
  }

  // Extract task description from first user message
  const userMsg = messages.find(m => m.source === 'user');
  const taskDescription = userMsg?.content || run.task || 'AutoGen Task';

  // 1) Session header card
  tasks.push({
    id: `autogen_session_${sessionId}_header`,
    projectId: 'autogen',
    specId: `autogen_session_${sessionId}`,
    title: `[AutoGen] Session ${sessionId}`,
    description: taskDescription.length > 200 ? taskDescription.slice(0, 200) + '...' : taskDescription,
    status: headerStatus,
    createdAt: timestamp,
    updatedAt: timestamp,
    subtasks: [],
    logs: [],
    metadata: {
      source: 'autogen-session-header',
      isHeader: true,
      agentCount,
      runStatus: runStatus,
      sessionId: String(sessionId),
    } as Task['metadata']
  });

  // 2) Per-agent cards
  // Find the index of the last non-user message for "isLastAgent" detection
  let lastAgentIdx = -1;
  for (let j = messages.length - 1; j >= 0; j--) {
    if (messages[j].source && messages[j].source !== 'user') {
      lastAgentIdx = j;
      break;
    }
  }

  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    if (!msg.source || msg.source === 'user') continue;

    const isLastAgent = (i === lastAgentIdx);
    let column: TaskStatus;

    if (runStatus === 'COMPLETE' || runStatus === 'COMPLETED') {
      // Complete + recent: keep agent in role column for review
      // Complete + old: move all to done
      column = isRecent ? agentToColumn(msg.source) : 'done';
    } else if (runStatus === 'ERROR' || runStatus === 'FAILED') {
      column = 'human_review';
    } else if (runStatus === 'RUNNING' || runStatus === 'IN_PROGRESS' || runStatus === 'ACTIVE') {
      // Running: last agent is actively working, others in their role column
      column = agentToColumn(msg.source);
    } else {
      column = agentToColumn(msg.source);
    }

    tasks.push({
      id: `autogen_s${sessionId}_agent_${i}`,
      projectId: 'autogen',
      specId: `autogen_session_${sessionId}`,
      title: `  └ ${msg.source}`,
      description: (msg.content || '').slice(0, 300),
      status: column,
      createdAt: timestamp,
      updatedAt: timestamp,
      subtasks: [],
      logs: [],
      metadata: {
        source: 'autogen-agent',
        agent: msg.source,
        parentSession: String(sessionId),
        isLastAgent: isLastAgent && (runStatus === 'RUNNING' || runStatus === 'IN_PROGRESS' || runStatus === 'ACTIVE'),
      } as Task['metadata']
    });
  }

  return tasks;
}

// ──────────────────────────────────────────────
// Pipeline types for AG-ACE-BRIDGE integration
// ──────────────────────────────────────────────

interface PipelineTask {
  id: string;
  title: string;
  description: string;
  stage: string;   // planning | coding | reviewing | testing | done | error
  agent: string;
  status: string;  // pending | in_progress | completed | failed
  started_at?: string;
  completed_at?: string;
}

interface PipelineProject {
  project_id: string;
  name: string;
  path: string;
  status: string;
}

/**
 * Map pipeline task stage+status to Kanban TaskStatus
 */
function pipelineTaskToKanbanStatus(task: PipelineTask): TaskStatus {
  if (task.status === 'failed') return 'human_review';
  if (task.status === 'completed' || task.stage === 'done') return 'done';

  switch (task.stage) {
    case 'planning': return 'backlog';
    case 'coding': return 'in_progress';
    case 'reviewing': return 'ai_review';
    case 'testing': return 'ai_review';
    case 'error': return 'human_review';
    default: return 'in_progress';
  }
}

/**
 * Convert pipeline task to Kanban Task object
 */
function pipelineTaskToTask(pt: PipelineTask, projectId: string): Task {
  const status = pipelineTaskToKanbanStatus(pt);
  return {
    id: `pipeline_${pt.id}`,
    projectId,
    specId: `pipeline_${pt.id}`,
    title: pt.title,
    description: pt.description,
    status,
    createdAt: pt.started_at ? new Date(pt.started_at) : new Date(),
    updatedAt: pt.completed_at ? new Date(pt.completed_at) : new Date(),
    subtasks: [],
    logs: [],
    metadata: {
      source: 'pipeline',
      agent: pt.agent,
      stage: pt.stage,
    } as Task['metadata'],
  };
}

export function KanbanBoard({ tasks, onTaskClick, onNewTaskClick, onRefresh, isRefreshing }: KanbanBoardProps) {
  const { t } = useTranslation(['tasks', 'dialogs', 'common']);
  const { toast } = useToast();
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [overColumnId, setOverColumnId] = useState<string | null>(null);
  const { showArchived, toggleShowArchived } = useViewState();

  // AutoGen results state
  const [autogenTasks, setAutogenTasks] = useState<Task[]>([]);
  const autogenPollRef = useRef<NodeJS.Timeout | null>(null);

  // ★ 24/7 Auto-trigger: track processed sessions + trigger status
  // Using refs for trigger state to avoid useEffect dependency loops
  const processedSessionsRef = useRef<Set<string>>(new Set());
  const triggerLogRef = useRef<Record<string, { status: 'triggered' | 'running' | 'done' | 'error'; execId?: string; message?: string }>>({});
  // Counter to force re-render when triggerLog changes (avoids object dep in useEffect)
  const [triggerLogVersion, setTriggerLogVersion] = useState(0);
  // Queue for serialized execution (prevent concurrent workflowExecute calls)
  const triggerQueueRef = useRef<Array<{ sessionId: string; taskDesc: string }>>([]);
  const isProcessingQueueRef = useRef(false);
  // Initial load flag - skip triggers until first fetch completes
  const initialLoadDoneRef = useRef(false);
  // Execution status polling
  const execPollRef = useRef<NodeJS.Timeout | null>(null);

  // Pipeline project state
  const [pipelineProjects, setPipelineProjects] = useState<PipelineProject[]>([]);
  const [pipelineTasks, setPipelineTasks] = useState<Task[]>([]);
  const pipelinePollRef = useRef<NodeJS.Timeout | null>(null);

  // Project creation dialog state
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [projectForm, setProjectForm] = useState({
    path: 'D:\\AutoClaude\\01_TEST',
    name: 'calculator',
    description: 'Create a Python calculator with basic operations and unit tests',
  });
  const [isCreatingProject, setIsCreatingProject] = useState(false);

  // ★ 24/7 Auto-trigger: serialized queue processor
  // Processes one trigger at a time to prevent concurrent workflowExecute calls
  const processQueue = useCallback(async () => {
    if (isProcessingQueueRef.current) return;
    if (triggerQueueRef.current.length === 0) return;

    isProcessingQueueRef.current = true;

    while (triggerQueueRef.current.length > 0) {
      const { sessionId, taskDesc } = triggerQueueRef.current.shift()!;
      const key = String(sessionId);

      console.log(`[24/7] Auto-triggering workflow for session ${sessionId}: "${taskDesc.slice(0, 80)}..."`);
      triggerLogRef.current = { ...triggerLogRef.current, [key]: { status: 'triggered' } };
      setTriggerLogVersion(v => v + 1);

      try {
        // Infer complexity from agent count
        const agentCount = processedSessionsRef.current.size; // rough heuristic
        const complexity: 'simple' | 'standard' | 'complex' =
          taskDesc.length < 100 ? 'simple' : taskDesc.length > 500 ? 'complex' : 'standard';

        const response = await window.electronAPI.workflowExecute(
          taskDesc,
          complexity,
          false // Don't auto-merge; let human review
        );

        if (response.success && response.data?.success) {
          console.log(`[24/7] Workflow triggered for session ${sessionId}:`, response.data.exec_id);
          triggerLogRef.current = {
            ...triggerLogRef.current,
            [key]: { status: 'running', execId: response.data.exec_id, message: response.data.message }
          };
          setTriggerLogVersion(v => v + 1);
          toast({
            title: `[24/7] Auto-pipeline started`,
            description: `Session ${sessionId} → ${response.data.exec_id || 'running'}`,
          });
        } else {
          console.warn(`[24/7] Workflow trigger failed for session ${sessionId}:`, response.error);
          triggerLogRef.current = {
            ...triggerLogRef.current,
            [key]: { status: 'error', message: response.error || 'Unknown error' }
          };
          setTriggerLogVersion(v => v + 1);
        }
      } catch (err) {
        console.error(`[24/7] Workflow trigger error for session ${sessionId}:`, err);
        triggerLogRef.current = {
          ...triggerLogRef.current,
          [key]: { status: 'error', message: String(err) }
        };
        setTriggerLogVersion(v => v + 1);
      }
    }

    isProcessingQueueRef.current = false;
  }, [toast]);

  // ★ 24/7 Execution status polling: check running executions periodically
  useEffect(() => {
    const pollExecutionStatus = async () => {
      const runningEntries = Object.entries(triggerLogRef.current)
        .filter(([, v]) => v.status === 'running' && v.execId);

      if (runningEntries.length === 0) return;

      for (const [sessionKey, entry] of runningEntries) {
        try {
          const api = window.electronAPI as unknown as Record<string, unknown>;
          if (typeof api.workflowGetExecution !== 'function') break;

          const result = await (api.workflowGetExecution as (id: string) => Promise<{ success: boolean; data?: { status: string } }>)(entry.execId!);
          if (result.success && result.data) {
            const execStatus = result.data.status;
            if (execStatus === 'completed') {
              triggerLogRef.current = {
                ...triggerLogRef.current,
                [sessionKey]: { ...entry, status: 'done' }
              };
              setTriggerLogVersion(v => v + 1);
              toast({ title: `[24/7] Pipeline completed`, description: `Session ${sessionKey} → ${entry.execId}` });
            } else if (execStatus === 'failed' || execStatus === 'error') {
              triggerLogRef.current = {
                ...triggerLogRef.current,
                [sessionKey]: { ...entry, status: 'error', message: `Execution ${execStatus}` }
              };
              setTriggerLogVersion(v => v + 1);
            }
          }
        } catch {
          // Silently skip poll errors
        }
      }
    };

    execPollRef.current = setInterval(pollExecutionStatus, 10000); // Check every 10s
    return () => {
      if (execPollRef.current) clearInterval(execPollRef.current);
    };
  }, [toast]);

  // ★ Memory cleanup: remove old entries after 1 hour to prevent unbounded growth
  useEffect(() => {
    const cleanup = setInterval(() => {
      const now = Date.now();
      const maxEntries = 100;
      const entries = Object.entries(triggerLogRef.current);
      if (entries.length > maxEntries) {
        // Keep only the most recent maxEntries (by removing done/error entries first)
        const removable = entries.filter(([, v]) => v.status === 'done' || v.status === 'error');
        const toRemove = removable.slice(0, entries.length - maxEntries);
        if (toRemove.length > 0) {
          const updated = { ...triggerLogRef.current };
          for (const [key] of toRemove) {
            delete updated[key];
            processedSessionsRef.current.delete(key);
          }
          triggerLogRef.current = updated;
          setTriggerLogVersion(v => v + 1);
        }
      }
    }, 60 * 60 * 1000); // Every hour
    return () => clearInterval(cleanup);
  }, []);

  // Poll AutoGen results directly from AutoGen Studio (8081)
  // ★ Fixed: useEffect deps are stable (no state objects) → no re-mount loop
  useEffect(() => {
    const fetchAutogenResults = async () => {
      try {
        const detailedResponse = await window.electronAPI.getAutogenRunsDetailed();
        if (detailedResponse.success && detailedResponse.data && detailedResponse.data.length > 0) {
          const detailedTasks: Task[] = [];
          const seenSessions = new Set<string | number>();

          for (const run of detailedResponse.data) {
            if (seenSessions.has(run.sessionId)) continue;
            seenSessions.add(run.sessionId);

            const sessionTasks = autogenRunToTasks(run);
            detailedTasks.push(...sessionTasks);

            // ★ 24/7 Auto-trigger: detect newly completed sessions
            // Skip during initial load (existing sessions marked as processed first)
            if (initialLoadDoneRef.current) {
              const status = (run.status || '').toUpperCase();
              const sessionKey = String(run.sessionId);
              if (
                (status === 'COMPLETE' || status === 'COMPLETED') &&
                !processedSessionsRef.current.has(sessionKey)
              ) {
                processedSessionsRef.current.add(sessionKey);
                const messages = run.messages || [];
                const userMsg = messages.find((m: { source: string }) => m.source === 'user');
                const taskDesc = userMsg?.content || run.task || '';
                if (taskDesc) {
                  triggerQueueRef.current.push({ sessionId: sessionKey, taskDesc });
                  processQueue();
                }
              }
            }
          }

          if (detailedTasks.length > 0) {
            // ★ Enrich header cards with trigger status from ref (no state dep)
            const currentLog = triggerLogRef.current;
            const enriched: Task[] = detailedTasks.map(t => {
              const meta = t.metadata as Record<string, unknown>;
              if (meta?.isHeader && meta?.sessionId) {
                const triggerInfo = currentLog[String(meta.sessionId)];
                if (triggerInfo) {
                  return {
                    ...t,
                    metadata: { ...meta, triggerStatus: triggerInfo.status, triggerExecId: triggerInfo.execId, triggerMessage: triggerInfo.message } as Task['metadata']
                  };
                }
              }
              return t;
            });
            setAutogenTasks(enriched);
            return;
          }
        }
      } catch (err) {
        console.debug('[KanbanBoard] AutoGen fetch error:', err);
      }
    };

    // Initial fetch - mark all existing completed sessions as processed (no re-trigger)
    const initialFetch = async () => {
      try {
        const detailedResponse = await window.electronAPI.getAutogenRunsDetailed();
        if (detailedResponse.success && detailedResponse.data) {
          const detailedTasks: Task[] = [];
          const seenSessions = new Set<string | number>();

          for (const run of detailedResponse.data) {
            if (seenSessions.has(run.sessionId)) continue;
            seenSessions.add(run.sessionId);

            const status = (run.status || '').toUpperCase();
            if (status === 'COMPLETE' || status === 'COMPLETED') {
              processedSessionsRef.current.add(String(run.sessionId));
            }
            detailedTasks.push(...autogenRunToTasks(run));
          }

          if (detailedTasks.length > 0) {
            setAutogenTasks(detailedTasks);
          }
        }
      } catch (err) {
        console.debug('[KanbanBoard] AutoGen initial fetch error:', err);
      }
      // Mark initial load as done → subsequent polls can trigger
      initialLoadDoneRef.current = true;
    };

    initialFetch();

    // Poll every 3 seconds for real-time sync + auto-trigger
    autogenPollRef.current = setInterval(fetchAutogenResults, 3000);

    return () => {
      if (autogenPollRef.current) {
        clearInterval(autogenPollRef.current);
      }
    };
  }, [processQueue]); // ★ Stable dep: processQueue only changes if toast changes (rare)

  // ──────────────────────────────────────────────
  // Pipeline: Create project + plan + poll tasks
  // ──────────────────────────────────────────────

  const handleCreatePipelineProject = useCallback(async () => {
    const api = window.electronAPI as any;
    if (!api.bridgePipelineInit) {
      toast({ title: 'Pipeline API not available', variant: 'destructive' });
      return;
    }

    setIsCreatingProject(true);
    try {
      // Step 1: Init project folder
      const initResult = await api.bridgePipelineInit(
        projectForm.path, projectForm.name, projectForm.description
      );
      if (!initResult.success) {
        toast({ title: 'Failed to init project', description: initResult.error, variant: 'destructive' });
        return;
      }

      const projectId = initResult.data.project_id;
      const newProject: PipelineProject = {
        project_id: projectId,
        name: projectForm.name,
        path: projectForm.path,
        status: 'init',
      };
      setPipelineProjects(prev => [...prev, newProject]);

      // Step 2: Read AutoGen session → decompose to tasks
      const planResult = await api.bridgePipelinePlan(projectId);
      if (planResult.success && planResult.data?.tasks) {
        const kanbanTasks = planResult.data.tasks.map((pt: PipelineTask) =>
          pipelineTaskToTask(pt, projectId)
        );
        setPipelineTasks(prev => [...prev.filter(t => t.projectId !== projectId), ...kanbanTasks]);
      }

      setShowProjectDialog(false);
      toast({ title: `Project "${projectForm.name}" created`, description: `Path: ${projectForm.path}` });
    } catch (err) {
      toast({ title: 'Pipeline error', description: String(err), variant: 'destructive' });
    } finally {
      setIsCreatingProject(false);
    }
  }, [projectForm, toast]);

  // Poll pipeline tasks for all active projects
  useEffect(() => {
    if (pipelineProjects.length === 0) return;

    const pollPipelineTasks = async () => {
      const api = window.electronAPI as any;
      if (!api.bridgePipelineTasks) return;

      const allPipelineTasks: Task[] = [];
      for (const project of pipelineProjects) {
        try {
          const result = await api.bridgePipelineTasks(project.project_id);
          if (result.success && result.data?.tasks) {
            const kanbanTasks = result.data.tasks.map((pt: PipelineTask) =>
              pipelineTaskToTask(pt, project.project_id)
            );
            allPipelineTasks.push(...kanbanTasks);
          }
        } catch {
          // Skip failed polls
        }
      }
      if (allPipelineTasks.length > 0) {
        setPipelineTasks(allPipelineTasks);
      }
    };

    pollPipelineTasks();
    pipelinePollRef.current = setInterval(pollPipelineTasks, 5000);

    return () => {
      if (pipelinePollRef.current) clearInterval(pipelinePollRef.current);
    };
  }, [pipelineProjects]);

  // Combine regular tasks + AutoGen tasks + Pipeline tasks
  const allTasks = useMemo(() => {
    return [...tasks, ...autogenTasks, ...pipelineTasks];
  }, [tasks, autogenTasks, pipelineTasks]);

  // Selection state for bulk actions (Human Review column)
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set());

  // Bulk PR dialog state
  const [bulkPRDialogOpen, setBulkPRDialogOpen] = useState(false);

  // Worktree cleanup dialog state
  const [worktreeCleanupDialog, setWorktreeCleanupDialog] = useState<{
    open: boolean;
    taskId: string | null;
    taskTitle: string;
    worktreePath?: string;
    isProcessing: boolean;
    error?: string;
  }>({
    open: false,
    taskId: null,
    taskTitle: '',
    worktreePath: undefined,
    isProcessing: false,
    error: undefined
  });

  // Calculate archived count for Done column button
  const archivedCount = useMemo(() =>
    allTasks.filter(t => t.metadata?.archivedAt).length,
    [allTasks]
  );

  // Filter tasks based on archive status
  const filteredTasks = useMemo(() => {
    if (showArchived) {
      return allTasks; // Show all tasks including archived
    }
    return allTasks.filter((t) => !t.metadata?.archivedAt);
  }, [allTasks, showArchived]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8 // 8px movement required before drag starts
      }
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates
    })
  );

  // Get task order from store for custom ordering
  const taskOrder = useTaskStore((state) => state.taskOrder);

  const tasksByStatus = useMemo(() => {
    // Note: pr_created tasks are shown in the 'done' column since they're essentially complete
    const grouped: Record<typeof TASK_STATUS_COLUMNS[number], Task[]> = {
      backlog: [],
      in_progress: [],
      ai_review: [],
      human_review: [],
      done: []
    };

    filteredTasks.forEach((task) => {
      // Map pr_created tasks to the done column
      const targetColumn = task.status === 'pr_created' ? 'done' : task.status;
      if (grouped[targetColumn]) {
        grouped[targetColumn].push(task);
      }
    });

    // Sort tasks within each column
    Object.keys(grouped).forEach((status) => {
      const statusKey = status as typeof TASK_STATUS_COLUMNS[number];
      const columnTasks = grouped[statusKey];
      const columnOrder = taskOrder?.[statusKey];

      if (columnOrder && columnOrder.length > 0) {
        // Custom order exists: sort by order index
        // 1. Create a set of current task IDs for fast lookup (filters stale IDs)
        const currentTaskIds = new Set(columnTasks.map(t => t.id));

        // 2. Create valid order by filtering out stale IDs
        const validOrder = columnOrder.filter(id => currentTaskIds.has(id));
        const validOrderSet = new Set(validOrder);

        // 3. Find new tasks not in order (prepend at top)
        const newTasks = columnTasks.filter(t => !validOrderSet.has(t.id));
        // Sort new tasks by createdAt (newest first)
        newTasks.sort((a, b) => {
          const dateA = new Date(a.createdAt).getTime();
          const dateB = new Date(b.createdAt).getTime();
          return dateB - dateA;
        });

        // 4. Sort ordered tasks by their index in validOrder
        // Pre-compute index map for O(n) sorting instead of O(n²) with indexOf
        const indexMap = new Map(validOrder.map((id, idx) => [id, idx]));
        const orderedTasks = columnTasks
          .filter(t => validOrderSet.has(t.id))
          .sort((a, b) => (indexMap.get(a.id) ?? 0) - (indexMap.get(b.id) ?? 0));

        // 5. Prepend new tasks at top, then ordered tasks
        grouped[statusKey] = [...newTasks, ...orderedTasks];
      } else {
        // No custom order: fallback to createdAt sort (newest first)
        grouped[statusKey].sort((a, b) => {
          const dateA = new Date(a.createdAt).getTime();
          const dateB = new Date(b.createdAt).getTime();
          return dateB - dateA;
        });
      }
    });

    return grouped;
  }, [filteredTasks, taskOrder]);

  // Prune stale IDs when tasks move out of human_review column
  useEffect(() => {
    const validIds = new Set(tasksByStatus.human_review.map(t => t.id));
    setSelectedTaskIds(prev => {
      const filtered = new Set([...prev].filter(id => validIds.has(id)));
      return filtered.size === prev.size ? prev : filtered;
    });
  }, [tasksByStatus.human_review]);

  // Selection callbacks for bulk actions (Human Review column)
  const toggleTaskSelection = useCallback((taskId: string) => {
    setSelectedTaskIds(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  }, []);

  const selectAllTasks = useCallback(() => {
    const humanReviewTasks = tasksByStatus.human_review;
    const allIds = new Set(humanReviewTasks.map(t => t.id));
    setSelectedTaskIds(allIds);
  }, [tasksByStatus.human_review]);

  const deselectAllTasks = useCallback(() => {
    setSelectedTaskIds(new Set());
  }, []);

  // Get selected task objects for the BulkPRDialog
  const selectedTasks = useMemo(() => {
    return tasksByStatus.human_review.filter(task => selectedTaskIds.has(task.id));
  }, [tasksByStatus.human_review, selectedTaskIds]);

  // Handle opening the bulk PR dialog
  const handleOpenBulkPRDialog = useCallback(() => {
    if (selectedTaskIds.size > 0) {
      setBulkPRDialogOpen(true);
    }
  }, [selectedTaskIds.size]);

  // Handle bulk PR dialog completion - clear selection
  const handleBulkPRComplete = useCallback(() => {
    deselectAllTasks();
  }, [deselectAllTasks]);

  const handleArchiveAll = async () => {
    // Get projectId from the first task (all tasks should have the same projectId)
    const projectId = tasks[0]?.projectId;
    if (!projectId) {
      console.error('[KanbanBoard] No projectId found');
      return;
    }

    const doneTaskIds = tasksByStatus.done.map((t) => t.id);
    if (doneTaskIds.length === 0) return;

    const result = await archiveTasks(projectId, doneTaskIds);
    if (!result.success) {
      console.error('[KanbanBoard] Failed to archive tasks:', result.error);
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const task = allTasks.find((t) => t.id === active.id);
    if (task) {
      setActiveTask(task);
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { over } = event;

    if (!over) {
      setOverColumnId(null);
      return;
    }

    const overId = over.id as string;

    // Check if over a column
    if (isValidDropColumn(overId)) {
      setOverColumnId(overId);
      return;
    }

    // Check if over a task - get its column
    const overTask = allTasks.find((t) => t.id === overId);
    if (overTask) {
      setOverColumnId(overTask.status);
    }
  };

  /**
   * Handle status change with worktree cleanup dialog support
   * Consolidated handler that accepts an optional task object for the dialog title
   */
  const handleStatusChange = async (taskId: string, newStatus: TaskStatus, providedTask?: Task) => {
    const task = providedTask || allTasks.find(t => t.id === taskId);
    const result = await persistTaskStatus(taskId, newStatus);

    if (!result.success) {
      if (result.worktreeExists) {
        // Show the worktree cleanup dialog
        setWorktreeCleanupDialog({
          open: true,
          taskId: taskId,
          taskTitle: task?.title || t('tasks:untitled'),
          worktreePath: result.worktreePath,
          isProcessing: false,
          error: undefined
        });
      } else {
        // Show error toast for other failures
        toast({
          title: t('common:errors.operationFailed'),
          description: result.error || t('common:errors.unknownError'),
          variant: 'destructive'
        });
      }
    }
  };

  /**
   * Handle worktree cleanup confirmation
   */
  const handleWorktreeCleanupConfirm = async () => {
    if (!worktreeCleanupDialog.taskId) return;

    setWorktreeCleanupDialog(prev => ({ ...prev, isProcessing: true, error: undefined }));

    const result = await forceCompleteTask(worktreeCleanupDialog.taskId);

    if (result.success) {
      setWorktreeCleanupDialog({
        open: false,
        taskId: null,
        taskTitle: '',
        worktreePath: undefined,
        isProcessing: false,
        error: undefined
      });
    } else {
      // Keep dialog open with error state for retry - show actual error if available
      setWorktreeCleanupDialog(prev => ({
        ...prev,
        isProcessing: false,
        error: result.error || t('dialogs:worktreeCleanup.errorDescription')
      }));
    }
  };

  // Get task order actions from store
  const reorderTasksInColumn = useTaskStore((state) => state.reorderTasksInColumn);
  const moveTaskToColumnTop = useTaskStore((state) => state.moveTaskToColumnTop);
  const saveTaskOrderToStorage = useTaskStore((state) => state.saveTaskOrder);
  const loadTaskOrder = useTaskStore((state) => state.loadTaskOrder);
  const setTaskOrder = useTaskStore((state) => state.setTaskOrder);

  // Get projectId from tasks (all tasks in KanbanBoard share the same project)
  const projectId = useMemo(() => tasks[0]?.projectId ?? null, [tasks]);

  const saveTaskOrder = useCallback((projectIdToSave: string) => {
    const success = saveTaskOrderToStorage(projectIdToSave);
    if (!success) {
      toast({
        title: t('kanban.orderSaveFailedTitle'),
        description: t('kanban.orderSaveFailedDescription'),
        variant: 'destructive'
      });
    }
    return success;
  }, [saveTaskOrderToStorage, toast, t]);

  // Load task order on mount and when project changes
  useEffect(() => {
    if (projectId) {
      loadTaskOrder(projectId);
    }
  }, [projectId, loadTaskOrder]);

  // Clean up stale task IDs from order when tasks change (e.g., after deletion)
  // This ensures the persisted order doesn't contain IDs for deleted tasks
  useEffect(() => {
    if (!projectId || !taskOrder) return;

    // Build a set of current task IDs for fast lookup
    const currentTaskIds = new Set(tasks.map(t => t.id));

    // Check each column for stale IDs
    let hasStaleIds = false;
    const cleanedOrder: typeof taskOrder = {
      backlog: [],
      in_progress: [],
      ai_review: [],
      human_review: [],
      pr_created: [],
      done: []
    };

    for (const status of Object.keys(taskOrder) as Array<keyof typeof taskOrder>) {
      const columnOrder = taskOrder[status] || [];
      const cleanedColumnOrder = columnOrder.filter(id => currentTaskIds.has(id));

      cleanedOrder[status] = cleanedColumnOrder;

      // Check if any IDs were removed
      if (cleanedColumnOrder.length !== columnOrder.length) {
        hasStaleIds = true;
      }
    }

    // If stale IDs were found, update the order and persist
    if (hasStaleIds) {
      setTaskOrder(cleanedOrder);
      saveTaskOrder(projectId);
    }
  }, [tasks, taskOrder, projectId, setTaskOrder, saveTaskOrder]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);
    setOverColumnId(null);

    if (!over) return;

    const activeTaskId = active.id as string;
    const overId = over.id as string;

    // Check if dropped on a column
    if (isValidDropColumn(overId)) {
      const newStatus = overId;
      const task = allTasks.find((t) => t.id === activeTaskId);

      if (task && task.status !== newStatus) {
        // Move task to top of target column's order array
        moveTaskToColumnTop(activeTaskId, newStatus, task.status);

        // Persist task order
        if (projectId) {
          saveTaskOrder(projectId);
        }

        // Persist status change to file and update local state
        handleStatusChange(activeTaskId, newStatus, task).catch((err) =>
          console.error('[KanbanBoard] Status change failed:', err)
        );
      }
      return;
    }

    // Check if dropped on another task
    const overTask = allTasks.find((t) => t.id === overId);
    if (overTask) {
      const task = allTasks.find((t) => t.id === activeTaskId);
      if (!task) return;

      // Compare visual columns (pr_created maps to 'done' visually)
      const taskVisualColumn = getVisualColumn(task.status);
      const overTaskVisualColumn = getVisualColumn(overTask.status);

      // Same visual column: reorder within column
      if (taskVisualColumn === overTaskVisualColumn) {
        // Ensure both tasks are in the order array before reordering
        // This handles tasks that existed before ordering was enabled
        const currentColumnOrder = taskOrder?.[taskVisualColumn] ?? [];
        const activeInOrder = currentColumnOrder.includes(activeTaskId);
        const overInOrder = currentColumnOrder.includes(overId);

        if (!activeInOrder || !overInOrder) {
          // Sync the current visual order to the stored order
          // This ensures existing tasks can be reordered
          const visualOrder = tasksByStatus[taskVisualColumn].map(t => t.id);
          setTaskOrder({
            ...taskOrder,
            [taskVisualColumn]: visualOrder
          } as TaskOrderState);
        }

        // Reorder tasks within the same column using the visual column key
        reorderTasksInColumn(taskVisualColumn, activeTaskId, overId);

        if (projectId) {
          saveTaskOrder(projectId);
        }
        return;
      }

      // Different visual column: move to that task's column (status change)
      // Use the visual column key for ordering to ensure consistency
      moveTaskToColumnTop(activeTaskId, overTaskVisualColumn, taskVisualColumn);

      // Persist task order
      if (projectId) {
        saveTaskOrder(projectId);
      }

      handleStatusChange(activeTaskId, overTask.status, task).catch((err) =>
        console.error('[KanbanBoard] Status change failed:', err)
      );
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Kanban header with refresh + pipeline project button */}
      <div className="flex items-center justify-between px-6 pt-4 pb-2">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowProjectDialog(true)}
            className="gap-2"
          >
            <FolderPlus className="h-4 w-4" />
            Pipeline Project
          </Button>
          {pipelineProjects.length > 0 && (
            <span className="text-xs text-muted-foreground">
              {pipelineProjects.length} project(s) | {pipelineTasks.length} task(s)
            </span>
          )}
        </div>
        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="gap-2 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            {isRefreshing ? t('common:buttons.refreshing') : t('tasks:refreshTasks')}
          </Button>
        )}
      </div>
      {/* Kanban columns */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex flex-1 gap-4 overflow-x-auto p-6">
          {TASK_STATUS_COLUMNS.map((status) => (
            <DroppableColumn
              key={status}
              status={status}
              tasks={tasksByStatus[status]}
              onTaskClick={onTaskClick}
              onStatusChange={handleStatusChange}
              isOver={overColumnId === status}
              onAddClick={status === 'backlog' ? onNewTaskClick : undefined}
              onArchiveAll={status === 'done' ? handleArchiveAll : undefined}
              archivedCount={status === 'done' ? archivedCount : undefined}
              showArchived={status === 'done' ? showArchived : undefined}
              onToggleArchived={status === 'done' ? toggleShowArchived : undefined}
              selectedTaskIds={status === 'human_review' ? selectedTaskIds : undefined}
              onSelectAll={status === 'human_review' ? selectAllTasks : undefined}
              onDeselectAll={status === 'human_review' ? deselectAllTasks : undefined}
              onToggleSelect={status === 'human_review' ? toggleTaskSelection : undefined}
            />
          ))}
        </div>

        {/* Drag overlay - enhanced visual feedback */}
        <DragOverlay>
          {activeTask ? (
            <div className="drag-overlay-card">
              <TaskCard task={activeTask} onClick={() => {}} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {selectedTaskIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-3 px-4 py-3 rounded-2xl border border-border bg-card shadow-lg backdrop-blur-sm">
            <span className="text-sm font-medium text-foreground">
              {t('kanban.selectedCountOther', { count: selectedTaskIds.size })}
            </span>
            <div className="w-px h-5 bg-border" />
            <Button
              variant="default"
              size="sm"
              className="gap-2"
              onClick={handleOpenBulkPRDialog}
            >
              <GitPullRequest className="h-4 w-4" />
              {t('kanban.createPRs')}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-muted-foreground hover:text-foreground"
              onClick={deselectAllTasks}
            >
              <X className="h-4 w-4" />
              {t('kanban.clearSelection')}
            </Button>
          </div>
        </div>
      )}

      {/* Worktree cleanup confirmation dialog */}
      <WorktreeCleanupDialog
        open={worktreeCleanupDialog.open}
        taskTitle={worktreeCleanupDialog.taskTitle}
        worktreePath={worktreeCleanupDialog.worktreePath}
        isProcessing={worktreeCleanupDialog.isProcessing}
        error={worktreeCleanupDialog.error}
        onOpenChange={(open) => {
          if (!open && !worktreeCleanupDialog.isProcessing) {
            setWorktreeCleanupDialog(prev => ({ ...prev, open: false, error: undefined }));
          }
        }}
        onConfirm={handleWorktreeCleanupConfirm}
      />

      {/* Bulk PR creation dialog */}
      <BulkPRDialog
        open={bulkPRDialogOpen}
        tasks={selectedTasks}
        onOpenChange={setBulkPRDialogOpen}
        onComplete={handleBulkPRComplete}
      />

      {/* Pipeline Project Creation Dialog */}
      {showProjectDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <FolderPlus className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Create Pipeline Project</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Creates a project folder, reads the latest AutoGen Studio session,
              and decomposes it into pipeline tasks.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Project Path</label>
                <input
                  type="text"
                  value={projectForm.path}
                  onChange={(e) => setProjectForm(prev => ({ ...prev, path: e.target.value }))}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  placeholder="D:\AutoClaude\01_TEST"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Project Name</label>
                <input
                  type="text"
                  value={projectForm.name}
                  onChange={(e) => setProjectForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  placeholder="calculator"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={projectForm.description}
                  onChange={(e) => setProjectForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  rows={2}
                  placeholder="Describe the project..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-5">
              <Button
                variant="ghost"
                onClick={() => setShowProjectDialog(false)}
                disabled={isCreatingProject}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreatePipelineProject}
                disabled={isCreatingProject || !projectForm.path || !projectForm.name}
                className="gap-2"
              >
                {isCreatingProject ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                {isCreatingProject ? 'Creating...' : 'Create & Plan'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
