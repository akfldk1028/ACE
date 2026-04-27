import React from 'react';
import type { SunlightEnvelope } from '../../land/lib/types';

const CASE_LABEL: Record<string, string> = {
  flat: '평탄지 (§119① 5호)',
  slope_le3m: '경사지 ≤8m (§119② 가중평균)',
  slope_gt3m: '경사지 >8m (§119② 단서)',
  road_flat: '도로접지 평지 (§119① 5호 가목)',
  road_sloped: '도로접지 경사 (§119① 5호 가목 단서)',
  site_above_road: '대지>도로 (§119① 5호 나목)',
  neighbor_avg_86: '정북인접 평균 (§86)',
};

const SOURCE_LABEL: Record<string, string> = {
  open_meteo: 'Open-Meteo (90m DEM)',
  failed: '⚠ fetch 실패',
};

const BASIS_LABEL: Record<string, string> = {
  ground_flat: '대지 평탄',
  ground_weighted_avg: '대지 둘레 가중평균',
  ground_split_3m: '대지 3m 분할',
  road_centerline: '도로 중심선',
  road_centerline_weighted_avg: '도로 가중평균',
  site_above_road_half_raise: '대지>도로 1/2 raise',
  neighbor_avg_86: '인접지 평균',
  elevation_fetch_failed: '⚠ fetch 실패 → 0.0 fallback',
};

interface Props {
  envelope: SunlightEnvelope | null | undefined;
}

/**
 * 정북일조 envelope의 §119 datum 메타데이터를 시각 표시.
 *
 * 3-state:
 *   elevation_source = null      → datum 미계산 (회색 안내, ENABLE_DATUM_ELEVATION=false)
 *   elevation_source = open_meteo → cyan accent, datum_m + case + basis + source
 *   elevation_source = failed    → amber accent, fetch 실패 표시
 *
 * Sibling: ConstraintSummary와 동일 surface(`#111827`/`#1e293b`).
 */
const DatumInfoCard: React.FC<Props> = React.memo(({ envelope }) => {
  if (!envelope) return null;

  // datum 미계산 (env flag false 또는 backend 미전달)
  if (envelope.elevation_source == null) {
    return (
      <div style={{
        background: '#111827', borderRadius: 10, padding: 14, marginBottom: 10,
        border: '1px solid #1e293b',
      }}>
        <h3 style={{
          color: '#64748b', fontSize: 10, fontWeight: 600,
          marginBottom: 6, letterSpacing: '0.08em',
          textTransform: 'uppercase' as const, margin: 0,
        }}>지반 레벨 (§119 datum)</h3>
        <p style={{ margin: '6px 0 0 0', fontSize: 11, color: '#64748b', lineHeight: 1.5 }}>
          datum 미계산 (ENABLE_DATUM_ELEVATION=false). envelope은 Cesium terrain 사용.
        </p>
      </div>
    );
  }

  const datum_m = envelope.datum_elevation_m ?? 0;
  const caseLabel = envelope.datum_case
    ? (CASE_LABEL[envelope.datum_case] ?? envelope.datum_case) : '-';
  const srcLabel = SOURCE_LABEL[envelope.elevation_source] ?? envelope.elevation_source;
  const basisLabel = envelope.datum_basis
    ? (BASIS_LABEL[envelope.datum_basis] ?? envelope.datum_basis) : null;
  const isFailed = envelope.elevation_source === 'failed';
  const accent = isFailed ? '#f59e0b' : '#22d3ee';   // amber / cyan (design 모듈은 hex 직접 사용 패턴)

  return (
    <div style={{
      background: '#111827', borderRadius: 10, padding: 14, marginBottom: 10,
      border: '1px solid #1e293b',
      borderLeft: `3px solid ${accent}`,
    }}>
      <h3 style={{
        color: '#64748b', fontSize: 10, fontWeight: 600,
        marginBottom: 10, letterSpacing: '0.08em',
        textTransform: 'uppercase' as const, margin: 0,
      }}>지반 레벨 (§119 datum)</h3>

      {/* H=0 표고 강조 */}
      <div style={{
        display: 'flex', alignItems: 'baseline', gap: 8,
        padding: '8px 0 6px 0',
        borderBottom: '1px solid #1e293b',
        marginBottom: 6, marginTop: 4,
      }}>
        <span style={{ color: '#94a3b8', fontSize: 12 }}>H = 0 절대 표고</span>
        <span style={{ flex: 1 }} />
        <span style={{
          fontSize: 22, fontWeight: 700, color: accent,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontFeatureSettings: '"tnum"',
        }}>
          {datum_m.toFixed(2)}
          <span style={{ fontSize: 12, fontWeight: 500, color: '#64748b', marginLeft: 4 }}>m</span>
        </span>
      </div>

      {/* 케이스 + 산정방법 + 소스 */}
      {([
        ['§119/§86 케이스', caseLabel, false],
        ...(basisLabel ? [['산정 방법', basisLabel, false]] : []),
        ['데이터 소스', srcLabel, true],
      ] as Array<[string, string, boolean]>).map(([label, val, mono], i) => (
        <div key={label} style={{
          display: 'flex', justifyContent: 'space-between',
          padding: '4px 0', fontSize: 11,
          borderTop: i > 0 ? '1px solid #1e293b' : 'none',
        }}>
          <span style={{ color: '#94a3b8' }}>{label}</span>
          <span style={{
            color: '#e2e8f0', fontWeight: 500,
            fontFamily: mono ? 'ui-monospace, SFMono-Regular, Menlo, monospace' : 'inherit',
          }}>{val}</span>
        </div>
      ))}

      <p style={{
        margin: '8px 0 0 0', fontSize: 10, color: '#64748b', lineHeight: 1.5,
      }}>
        envelope walls/slanted_polygons 의 H는 이 datum 기준 상대값.
        Cesium 렌더 시 datum_m 위에 envelope 위치 (3-state: open_meteo→datum, failed/null→terrainH).
      </p>
    </div>
  );
});

DatumInfoCard.displayName = 'DatumInfoCard';

export default DatumInfoCard;
