import React from 'react';
import { cn } from '@/lib/utils';
import {
  Target,
  SearchCode,
  Link2,
  TreePine,
  Sparkles,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import type { SearchProgress, SearchStage } from '../hooks/use-law-search-stream';

interface SearchProgressProps {
  progress: SearchProgress;
}

const STAGES: { key: SearchStage; label: string; icon: React.ElementType; threshold: number }[] = [
  { key: 'exact_match', label: '정확 일치', icon: Target, threshold: 0.2 },
  { key: 'vector_search', label: '벡터 검색', icon: SearchCode, threshold: 0.4 },
  { key: 'relationship_search', label: '관계 검색', icon: Link2, threshold: 0.6 },
  { key: 'rne_expansion', label: '그래프 확장', icon: TreePine, threshold: 0.8 },
  { key: 'enrichment', label: '결과 강화', icon: Sparkles, threshold: 0.95 },
];

export function SearchProgressIndicator({ progress }: SearchProgressProps) {
  const currentProgress = progress.progress || 0;

  return (
    <div className="space-y-5">
      {/* Agent info */}
      <div className="flex items-center gap-3 rounded-xl border border-indigo-100 bg-indigo-50/50 px-4 py-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-indigo-600 text-white">
          <SearchCode className="size-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-800 truncate">
            {progress.agent || '에이전트 준비 중...'}
          </p>
          {progress.node_count != null && (
            <p className="text-xs text-slate-500">
              {progress.node_count.toLocaleString()} 노드 탐색 중
            </p>
          )}
        </div>
        <Loader2 className="size-5 animate-spin text-indigo-500" />
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-slate-600">
            {progress.stage_name || '검색 준비 중...'}
          </span>
          <span className="tabular-nums text-slate-400">
            {Math.round(currentProgress * 100)}%
          </span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={Math.round(currentProgress * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="검색 진행률"
          className="h-1.5 overflow-hidden rounded-full bg-slate-100"
        >
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500 ease-out"
            style={{ width: `${currentProgress * 100}%` }}
          />
        </div>
      </div>

      {/* Stage steps */}
      <div className="flex items-center justify-between gap-1">
        {STAGES.map((stage, i) => {
          const isDone = currentProgress >= stage.threshold;
          const isActive =
            progress.stage === stage.key ||
            (i > 0 &&
              currentProgress >= STAGES[i - 1].threshold &&
              currentProgress < stage.threshold);
          const Icon = stage.icon;

          return (
            <React.Fragment key={stage.key}>
              {i > 0 && (
                <div
                  className={cn(
                    'h-px flex-1 transition-colors duration-300',
                    isDone ? 'bg-indigo-400' : 'bg-slate-200'
                  )}
                />
              )}
              <div
                className={cn(
                  'flex flex-col items-center gap-1.5 transition-all duration-300',
                  isDone
                    ? 'text-indigo-600'
                    : isActive
                      ? 'text-indigo-500'
                      : 'text-slate-300'
                )}
              >
                <div
                  className={cn(
                    'flex size-8 items-center justify-center rounded-full border-2 transition-all duration-300',
                    isDone
                      ? 'border-indigo-500 bg-indigo-50'
                      : isActive
                        ? 'border-indigo-400 bg-white animate-pulse'
                        : 'border-slate-200 bg-white'
                  )}
                >
                  {isDone ? (
                    <CheckCircle2 className="size-4 text-indigo-600" />
                  ) : (
                    <Icon className="size-3.5" />
                  )}
                </div>
                <span className="text-[10px] font-medium whitespace-nowrap">{stage.label}</span>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

export function SearchErrorIndicator({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50/80 p-4">
      <XCircle className="mt-0.5 size-5 shrink-0 text-red-500" />
      <div>
        <p className="text-sm font-semibold text-red-800">검색 실패</p>
        <p className="mt-1 text-xs text-red-600">{message}</p>
      </div>
    </div>
  );
}

export function SearchCompleteHeader({
  resultCount,
  responseTime,
  domainName,
}: {
  resultCount: number;
  responseTime: number;
  domainName?: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50/80 p-4">
      <div className="flex items-center gap-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
          <CheckCircle2 className="size-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-emerald-800">검색 완료</p>
          <p className="text-xs text-emerald-600">
            {resultCount}개 결과{domainName && ` \u00B7 ${domainName}`}
          </p>
        </div>
      </div>
      <div className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold tabular-nums text-white">
        {responseTime}ms
      </div>
    </div>
  );
}
