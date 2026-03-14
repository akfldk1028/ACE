/**
 * useMapLawSearch — 지적도 클릭/호버 → 토지 규제 분석 훅.
 *
 * 3D 지도(Vworld WebGL)와 토지 분석(/land/analyze/)을 연결하는 중간 계층.
 *
 * 클릭 흐름 (quick 모드):
 *   Cesium LEFT_CLICK → (lng, lat)
 *   → reverse()    — 좌표 → PNU + 주소 + geometry
 *   → highlightParcel(geometry)   — 진한 파랑 하이라이트
 *   → analyze(pnu)  — PNU → 건폐율/용적률/41규제
 *   → addMessage(user: 주소) + addMessage(assistant: land_analysis)
 *
 * 클릭 흐름 (agent 모드):
 *   Cesium LEFT_CLICK → (lng, lat)
 *   → reverse geocode (동일)
 *   → SSE /land/agent-analyze/stream → quick_done(규제 즉시표시) → agent 메시지 릴레이
 *
 * 호버 흐름 (300ms 디바운스):
 *   Cesium MOUSE_MOVE → (lng, lat)
 *   → reverse()    — 좌표 → PNU + geometry
 *   → highlightHover(geometry)    — 연한 인디고 하이라이트
 *   → PNU 캐시로 동일 필지 재호출 방지
 *
 * highlightRef 패턴:
 *   handleMapClick(useCallback) ↔ useVworld3D(onClick) 순환 참조를
 *   ref 동기화로 해결.
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { useVworld3D } from '../../land/hooks/use-vworld-3d';
import { reverse, analyze } from '../../land/lib/land-api-client';
import { useAgentAnalyze } from '../../land/hooks/use-agent-analyze';
import type { ChatMessage } from '../lib/types';
import type { AgentAnalysisEvent, AgentMessage, LandAnalysisResult } from '../../land/lib/types';

export type AnalysisMode = 'quick' | 'agent';

interface UseMapLawSearchOptions {
  /** 3D 맵 컨테이너 ref */
  target: React.RefObject<HTMLDivElement | null>;
  /** 검색/분석 중이면 클릭 무시 */
  busy: boolean;
  /** useLawChat.addMessage — 채팅에 메시지 추가 */
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
}

interface UseMapLawSearchReturn {
  /** 3D 맵 초기화 완료 */
  mapReady: boolean;
  /** 3D 맵 로딩 중 */
  mapLoading: boolean;
  /** 3D 맵 에러 메시지 */
  mapError: string | null;
  /** 필지 클릭 → 분석 진행 중 */
  mapClickLoading: boolean;
  /** 분석 모드 ('quick' | 'agent') */
  analysisMode: AnalysisMode;
  /** 모드 토글 */
  setAnalysisMode: (mode: AnalysisMode) => void;
  /** 에이전트 분석 상태 (agent 모드용) */
  agent: {
    event: AgentAnalysisEvent | null;
    quickResult: LandAnalysisResult | null;
    messages: AgentMessage[];
    report: string | null;
    runSummary: { duration: number; total_tokens: number; turn_count: number } | null;
    progress: number;
    isRunning: boolean;
    stop: () => void;
  };
}

/** 호버 디바운스 (ms) — API 호출 빈도 제한 */
const HOVER_DEBOUNCE_MS = 300;

/**
 * 지적도 클릭 시 토지 규제 분석 + 호버 시 필지 하이라이트.
 */
export function useMapLawSearch({
  target,
  busy,
  addMessage,
}: UseMapLawSearchOptions): UseMapLawSearchReturn {
  const [mapClickLoading, setMapClickLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('agent');

  // ── Agent analysis SSE hook ──
  const {
    event: agentEvent,
    quickResult,
    agentMessages,
    report,
    runSummary,
    progress: agentProgress,
    isRunning: agentRunning,
    startAnalysis,
    stopAnalysis,
  } = useAgentAnalyze('');

  // ── Refs (순환 참조 방지 + 디바운스 상태) ──
  const highlightRef = useRef<(geojson: object) => void>(() => {});
  const highlightHoverRef = useRef<(geojson: object) => void>(() => {});
  const clearHoverRef = useRef<() => void>(() => {});
  const analyzingRef = useRef(false);
  const hoverTimerRef = useRef<number | null>(null);
  const lastHoverPnuRef = useRef<string | null>(null);
  const clickedPnuRef = useRef<string | null>(null);
  const analysisModeRef = useRef(analysisMode);

  // Keep ref in sync
  useEffect(() => { analysisModeRef.current = analysisMode; }, [analysisMode]);

  // ── Agent quick_done → addMessage (한 번만) ──
  // quickResult의 object identity가 바뀔 때만 addMessage 호출
  const lastQuickResultRef = useRef<object | null>(null);
  useEffect(() => {
    if (quickResult && quickResult !== lastQuickResultRef.current) {
      lastQuickResultRef.current = quickResult;
      const pnu = quickResult.pnu;
      const addr = (typeof pnu === 'object' && pnu?.address) ? pnu.address : '';
      addMessage({
        role: 'assistant',
        content: addr || '토지 규제 분석 완료',
        land_analysis: quickResult,
      });
    }
  }, [quickResult, addMessage]);

  /** Cesium LEFT_CLICK → reverse geocode → land analyze */
  const handleMapClick = useCallback(async (lng: number, lat: number) => {
    if (busy || analyzingRef.current) return;
    analyzingRef.current = true;
    setMapClickLoading(true);

    // 호버 하이라이트 제거 (클릭 하이라이트로 대체)
    clearHoverRef.current();

    try {
      const rev = await reverse(lng, lat);
      if (!rev.success || !rev.pnu) {
        addMessage({
          role: 'assistant',
          content: '이 위치의 필지 정보를 찾을 수 없습니다.',
          error: rev.error || '해당 좌표에 필지가 없습니다',
        });
        return;
      }

      // 필지 폴리곤 하이라이트 (진한 파랑)
      if (rev.geometry) highlightRef.current(rev.geometry);
      clickedPnuRef.current = rev.pnu;

      const addr = rev.address || rev.pnu;

      // 주소를 사용자 메시지로 표시
      addMessage({ role: 'user', content: addr });

      if (analysisModeRef.current === 'agent') {
        // Agent mode: SSE 스트리밍 (quick + 에이전트 협업)
        startAnalysis(rev.pnu, rev.address || undefined);
        // mapClickLoading stays true until agent finishes or quick_done
      } else {
        // Quick mode: 기존 동기 분석
        const result = await analyze(rev.pnu, 'pnu');
        addMessage({
          role: 'assistant',
          content: addr,
          land_analysis: result,
        });
      }
    } catch (e) {
      addMessage({
        role: 'assistant',
        content: '토지 분석 실패',
        error: e instanceof Error ? e.message : '알 수 없는 오류',
      });
    } finally {
      analyzingRef.current = false;
      setMapClickLoading(false);
    }
  }, [busy, addMessage, startAnalysis]);

  /** Cesium MOUSE_MOVE → 디바운스 → reverse geocode → 호버 하이라이트 */
  const handleHover = useCallback((lng: number, lat: number) => {
    if (hoverTimerRef.current) window.clearTimeout(hoverTimerRef.current);

    hoverTimerRef.current = window.setTimeout(async () => {
      // 분석 중이면 호버 무시
      if (analyzingRef.current) return;

      try {
        const rev = await reverse(lng, lat);
        if (!rev.success || !rev.pnu) {
          clearHoverRef.current();
          lastHoverPnuRef.current = null;
          return;
        }

        // 동일 필지 → 스킵 (API 절약)
        if (rev.pnu === lastHoverPnuRef.current) return;
        // 클릭된 필지 위에 호버 → 스킵 (이미 진한 하이라이트)
        if (rev.pnu === clickedPnuRef.current) return;

        lastHoverPnuRef.current = rev.pnu;
        if (rev.geometry) highlightHoverRef.current(rev.geometry);
      } catch {
        /* 네트워크 오류 — silent */
      }
    }, HOVER_DEBOUNCE_MS);
  }, []);

  const {
    ready: mapReady,
    loading: mapLoading,
    error: mapError,
    highlightParcel,
    highlightHover,
    clearHoverHighlight,
  } = useVworld3D({ target, onClick: handleMapClick, onHover: handleHover });

  // ref 동기화 (useVworld3D 반환 후 결정되므로)
  useEffect(() => { highlightRef.current = highlightParcel; }, [highlightParcel]);
  useEffect(() => { highlightHoverRef.current = highlightHover; }, [highlightHover]);
  useEffect(() => { clearHoverRef.current = clearHoverHighlight; }, [clearHoverHighlight]);

  // 클린업 — 디바운스 타이머 해제
  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) window.clearTimeout(hoverTimerRef.current);
    };
  }, []);

  return {
    mapReady, mapLoading, mapError, mapClickLoading,
    analysisMode, setAnalysisMode,
    agent: {
      event: agentEvent,
      quickResult,
      messages: agentMessages,
      report,
      runSummary,
      progress: agentProgress,
      isRunning: agentRunning,
      stop: stopAnalysis,
    },
  };
}
