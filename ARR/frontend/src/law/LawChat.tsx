/**
 * 법규 AI 채팅 메인 컴포넌트 — Modern redesign
 */

import React, { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Scale,
  Wifi,
  WifiOff,
  Radio,
  RotateCcw,
  StopCircle,
  Cpu,
  Link2,
  TreePine,
  Globe2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { LawAPIProvider, useLawAPI } from './contexts/LawAPIContext';
import { useLawChat } from './hooks/use-law-chat';
import { useLawSearchStream } from './hooks/use-law-search-stream';
import { QueryInput } from './components/QueryInput';
import { ResultDisplay } from './components/ResultDisplay';
import {
  SearchProgressIndicator,
  SearchCompleteHeader,
  SearchErrorIndicator,
} from './components/SearchProgress';

function LawChatInner() {
  const navigate = useNavigate();
  const { domains, domainsLoading, selectedDomainId, setSelectedDomainId, isConnected } =
    useLawAPI();
  const { messages, isLoading, search, clearMessages, addMessage } = useLawChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { progress, isSearching, startSearch, stopSearch, resetProgress } =
    useLawSearchStream('http://127.0.0.1:8000');

  const [streamingMode, setStreamingMode] = useState(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (progress?.status === 'complete' && progress.results) {
      addMessage({
        role: 'assistant',
        content: `검색 완료 (${progress.response_time ?? 0}ms)`,
        search_response: {
          results: progress.results,
          total_count: progress.result_count || progress.results.length,
          query: '',
          response_time: progress.response_time || 0,
          domain_id: progress.domain_id,
          domain_name: progress.domain_name,
        },
      });
      resetProgress();
    }
  }, [progress, addMessage, resetProgress]);

  const handleSearch = (query: string) => {
    if (streamingMode) {
      addMessage({ role: 'user', content: query });
      resetProgress();
      startSearch(query, 10);
    } else {
      search(query, 10);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      {/* ── Header ── */}
      <header className="relative z-10 shrink-0 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
          {/* Left: back + title */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="flex size-9 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
              aria-label="뒤로 가기"
            >
              <ArrowLeft className="size-4" />
            </button>
            <div className="flex items-center gap-2.5">
              <div className="flex size-9 items-center justify-center rounded-xl bg-indigo-600 text-white">
                <Scale className="size-4" />
              </div>
              <div>
                <h1 className="text-base font-bold text-slate-900">법규 검색 AI</h1>
                <p className="text-[11px] text-slate-500">
                  18개 법률 &middot; 16,081 노드 &middot; 7-stage 하이브리드 검색
                </p>
              </div>
            </div>
          </div>

          {/* Right: controls */}
          <div className="flex items-center gap-2">
            {/* Connection status */}
            <div
              role="status"
              aria-live="polite"
              className={cn(
                'flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium',
                isConnected
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-red-50 text-red-700'
              )}
            >
              {isConnected ? <Wifi className="size-3" /> : <WifiOff className="size-3" />}
              {isConnected ? '연결됨' : '연결 끊김'}
            </div>

            {/* Streaming toggle */}
            <button
              onClick={() => setStreamingMode(prev => !prev)}
              className={cn(
                'flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-colors',
                streamingMode
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
              )}
            >
              <Radio className={cn('size-3', streamingMode && 'animate-pulse')} />
              실시간
            </button>

            {/* Domain selector */}
            {!domainsLoading && domains.length > 0 && (
              <select
                value={selectedDomainId || ''}
                onChange={(e) => setSelectedDomainId(e.target.value || null)}
                aria-label="검색 도메인 선택"
                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[11px] font-medium text-slate-600 outline-none focus:ring-2 focus:ring-indigo-200"
              >
                <option value="">전체 도메인</option>
                {domains.map((d) => (
                  <option key={d.domain_id} value={d.domain_id}>
                    {d.domain_name} ({d.node_count})
                  </option>
                ))}
              </select>
            )}

            {/* Stop button */}
            {streamingMode && isSearching && (
              <button
                onClick={stopSearch}
                className="flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-[11px] font-semibold text-red-600 hover:bg-red-100"
              >
                <StopCircle className="size-3" />
                중단
              </button>
            )}

            {/* Clear button */}
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="flex items-center gap-1 rounded-lg bg-slate-100 px-2.5 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-slate-200"
              >
                <RotateCcw className="size-3" />
                초기화
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-5 py-6">
          {/* Welcome */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-8"
            >
              <div className="overflow-hidden rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-violet-50">
                <div className="px-6 py-8">
                  <h2 className="text-xl font-bold text-slate-900">
                    건축 법규 AI 검색 시스템
                  </h2>
                  <p className="mt-2 text-sm text-slate-600">
                    Multi-Agent RAG + Legal Knowledge Graph로 법률 조항을 검색합니다.
                  </p>

                  <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[
                      { icon: Cpu, label: '벡터 검색', desc: 'OpenAI 3072-dim 임베딩', color: 'bg-emerald-500' },
                      { icon: Link2, label: '관계 검색', desc: '법률 구조 관계 기반', color: 'bg-violet-500' },
                      { icon: TreePine, label: '그래프 확장', desc: 'RNE 연관 조항 탐색', color: 'bg-amber-500' },
                      { icon: Globe2, label: '도메인 협업', desc: 'A2A 병렬 검색', color: 'bg-pink-500' },
                    ].map(({ icon: Icon, label, desc, color }) => (
                      <div key={label} className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
                        <div className={cn('mb-2.5 flex size-8 items-center justify-center rounded-lg text-white', color)}>
                          <Icon className="size-4" />
                        </div>
                        <p className="text-sm font-semibold text-slate-800">{label}</p>
                        <p className="mt-0.5 text-[11px] text-slate-500">{desc}</p>
                      </div>
                    ))}
                  </div>

                  {streamingMode && (
                    <div className="mt-4 flex items-center gap-2 rounded-lg bg-indigo-100/60 px-4 py-2">
                      <Radio className="size-3.5 animate-pulse text-indigo-500" />
                      <span className="text-xs font-medium text-indigo-700">
                        실시간 진행상황 모드 활성화
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* Search input */}
          <div className="mb-6">
            <QueryInput onSearch={handleSearch} isLoading={isLoading || isSearching} />
          </div>

          {/* Messages */}
          <div className="space-y-4 pb-8">
            <AnimatePresence mode="popLayout">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                >
                  {/* User message */}
                  {message.role === 'user' && (
                    <div className="flex justify-end">
                      <div className="rounded-2xl rounded-br-md bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-md shadow-indigo-200/50">
                        {message.content}
                      </div>
                    </div>
                  )}

                  {/* Assistant message */}
                  {message.role === 'assistant' && (
                    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                      {/* Loading (non-streaming) */}
                      {!streamingMode && message.loading && (
                        <div className="flex items-center gap-3 text-slate-500">
                          <div className="size-5 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
                          <span className="text-sm">{message.content}</span>
                        </div>
                      )}

                      {/* Error */}
                      {message.error && !message.loading && (
                        <SearchErrorIndicator message={message.error} />
                      )}

                      {/* Results */}
                      {message.search_response && !message.loading && !message.error && (
                        <div className="space-y-4">
                          {!streamingMode && (
                            <SearchCompleteHeader
                              resultCount={message.search_response.total_count || message.search_response.results.length}
                              responseTime={message.search_response.response_time || 0}
                              domainName={message.search_response.domain_name}
                            />
                          )}
                          <ResultDisplay response={message.search_response} />
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Streaming progress */}
            {streamingMode && isSearching && progress && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                {progress.status !== 'complete' && progress.status !== 'error' && (
                  <SearchProgressIndicator progress={progress} />
                )}
                {progress.status === 'error' && (
                  <SearchErrorIndicator message={progress.message || '알 수 없는 오류'} />
                )}
                {progress.status === 'complete' && (
                  <SearchCompleteHeader
                    resultCount={progress.result_count || 0}
                    responseTime={progress.response_time || 0}
                    domainName={progress.domain_name}
                  />
                )}
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Backend disconnected */}
          {!isConnected && messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/80 p-6"
            >
              <div className="flex items-start gap-3">
                <WifiOff className="mt-0.5 size-5 text-amber-500" />
                <div>
                  <h3 className="text-sm font-semibold text-amber-800">
                    백엔드 서버에 연결할 수 없습니다
                  </h3>
                  <p className="mt-1 text-xs text-amber-700">
                    Django 백엔드 서버가 실행 중인지 확인하세요.
                  </p>
                  <div className="mt-3 overflow-hidden rounded-lg bg-amber-100/60 px-3 py-2">
                    <code className="text-[11px] text-amber-800">
                      cd ARR/backend && python manage.py runserver 8000
                    </code>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function LawChat() {
  return (
    <LawAPIProvider>
      <LawChatInner />
    </LawAPIProvider>
  );
}
