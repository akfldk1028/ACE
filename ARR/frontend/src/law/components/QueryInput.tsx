import React, { useState, KeyboardEvent } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QueryInputProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  initialValue?: string;
}

const EXAMPLE_QUERIES = [
  '개발행위 허가 요건',
  '건폐율 용적률 제한',
  '용도지역 변경',
  '일조권 높이제한',
];

export function QueryInput({
  onSearch,
  isLoading = false,
  placeholder = '법규 내용을 검색하세요...',
  initialValue = '',
}: QueryInputProps) {
  const [query, setQuery] = useState(initialValue);
  const [isFocused, setIsFocused] = useState(false);

  const handleSearch = () => {
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="space-y-3">
      {/* Search bar */}
      <div
        className={cn(
          'relative flex items-center gap-3 rounded-2xl border bg-white/80 backdrop-blur-sm px-5 py-3 transition-all duration-300',
          isFocused
            ? 'border-indigo-400 shadow-lg shadow-indigo-100/50 ring-4 ring-indigo-50'
            : 'border-slate-200 shadow-sm hover:border-slate-300 hover:shadow-md'
        )}
      >
        <Search
          className={cn(
            'size-5 shrink-0 transition-colors duration-200',
            isFocused ? 'text-indigo-500' : 'text-slate-400'
          )}
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={isLoading}
          aria-label="법규 검색어 입력"
          className="flex-1 bg-transparent text-slate-900 placeholder:text-slate-400 outline-none text-[15px] disabled:opacity-50"
        />
        <button
          onClick={handleSearch}
          disabled={!query.trim() || isLoading}
          className={cn(
            'flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all duration-200',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            query.trim() && !isLoading
              ? 'bg-indigo-600 text-white hover:bg-indigo-700 active:scale-[0.97] shadow-md shadow-indigo-200'
              : 'bg-slate-100 text-slate-400'
          )}
        >
          {isLoading ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              <span>검색 중</span>
            </>
          ) : (
            <>
              <Sparkles className="size-4" />
              <span>검색</span>
            </>
          )}
        </button>
      </div>

      {/* Example chips */}
      {!query && (
        <div className="flex items-center gap-2 px-1">
          <span className="text-xs font-medium text-slate-400">추천</span>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => setQuery(q)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition-all hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 active:scale-[0.97]"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
