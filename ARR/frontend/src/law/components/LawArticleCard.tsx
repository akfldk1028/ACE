import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  FileText,
  ChevronDown,
  Cpu,
  Link2,
  TreePine,
  Target,
  Sparkles,
  Handshake,
  ExternalLink,
} from 'lucide-react';
import type { LawArticle } from '../lib/types';

interface LawArticleCardProps {
  article: LawArticle;
  index: number;
}

/** Law type → accent color map */
const LAW_TYPE_STYLES: Record<string, { border: string; badge: string; bg: string; text: string }> = {
  '법률':     { border: 'border-l-blue-500',   badge: 'bg-blue-50 text-blue-700 ring-blue-200',     bg: 'bg-blue-500',   text: 'text-blue-700' },
  '시행령':   { border: 'border-l-violet-500',  badge: 'bg-violet-50 text-violet-700 ring-violet-200', bg: 'bg-violet-500', text: 'text-violet-700' },
  '시행규칙': { border: 'border-l-amber-500',   badge: 'bg-amber-50 text-amber-700 ring-amber-200',   bg: 'bg-amber-500',  text: 'text-amber-700' },
};

const DEFAULT_STYLE = { border: 'border-l-slate-400', badge: 'bg-slate-50 text-slate-700 ring-slate-200', bg: 'bg-slate-400', text: 'text-slate-700' };

/** Search stage → icon + style */
const STAGE_MAP: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  vector_search:       { icon: Cpu,      color: 'bg-emerald-50 text-emerald-700', label: '벡터' },
  vector:              { icon: Cpu,      color: 'bg-emerald-50 text-emerald-700', label: '벡터' },
  relationship_search: { icon: Link2,    color: 'bg-violet-50 text-violet-700',   label: '관계' },
  relationship:        { icon: Link2,    color: 'bg-violet-50 text-violet-700',   label: '관계' },
  graph_expansion:     { icon: TreePine, color: 'bg-amber-50 text-amber-700',     label: '확장' },
  rne_expansion:       { icon: TreePine, color: 'bg-amber-50 text-amber-700',     label: '확장' },
  exact_match:         { icon: Target,   color: 'bg-blue-50 text-blue-700',       label: '정확' },
  fulltext_keyword:    { icon: Target,   color: 'bg-blue-50 text-blue-700',       label: '키워드' },
  enrichment:          { icon: Sparkles, color: 'bg-pink-50 text-pink-700',       label: '강화' },
};

/** Similarity ring color */
function getSimilarityColor(s: number) {
  if (s >= 0.8) return { ring: 'text-emerald-500', bg: 'bg-emerald-50', text: 'text-emerald-700' };
  if (s >= 0.6) return { ring: 'text-amber-500',   bg: 'bg-amber-50',   text: 'text-amber-700' };
  return               { ring: 'text-slate-400',    bg: 'bg-slate-50',   text: 'text-slate-600' };
}

export const LawArticleCard = React.memo(function LawArticleCard({ article, index }: LawArticleCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isA2A = article.via_a2a === true;
  const lawType = article.law_type || '';
  const style = LAW_TYPE_STYLES[lawType] || DEFAULT_STYLE;
  const sim = getSimilarityColor(article.similarity);
  const percent = Math.round((article.similarity || 0) * 100);

  // Parse law name + article number from hang_id
  const lawName = article.law_name || article.hang_id?.split('_')[0] || '';
  const articleNum = article.article || '';

  // Truncate content for collapsed view
  const contentPreview = article.content.length > 120
    ? article.content.slice(0, 120) + '...'
    : article.content;

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-xl border-l-[3px] bg-white transition-all duration-200',
        style.border,
        isA2A
          ? 'border border-violet-200 shadow-md shadow-violet-50'
          : 'border border-slate-200 shadow-sm hover:shadow-md',
      )}
    >
      {/* A2A banner */}
      {isA2A && (
        <div className="flex items-center gap-2 border-b border-violet-100 bg-gradient-to-r from-violet-50 to-pink-50 px-4 py-1.5">
          <Handshake className="size-3 text-violet-500" />
          <span className="text-[10px] font-semibold text-violet-600">A2A 협업</span>
          {article.source_domain && (
            <span className="rounded bg-white px-1.5 py-0.5 text-[10px] font-medium text-violet-700 ring-1 ring-violet-200">
              {article.source_domain}
            </span>
          )}
        </div>
      )}

      <div className="px-4 py-3">
        {/* Header row */}
        <div className="flex items-start gap-3">
          {/* Index number */}
          <div
            className={cn(
              'flex size-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white',
              isA2A ? 'bg-gradient-to-br from-violet-500 to-pink-500' : style.bg
            )}
          >
            {index}
          </div>

          {/* Title area */}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              {/* Law name */}
              {lawName && (
                <span className={cn('rounded-md px-2 py-0.5 text-[11px] font-semibold ring-1', style.badge)}>
                  {lawName}
                </span>
              )}
              {/* Law type */}
              {lawType && (
                <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                  {lawType}
                </span>
              )}
              {/* Article number */}
              {articleNum && (
                <span className="text-xs font-medium text-slate-700">{articleNum}</span>
              )}
            </div>

            {/* hang_id (subtle) */}
            <p className="mt-1 flex items-center gap-1 text-[10px] text-slate-400">
              <FileText className="size-2.5" />
              {article.hang_id}
              {article.unit_path && (
                <span className="ml-1 truncate max-w-[200px]">{article.unit_path}</span>
              )}
            </p>
          </div>

          {/* Similarity ring */}
          <div className="flex shrink-0 flex-col items-center gap-0.5">
            <div className={cn('relative flex size-10 items-center justify-center rounded-full', sim.bg)} aria-label={`유사도 ${percent}%`}>
              <svg className="absolute inset-0 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.9155" fill="none" stroke="currentColor"
                  className="text-slate-100" strokeWidth="2.5" />
                <circle cx="18" cy="18" r="15.9155" fill="none" stroke="currentColor"
                  className={sim.ring} strokeWidth="2.5"
                  strokeDasharray={`${percent} ${100 - percent}`}
                  strokeLinecap="round" />
              </svg>
              <span className={cn('relative text-[11px] font-bold tabular-nums', sim.text)}>
                {percent}
              </span>
            </div>
            <span className="text-[8px] font-medium text-slate-400">유사도</span>
          </div>
        </div>

        {/* Content */}
        <div className="mt-3">
          <p className="text-[13px] leading-relaxed text-slate-700">
            {expanded ? article.content : contentPreview}
          </p>
          {article.content.length > 120 && (
            <button
              onClick={() => setExpanded(prev => !prev)}
              aria-expanded={expanded}
              className="mt-1.5 flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-700"
            >
              <ChevronDown
                className={cn('size-3.5 transition-transform', expanded && 'rotate-180')}
              />
              {expanded ? '접기' : '더보기'}
            </button>
          )}
        </div>

        {/* Stage tags + A2A refined query */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {article.stages.map((stage, i) => {
            const info = STAGE_MAP[stage] || { icon: ExternalLink, color: 'bg-slate-50 text-slate-600', label: stage };
            const SIcon = info.icon;
            return (
              <span
                key={`${stage}-${i}`}
                className={cn('inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-medium', info.color)}
              >
                <SIcon className="size-2.5" />
                {info.label}
              </span>
            );
          })}
        </div>

        {isA2A && article.a2a_refined_query && (
          <p className="mt-2 text-[10px] text-violet-500">
            <span className="font-semibold">정제된 쿼리:</span> {article.a2a_refined_query}
          </p>
        )}
      </div>
    </div>
  );
});
