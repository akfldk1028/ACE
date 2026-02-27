import React from 'react';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Cpu,
  Link2,
  TreePine,
  Clock,
  Globe2,
  Handshake,
} from 'lucide-react';
import type { SearchStats } from '../lib/types';

interface StatsPanelProps {
  stats?: SearchStats;
  responseTime?: number;
  domainName?: string;
  domainsQueried?: string[];
  a2aDomains?: string[];
}

interface MetricProps {
  icon: React.ElementType;
  value: number;
  label: string;
  color: string;
  sub?: string;
}

function Metric({ icon: Icon, value, label, color, sub }: MetricProps) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-slate-100 bg-white px-3 py-2.5 shadow-sm">
      <div className={cn('flex size-8 items-center justify-center rounded-lg', color)}>
        <Icon className="size-3.5 text-white" />
      </div>
      <div className="min-w-0">
        <p className="text-lg font-bold leading-tight tabular-nums text-slate-800">{value}</p>
        <p className="text-[10px] font-medium text-slate-500 truncate">{label}</p>
        {sub && <p className="text-[9px] text-slate-400 truncate">{sub}</p>}
      </div>
    </div>
  );
}

export function StatsPanel({
  stats,
  responseTime,
  domainName,
  domainsQueried,
  a2aDomains,
}: StatsPanelProps) {
  const hasA2A = stats?.a2a_collaboration_triggered && a2aDomains && a2aDomains.length > 0;
  const total = stats?.total || 0;

  return (
    <div className="space-y-3">
      {/* Metrics row */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {responseTime != null && (
          <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-3 py-1.5">
            <Clock className="size-3.5 text-slate-400" />
            <span className="text-xs font-semibold tabular-nums text-slate-600">{responseTime}ms</span>
          </div>
        )}
        {domainName && (
          <div className="flex items-center gap-1.5 rounded-lg bg-indigo-50 px-3 py-1.5">
            <Globe2 className="size-3.5 text-indigo-500" />
            <span className="text-xs font-medium text-indigo-700 truncate max-w-[200px]">
              {domainName}
            </span>
          </div>
        )}
        {hasA2A && (
          <div className="flex items-center gap-1.5 rounded-lg bg-violet-50 px-3 py-1.5">
            <Handshake className="size-3.5 text-violet-500" />
            <span className="text-xs font-semibold text-violet-700">
              A2A {a2aDomains.length}개 도메인
            </span>
          </div>
        )}
      </div>

      {/* Stats grid */}
      {stats && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          <Metric icon={BarChart3} value={total} label="총 조항" color="bg-slate-600" />
          <Metric
            icon={Cpu}
            value={stats.vector_count || 0}
            label="벡터 검색"
            color="bg-emerald-500"
            sub="3072-dim"
          />
          <Metric
            icon={Link2}
            value={stats.relationship_count || 0}
            label="관계 검색"
            color="bg-violet-500"
            sub="CONTAINS"
          />
          <Metric
            icon={TreePine}
            value={stats.graph_expansion_count || 0}
            label="그래프 확장"
            color="bg-amber-500"
            sub="RNE"
          />
          <Metric
            icon={Globe2}
            value={stats.my_domain_count || 0}
            label="자체 도메인"
            color="bg-cyan-500"
          />
          <Metric
            icon={Handshake}
            value={stats.neighbor_count || 0}
            label="협업 도메인"
            color="bg-pink-500"
            sub="A2A"
          />
        </div>
      )}

      {/* Method distribution bar */}
      {total > 0 && stats && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-medium text-slate-400">검색 방법 분포</p>
          <div className="flex h-1.5 overflow-hidden rounded-full bg-slate-100">
            {stats.vector_count > 0 && (
              <div
                className="bg-emerald-500 transition-all duration-500"
                style={{ width: `${(stats.vector_count / total) * 100}%` }}
                title={`벡터: ${stats.vector_count}`}
              />
            )}
            {stats.relationship_count > 0 && (
              <div
                className="bg-violet-500 transition-all duration-500"
                style={{ width: `${(stats.relationship_count / total) * 100}%` }}
                title={`관계: ${stats.relationship_count}`}
              />
            )}
            {(stats.graph_expansion_count || 0) > 0 && (
              <div
                className="bg-amber-500 transition-all duration-500"
                style={{ width: `${((stats.graph_expansion_count || 0) / total) * 100}%` }}
                title={`확장: ${stats.graph_expansion_count}`}
              />
            )}
          </div>
          <div className="flex gap-3 text-[10px] text-slate-500">
            {stats.vector_count > 0 && (
              <span className="flex items-center gap-1">
                <span className="inline-block size-1.5 rounded-full bg-emerald-500" />
                벡터 {Math.round((stats.vector_count / total) * 100)}%
              </span>
            )}
            {stats.relationship_count > 0 && (
              <span className="flex items-center gap-1">
                <span className="inline-block size-1.5 rounded-full bg-violet-500" />
                관계 {Math.round((stats.relationship_count / total) * 100)}%
              </span>
            )}
            {(stats.graph_expansion_count || 0) > 0 && (
              <span className="flex items-center gap-1">
                <span className="inline-block size-1.5 rounded-full bg-amber-500" />
                확장 {Math.round(((stats.graph_expansion_count || 0) / total) * 100)}%
              </span>
            )}
          </div>
        </div>
      )}

      {/* A2A domains */}
      {hasA2A && (
        <div className="rounded-xl border border-violet-100 bg-violet-50/50 p-3">
          <div className="mb-2 flex items-center gap-2">
            <Handshake className="size-3.5 text-violet-500" />
            <span className="text-xs font-semibold text-violet-700">A2A 협업 도메인</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {a2aDomains.map((d) => (
              <span
                key={d}
                className="rounded-md border border-violet-200 bg-white px-2 py-1 text-[11px] font-medium text-violet-700"
              >
                {d}
              </span>
            ))}
          </div>
          {stats?.a2a_results_count != null && stats.a2a_results_count > 0 && (
            <p className="mt-2 text-[10px] text-violet-600">
              병렬 협업으로 {stats.a2a_results_count}개 추가 조항 발견
            </p>
          )}
        </div>
      )}

      {/* Queried domains */}
      {domainsQueried && domainsQueried.length > 1 && !hasA2A && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] font-medium text-slate-400">조회 도메인:</span>
          {domainsQueried.map((d) => (
            <span
              key={d}
              className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600"
            >
              {d}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
