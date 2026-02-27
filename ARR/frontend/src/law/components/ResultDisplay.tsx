import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { FileText, Handshake, SearchX, Globe2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { LawSearchResponse } from '../lib/types';
import { LawArticleCard } from './LawArticleCard';
import { StatsPanel } from './StatsPanel';

interface ResultDisplayProps {
  response: LawSearchResponse;
}

export function ResultDisplay({ response }: ResultDisplayProps) {
  const { results, stats, domain_name, response_time, domains_queried, a2a_domains } = response;

  const hasA2A = stats?.a2a_collaboration_triggered && a2a_domains && a2a_domains.length > 0;
  const [selfResults, a2aResults] = useMemo(
    () => [results.filter((r) => !r.via_a2a), results.filter((r) => r.via_a2a)],
    [results]
  );

  // No results
  if (results.length === 0) {
    return (
      <div className="space-y-4">
        <StatsPanel
          stats={stats}
          responseTime={response_time}
          domainName={domain_name}
          domainsQueried={domains_queried}
          a2aDomains={a2a_domains}
        />
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 py-12">
          <SearchX className="size-10 text-slate-300" />
          <h3 className="mt-3 text-base font-semibold text-slate-700">검색 결과가 없습니다</h3>
          <p className="mt-1 text-sm text-slate-500">다른 검색어를 시도해 보세요.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Stats */}
      <StatsPanel
        stats={stats}
        responseTime={response_time}
        domainName={domain_name}
        domainsQueried={domains_queried}
        a2aDomains={a2a_domains}
      />

      {hasA2A ? (
        <>
          {/* Self domain results */}
          {selfResults.length > 0 && (
            <Section
              icon={Globe2}
              title="자체 도메인 결과"
              count={selfResults.length}
              color="indigo"
              subtitle={domain_name}
            >
              <AnimatePresence mode="popLayout">
                {selfResults.map((article, i) => (
                  <motion.div
                    key={article.hang_id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2, delay: i * 0.03 }}
                  >
                    <LawArticleCard article={article} index={i + 1} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </Section>
          )}

          {/* A2A results */}
          {a2aResults.length > 0 && (
            <Section
              icon={Handshake}
              title="A2A 협업 결과"
              count={a2aResults.length}
              color="violet"
              subtitle={`${a2a_domains?.length || 0}개 도메인 병렬 협업`}
            >
              <AnimatePresence mode="popLayout">
                {a2aResults.map((article, i) => (
                  <motion.div
                    key={article.hang_id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2, delay: i * 0.03 }}
                  >
                    <LawArticleCard article={article} index={selfResults.length + i + 1} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </Section>
          )}
        </>
      ) : (
        /* Standard results */
        <Section
          icon={FileText}
          title="검색 결과"
          count={results.length}
          color="slate"
          subtitle={domain_name}
        >
          <AnimatePresence mode="popLayout">
            {results.map((article, i) => (
              <motion.div
                key={article.hang_id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, delay: i * 0.03 }}
              >
                <LawArticleCard article={article} index={i + 1} />
              </motion.div>
            ))}
          </AnimatePresence>
        </Section>
      )}
    </div>
  );
}

/* Section wrapper */
function Section({
  icon: Icon,
  title,
  count,
  color,
  subtitle,
  children,
}: {
  icon: React.ElementType;
  title: string;
  count: number;
  color: 'indigo' | 'violet' | 'slate';
  subtitle?: string;
  children: React.ReactNode;
}) {
  const palette = {
    indigo: { line: 'from-indigo-300', badge: 'bg-indigo-100 text-indigo-700', icon: 'text-indigo-500' },
    violet: { line: 'from-violet-300', badge: 'bg-violet-100 text-violet-700', icon: 'text-violet-500' },
    slate:  { line: 'from-slate-300',  badge: 'bg-slate-100 text-slate-700',   icon: 'text-slate-500' },
  }[color];

  return (
    <div className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div className={cn('h-px flex-1 bg-gradient-to-r to-transparent', palette.line)} />
        <div className="flex items-center gap-2">
          <Icon className={cn('size-4', palette.icon)} />
          <span className="text-sm font-semibold text-slate-700">{title}</span>
          <span className={cn('rounded-md px-2 py-0.5 text-[11px] font-bold', palette.badge)}>
            {count}
          </span>
        </div>
        <div className={cn('h-px flex-1 bg-gradient-to-l to-transparent', palette.line)} />
      </div>

      {subtitle && (
        <p className="text-center text-xs text-slate-500">{subtitle}</p>
      )}

      {/* Cards */}
      <div className="space-y-2.5">{children}</div>
    </div>
  );
}
