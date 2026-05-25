import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import type { DesignData, FloorPlanResult } from './lib/types';
import { cancelJob, generateFloorPlan } from './lib/api-client';
import { getRoomPreset } from './lib/room-presets';
import { useDesignJob } from './hooks/use-design-job';
import { useOptimizationStream } from './hooks/use-optimization-stream';
import ControlPanel from './components/ControlPanel';
import ConstraintSummary from './components/ConstraintSummary';
import DatumInfoCard from './components/DatumInfoCard';
import LegalBasisPanel from './components/LegalBasisPanel';
import { SunlightSectionDiagram } from './components/SunlightSectionDiagram';
import GenerationProgress from './components/GenerationProgress';
import ParetoChart from './components/ParetoChart';
import DesignInspector from './components/DesignInspector';
import DesignList from './components/DesignList';
import SiteMapPanel from './components/SiteMapPanel';
import FloorPlanViewer from './components/FloorPlanViewer';

const OBJECTIVE_LABELS: Record<string, string> = {
  floor_area: 'Floor Area (m\u00B2)',
  daylight_score: 'Daylight Score',
  landscaping_pct: 'Open Space (%)',
  setback: 'Setback (m)',
  bcr: 'BCR (%)',
  far: 'FAR (%)',
  height: 'Height (m)',
};

const BUILDING_TYPES = [
  { key: '공동주택', label: '공동주택 (아파트)', floorHeight: 2.8 },
  { key: '근린생활시설', label: '근린생활시설', floorHeight: 3.5 },
  { key: '업무시설', label: '업무시설 (오피스)', floorHeight: 3.8 },
  { key: '판매시설', label: '판매시설 (상가)', floorHeight: 4.0 },
  { key: '숙박시설', label: '숙박시설 (호텔)', floorHeight: 3.0 },
  { key: '문화집회시설', label: '문화 및 집회시설', floorHeight: 4.5 },
  { key: '의료시설', label: '의료시설', floorHeight: 3.6 },
  { key: '교육연구시설', label: '교육연구시설', floorHeight: 3.5 },
  { key: '공장', label: '공장', floorHeight: 5.0 },
  { key: '창고시설', label: '창고시설', floorHeight: 6.0 },
];

const ALGORITHMS = [
  { key: 'all', label: '전체 탐색 (10종 동시)' },
  { key: 'additive', label: '자유형 (Additive)' },
  { key: 'subtractive', label: '감산형 (Subtractive)' },
  { key: 'grid', label: '격자형 (Grid)' },
  { key: 'lshape', label: 'ㄱ자형 (L-shape)' },
  { key: 'ushape', label: 'ㄷ자형 (U-shape)' },
  { key: 'cross', label: '십자형 (Cross)' },
  { key: 'courtyard', label: '중정형 (Courtyard)' },
  { key: 'tower_podium', label: '타워+기단 (Tower+Podium)' },
  { key: 'hshape', label: 'H자형 (H-shape)' },
  { key: 'radial', label: '방사형 (Radial)' },
];

const DesignPage: React.FC = () => {
  const jobState = useDesignJob();
  const stream = useOptimizationStream();
  const [selectedDesign, setSelectedDesign] = useState<DesignData | null>(null);
  const [activePnu, setActivePnu] = useState('');
  const [buildingType, setBuildingType] = useState('공동주택');
  const [algorithm, setAlgorithm] = useState('all');
  const [viewTab, setViewTab] = useState<'mass' | 'floor'>('mass');
  const [floorPlanResult, setFloorPlanResult] = useState<FloorPlanResult | null>(null);
  const [floorPlanLoading, setFloorPlanLoading] = useState(false);
  const [floorPlanIndex, setFloorPlanIndex] = useState(0);
  const [autoFloorPlan, setAutoFloorPlan] = useState(true);
  const [floorAlgorithm, setFloorAlgorithm] = useState('ga');
  const lastAutoDesignId = useRef<number | null>(null);

  const handlePnuSearch = useCallback(async (pnu: string) => {
    setActivePnu(pnu);
    const boundary = await jobState.loadSiteBoundary(pnu);
    const resolvedPnu = boundary?.pnu || pnu;
    setActivePnu(resolvedPnu);
    console.log('[Design] boundary:', boundary ? `geometry=${boundary.geometry?.type}, area=${boundary.area_m2}` : 'null');
    // MultiPolygon → Polygon (first polygon) 변환. backend compute_setback_lines가 Polygon만
    // 처리. 분할 필지(separated parcels)면 첫 번째만 사용 — 일부 데이터 손실 가능.
    let site_polygon = boundary?.geometry as { type: string; coordinates: unknown } | undefined;
    if (site_polygon?.type === 'MultiPolygon') {
      const coords = site_polygon.coordinates as number[][][][];
      site_polygon = { type: 'Polygon', coordinates: coords[0] as unknown as number[][][] };
    }
    await jobState.loadConstraints({
      pnu: resolvedPnu,
      site_polygon,
      building_type: buildingType,
      include_law_articles: false,
    });
  }, [jobState, buildingType]);

  // Stable ref to avoid SiteMapPanel re-renders (prevents camera reset)
  const handlePnuSearchRef = useRef(handlePnuSearch);
  handlePnuSearchRef.current = handlePnuSearch;

  const handleParcelClick = useCallback((pnu: string, _address: string) => {
    handlePnuSearchRef.current(pnu);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryPnu = params.get('pnu') || params.get('address');
    if (!queryPnu) return;
    handlePnuSearchRef.current(queryPnu);
  }, []);

  const handleStart = useCallback(async (options: { maxGenerations: number; populationSize: number }) => {
    // Decompose population into islands (5 islands default)
    const numIslands = 5;
    const popPerIsland = Math.max(3, Math.round(options.populationSize / numIslands));
    const job = await jobState.startJob({
      pnu: activePnu,
      job_spec: {
        options: {
          'Number of generations': options.maxGenerations,
          'num_islands': numIslands,
          'pop_per_island': popPerIsland,
          'building_type': buildingType,
          'algorithm': algorithm,
        },
      },
    });
    if (job) {
      stream.connect(job.id);
    }
  }, [jobState, stream, buildingType, algorithm]);

  const handleCancel = useCallback(async () => {
    if (jobState.job) {
      await cancelJob(jobState.job.id);
      stream.disconnect();
    }
  }, [jobState.job, stream]);

  const runFloorPlan = useCallback(async (designId: number, quick: boolean) => {
    if (!stream.paretoGeojson?.length) return;
    const feat = stream.paretoGeojson.find(
      f => f.properties.design_id === designId,
    );
    if (!feat) return;

    setFloorPlanLoading(true);
    setFloorPlanIndex(0);
    const genOpts = quick
      ? { num_generations: 10, population_size: 15 }
      : { num_generations: 30, population_size: 30 };
    try {
      const rooms = getRoomPreset(buildingType);
      const result = await generateFloorPlan({
        footprint_geojson: feat.geometry,
        rooms,
        cell_size: 3.0,
        algorithm: floorAlgorithm,
        options: genOpts,
      });
      setFloorPlanResult(result);
      setViewTab('floor');
    } catch (e) {
      console.error('Floor plan generation failed:', e);
    } finally {
      setFloorPlanLoading(false);
    }
  }, [stream.paretoGeojson, buildingType, floorAlgorithm]);

  const handleDesignSelect = useCallback((d: DesignData) => {
    setSelectedDesign(d);
    if (autoFloorPlan && stream.paretoGeojson?.length && d.id !== lastAutoDesignId.current) {
      lastAutoDesignId.current = d.id;
      runFloorPlan(d.id, true);
    }
  }, [autoFloorPlan, stream.paretoGeojson, runFloorPlan]);

  const handleGenerateFloorPlan = useCallback(async () => {
    if (!selectedDesign) return;
    runFloorPlan(selectedDesign.id, false);
  }, [selectedDesign, runFloorPlan]);

  // Derive Pareto axis labels from SSE objectives (per building type)
  const xLabel = stream.objectives[0]
    ? (OBJECTIVE_LABELS[stream.objectives[0].name] || stream.objectives[0].name)
    : 'Floor Area (m\u00B2)';
  const yLabel = stream.objectives[1]
    ? (OBJECTIVE_LABELS[stream.objectives[1].name] || stream.objectives[1].name)
    : 'Daylight Score';

  // Compute mass features for 3D map rendering
  const massFeatures = useMemo(() => {
    // If user selected a specific design, show only that one
    if (selectedDesign && stream.paretoGeojson?.length) {
      const found = stream.paretoGeojson.find(
        f => f.properties.design_id === selectedDesign.id,
      );
      if (found) return [found];
    }
    // During optimization, show best design
    if (stream.bestGeojson) return [stream.bestGeojson];
    return [];
  }, [selectedDesign, stream.paretoGeojson, stream.bestGeojson]);

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      background: '#0a0f1a',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      {/* Left: Map */}
      <div style={{
        flex: 1,
        padding: 12,
        minWidth: 0,
      }}>
        <SiteMapPanel
          sitePolygon={jobState.sitePolygon}
          massFeatures={massFeatures.length > 0 ? massFeatures : undefined}
          selectedDesignId={selectedDesign?.id ?? undefined}
          onParcelClick={handleParcelClick}
          setbackGeometries={jobState.setbackGeometries}
        />
      </div>

      {/* Center: Controls */}
      <div style={{
        width: 320,
        padding: '12px 8px',
        overflowY: 'auto' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 0,
        borderLeft: '1px solid #1e293b',
        borderRight: '1px solid #1e293b',
        background: '#0f172a',
      }}>
        <div style={{
          padding: '4px 8px 14px',
          marginBottom: 4,
        }}>
          <h2 style={{
            color: '#e2e8f0',
            fontSize: 17,
            fontWeight: 700,
            margin: 0,
            letterSpacing: '-0.01em',
          }}>
            건물 매스 최적화
          </h2>
          <p style={{ color: '#475569', fontSize: 11, margin: '4px 0 0', letterSpacing: '0.02em' }}>
            SSIEA Island Evolutionary Algorithm
          </p>
        </div>

        <ControlPanel
          constraints={jobState.constraints}
          siteArea={jobState.siteArea}
          zones={jobState.zones}
          loading={jobState.loading}
          onPnuSearch={handlePnuSearch}
          onStart={handleStart}
          onCancel={handleCancel}
          status={stream.status}
          pnuValue={activePnu}
          buildingTypes={BUILDING_TYPES}
          buildingType={buildingType}
          onBuildingTypeChange={setBuildingType}
          algorithms={ALGORITHMS}
          algorithm={algorithm}
          onAlgorithmChange={setAlgorithm}
        />

        <LegalBasisPanel setbackGeometries={jobState.setbackGeometries} />

        <ConstraintSummary constraints={jobState.constraints} lawArticles={jobState.lawArticles} />

        {/* 지반 레벨 (§119 datum) — envelope 우선, 없으면 datum_result fallback */}
        <DatumInfoCard
          envelope={jobState.setbackGeometries?.sunlight_envelope ?? null}
          datumResult={jobState.setbackGeometries?.datum_result ?? null}
        />

        {/* 정북일조 사선제한 단면도 — 법규 §86① 그대로 2D 시각화 (지도 좌표 독립) */}
        {jobState.zones && jobState.zones.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <SunlightSectionDiagram
              applies={jobState.zones.some((z: string) =>
                z.includes('전용주거') || z.includes('일반주거')
              )}
              targetHeightM={18}
              width={440}
              height={280}
            />
          </div>
        )}

        {stream.status !== 'idle' && (
          <GenerationProgress
            status={stream.status}
            generation={stream.generation}
            maxGenerations={stream.maxGenerations}
            progress={stream.progress}
            feasibleCount={stream.feasibleCount}
            paretoCount={stream.paretoFront.length}
            totalEvaluated={stream.totalDesigns}
            error={stream.error}
          />
        )}
      </div>

      {/* Right: Pareto + List + Inspector */}
      <div style={{
        width: 460,
        display: 'flex',
        flexDirection: 'column' as const,
        background: '#0f172a',
        overflow: 'hidden',
      }}>
        {/* Pareto chart — fixed top */}
        <div style={{ padding: '12px 12px 0', flexShrink: 0 }}>
          {(stream.paretoFront.length > 0 || stream.scatterHistory.length > 0) ? (
            <ParetoChart
              designs={stream.paretoFront}
              scatterHistory={stream.scatterHistory}
              maxGeneration={stream.maxGenerations}
              selectedId={selectedDesign?.id ?? null}
              onSelect={handleDesignSelect}
              xLabel={xLabel}
              yLabel={yLabel}
            />
          ) : stream.status === 'idle' ? (
            <div style={{
              background: 'rgba(30,41,59,0.5)',
              borderRadius: 10,
              padding: 32,
              textAlign: 'center' as const,
              color: '#334155',
              border: '1px dashed #1e293b',
            }}>
              <div style={{ fontSize: 28, marginBottom: 12, opacity: 0.4 }}>&#x25B3;</div>
              <div style={{ fontSize: 13, lineHeight: 1.6 }}>
                왼쪽 지도에서 대지를 선택하고<br />
                최적화를 시작하면<br />
                파레토 프론트가 표시됩니다
              </div>
            </div>
          ) : null}
        </div>

        {/* Tab bar: 매스 | 평면 + 자동 토글 */}
        <div style={{
          display: 'flex', alignItems: 'center', padding: '6px 12px 0',
          borderBottom: '1px solid rgba(255,255,255,0.04)',
          flexShrink: 0,
        }}>
          {(['mass', 'floor'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setViewTab(tab)}
              style={{
                flex: 1, padding: '7px 0', border: 'none', cursor: 'pointer',
                fontSize: 11, fontWeight: 600, letterSpacing: '0.05em',
                background: 'transparent',
                color: viewTab === tab ? '#e2e8f0' : '#475569',
                borderBottom: viewTab === tab ? '2px solid #60c8ff' : '2px solid transparent',
                transition: 'all 0.15s',
              }}
            >
              {tab === 'mass' ? '매스' : '평면'}
            </button>
          ))}
          <select
            value={floorAlgorithm}
            onChange={e => setFloorAlgorithm(e.target.value)}
            style={{
              marginLeft: 6, padding: '2px 4px', borderRadius: 4,
              border: '1px solid #334155', background: '#0f172a',
              color: '#94a3b8', fontSize: 9, cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            <option value="ga">GA</option>
            <option value="subdivision">분할</option>
            <option value="mcts">MCTS</option>
            <option value="packing">패킹</option>
            <option value="graph2plan">Graph2Plan</option>
          </select>
          <button
            onClick={() => setAutoFloorPlan(prev => !prev)}
            title={autoFloorPlan ? '자동 평면 생성 켜짐' : '자동 평면 생성 꺼짐'}
            style={{
              marginLeft: 4, padding: '3px 8px', borderRadius: 6,
              border: 'none', cursor: 'pointer', fontSize: 9, fontWeight: 600,
              background: autoFloorPlan ? 'rgba(96,200,255,0.12)' : 'rgba(255,255,255,0.03)',
              color: autoFloorPlan ? '#60c8ff' : '#475569',
              transition: 'all 0.15s', whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            자동 {autoFloorPlan ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Tab content */}
        <div style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {viewTab === 'mass' ? (
            <div style={{ flex: 1, padding: '8px 12px', overflowY: 'auto', minHeight: 0 }}>
              <DesignList
                designs={stream.paretoFront}
                selectedId={selectedDesign?.id ?? null}
                onSelect={handleDesignSelect}
                objectiveNames={stream.objectives.map(o => o.name)}
              />

              {selectedDesign && (
                <div style={{ marginTop: 8 }}>
                  <DesignInspector design={selectedDesign} objectiveNames={stream.objectives.map(o => o.name)} />
                  {/* 평면 생성 버튼 */}
                  {stream.paretoGeojson?.length > 0 && (
                    <button
                      onClick={handleGenerateFloorPlan}
                      disabled={floorPlanLoading}
                      style={{
                        width: '100%', marginTop: 10, padding: '10px 0',
                        borderRadius: 8, border: 'none', cursor: 'pointer',
                        fontSize: 12, fontWeight: 700, letterSpacing: '0.03em',
                        background: floorPlanLoading
                          ? 'rgba(96,200,255,0.08)'
                          : 'linear-gradient(135deg, rgba(96,200,255,0.15), rgba(96,200,255,0.08))',
                        color: '#60c8ff',
                        transition: 'all 0.15s',
                      }}
                    >
                      {floorPlanLoading ? '생성 중...' : '⊞ 평면 생성'}
                    </button>
                  )}
                </div>
              )}
            </div>
          ) : (
            <FloorPlanViewer
              result={floorPlanResult}
              selectedIndex={floorPlanIndex}
              onSelectIndex={setFloorPlanIndex}
              loading={floorPlanLoading}
            />
          )}
        </div>

        {jobState.error && (
          <div style={{
            padding: '10px 14px', margin: '0 12px 12px',
            background: 'rgba(69,10,10,0.6)',
            borderRadius: 8,
            border: '1px solid rgba(239,68,68,0.2)',
            color: '#fca5a5',
            fontSize: 13,
            flexShrink: 0,
          }}>
            {jobState.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default DesignPage;
