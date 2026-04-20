import { useState, useCallback, useRef } from 'react';
import type { SSEEvent, DesignData, GeoJSONFeature } from '../lib/types';

interface ObjectiveInfo {
  name: string;
  goal: string;
}

// Lightweight scatter point: [obj0, obj1, feasible, generation]
export type ScatterPoint = [number, number, boolean, number];

interface OptimizationStreamState {
  status: 'idle' | 'connecting' | 'running' | 'complete' | 'error' | 'cancelled';
  generation: number;
  maxGenerations: number;
  paretoFront: DesignData[];
  best: DesignData | null;
  bestGeojson: GeoJSONFeature | null;
  paretoGeojson: GeoJSONFeature[];
  feasibleCount: number;
  totalDesigns: number;
  error: string | null;
  progress: number; // 0-100
  objectives: ObjectiveInfo[];
  scatterHistory: ScatterPoint[]; // accumulated across generations
}

export function useOptimizationStream() {
  const [state, setState] = useState<OptimizationStreamState>({
    status: 'idle',
    generation: 0,
    maxGenerations: 0,
    paretoFront: [],
    best: null,
    bestGeojson: null,
    paretoGeojson: [],
    feasibleCount: 0,
    totalDesigns: 0,
    error: null,
    progress: 0,
    objectives: [],
    scatterHistory: [],
  });

  const scatterRef = useRef<ScatterPoint[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback((jobId: string) => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Reset scatter history from previous run (fixes stale color bug)
    scatterRef.current = [];

    setState(prev => ({
      ...prev,
      status: 'connecting',
      error: null,
      scatterHistory: [],
      paretoFront: [],
      paretoGeojson: [],
      best: null,
      bestGeojson: null,
      generation: 0,
      progress: 0,
      feasibleCount: 0,
      totalDesigns: 0,
    }));

    const es = new EventSource(`/design/jobs/${jobId}/stream`);
    eventSourceRef.current = es;

    es.addEventListener('started', (e) => {
      const data: SSEEvent = JSON.parse(e.data);
      setState(prev => ({
        ...prev,
        status: 'running',
        maxGenerations: data.max_generations || 0,
        objectives: data.objectives || [],
      }));
    });

    es.addEventListener('generation', (e) => {
      const data: SSEEvent = JSON.parse(e.data);
      const gen = data.generation || 0;
      // Accumulate scatter points across all generations
      if (data.scatter) {
        scatterRef.current = [...scatterRef.current, ...data.scatter];
      }
      setState(prev => {
        const maxGen = data.max_generations || prev.maxGenerations;
        return {
          ...prev,
          status: 'running',
          generation: gen,
          maxGenerations: maxGen,
          paretoFront: data.pareto_front || prev.paretoFront,
          best: data.best || prev.best,
          bestGeojson: data.best_geojson ?? prev.bestGeojson,
          paretoGeojson: data.pareto_geojson ?? prev.paretoGeojson,
          feasibleCount: data.feasible_count || 0,
          totalDesigns: data.total_evaluated || prev.totalDesigns,
          progress: maxGen > 0 ? Math.round((gen / maxGen) * 100) : 0,
          scatterHistory: scatterRef.current,
        };
      });
    });

    es.addEventListener('complete', (e) => {
      const data: SSEEvent = JSON.parse(e.data);
      setState(prev => ({
        ...prev,
        status: 'complete',
        paretoFront: data.pareto_front || prev.paretoFront,
        bestGeojson: data.best_geojson ?? prev.bestGeojson,
        paretoGeojson: data.pareto_geojson ?? prev.paretoGeojson,
        totalDesigns: data.total_designs || 0,
        progress: 100,
      }));
      es.close();
    });

    es.addEventListener('error', (e) => {
      try {
        const data: SSEEvent = JSON.parse((e as MessageEvent).data);
        setState(prev => ({
          ...prev,
          status: 'error',
          error: data.message || 'Unknown error',
        }));
      } catch {
        setState(prev => ({
          ...prev,
          status: 'error',
          error: 'Connection lost',
        }));
      }
      es.close();
    });

    es.addEventListener('cancelled', () => {
      setState(prev => ({ ...prev, status: 'cancelled' }));
      es.close();
    });

    es.onerror = () => {
      // EventSource will auto-reconnect on transient errors
      // Only update state if the connection is truly closed
      if (es.readyState === EventSource.CLOSED) {
        setState(prev => {
          if (prev.status === 'running' || prev.status === 'connecting') {
            return { ...prev, status: 'error', error: 'Connection lost' };
          }
          return prev;
        });
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    disconnect();
    scatterRef.current = [];
    setState({
      status: 'idle',
      generation: 0,
      maxGenerations: 0,
      paretoFront: [],
      best: null,
      bestGeojson: null,
      paretoGeojson: [],
      feasibleCount: 0,
      totalDesigns: 0,
      error: null,
      progress: 0,
      objectives: [],
      scatterHistory: [],
    });
  }, [disconnect]);

  return { ...state, connect, disconnect, reset };
}
