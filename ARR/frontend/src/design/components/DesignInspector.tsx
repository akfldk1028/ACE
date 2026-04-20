import React from 'react';
import type { DesignData } from '../lib/types';

interface Props {
  design: DesignData | null;
  objectiveNames?: string[];
}

const OBJECTIVE_META: Record<string, { label: string; unit: string; color: string }> = {
  floor_area:      { label: '연면적',   unit: 'm\u00B2', color: '#60c8ff' },
  daylight_score:  { label: '일조점수', unit: '점',      color: '#fbbf24' },
  landscaping_pct: { label: '외부공간', unit: '%',       color: '#34d399' },
  setback:         { label: '이격거리', unit: 'm',       color: '#a78bfa' },
};

const DesignInspector: React.FC<Props> = React.memo(({ design, objectiveNames }) => {
  if (!design) {
    return (
      <div style={{
        background: 'linear-gradient(180deg, #0c1120 0%, #0e1525 100%)',
        borderRadius: 12,
        padding: 28,
        color: '#2d3548',
        fontSize: 12,
        textAlign: 'center' as const,
        border: '1px dashed rgba(255,255,255,0.06)',
      }}>
        <div style={{ fontSize: 24, marginBottom: 8, opacity: 0.3 }}>&#x25CE;</div>
        파레토 포인트를 클릭하세요
      </div>
    );
  }

  // Build objective cards from design data
  const objNames = objectiveNames || [];
  const objectives = design.objectives || [];

  return (
    <div style={{
      background: 'linear-gradient(180deg, #0c1120 0%, #0e1525 100%)',
      borderRadius: 12,
      padding: 16,
      border: '1px solid rgba(255,255,255,0.06)',
      boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 14,
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ color: '#5a6577', fontSize: 10, fontWeight: 700, letterSpacing: '0.1em' }}>
            DESIGN
          </span>
          <span style={{ color: '#e2e8f0', fontSize: 22, fontWeight: 800, fontFamily: 'ui-monospace, monospace' }}>
            #{design.id}
          </span>
        </div>
        <span style={{
          padding: '3px 10px', borderRadius: 8,
          fontSize: 10, fontWeight: 700, letterSpacing: '0.05em',
          background: design.feasible
            ? 'rgba(52,211,153,0.1)' : 'rgba(239,68,68,0.08)',
          color: design.feasible ? '#34d399' : '#f87171',
          border: `1px solid ${design.feasible ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.15)'}`,
        }}>
          {design.feasible ? 'FEASIBLE' : 'INFEASIBLE'}
        </span>
      </div>

      {/* Objective metric cards — dynamic based on building type */}
      {objectives.length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          {objectives.slice(0, 2).map((val, i) => {
            const name = objNames[i] || (i === 0 ? 'floor_area' : 'daylight_score');
            const meta = OBJECTIVE_META[name] || { label: name, unit: '', color: '#60c8ff' };
            return (
              <div key={i} style={{
                flex: 1,
                padding: '14px 12px',
                background: `linear-gradient(135deg, ${meta.color}08, ${meta.color}04)`,
                borderRadius: 10,
                textAlign: 'center' as const,
                border: `1px solid ${meta.color}18`,
                position: 'relative' as const,
                overflow: 'hidden',
              }}>
                {/* Subtle glow at top */}
                <div style={{
                  position: 'absolute', top: 0, left: '20%', right: '20%', height: 1,
                  background: `linear-gradient(90deg, transparent, ${meta.color}40, transparent)`,
                }} />
                <div style={{ color: '#5a6577', fontSize: 9, fontWeight: 600, letterSpacing: '0.08em', marginBottom: 6 }}>
                  {meta.label}
                </div>
                <div style={{
                  color: meta.color, fontSize: 22, fontWeight: 800,
                  fontFamily: 'ui-monospace, monospace',
                  textShadow: `0 0 20px ${meta.color}30`,
                }}>
                  {val >= 1000 ? val.toLocaleString('en-US', { maximumFractionDigits: 0 }) : val.toFixed(1)}
                </div>
                <div style={{ color: '#3d4556', fontSize: 9, marginTop: 2 }}>{meta.unit}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Performance bars */}
      {objectives.length >= 2 && (
        <div style={{ marginBottom: 14 }}>
          {objectives.slice(0, 2).map((val, i) => {
            const name = objNames[i] || (i === 0 ? 'floor_area' : 'daylight_score');
            const meta = OBJECTIVE_META[name] || { label: name, unit: '', color: '#60c8ff' };
            // Normalize to 0-100 range for display
            const displayPct = name === 'floor_area'
              ? Math.min(100, val / 300)         // 30000m²→100%
              : name === 'daylight_score'
                ? val                            // already 0-100
                : Math.min(100, val);
            return (
              <div key={i} style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ color: '#5a6577', fontSize: 10 }}>{meta.label}</span>
                  <span style={{
                    color: meta.color, fontSize: 12, fontWeight: 700,
                    fontFamily: 'ui-monospace, monospace',
                  }}>
                    {val >= 1000 ? (val / 1000).toFixed(1) + 'k' : val.toFixed(1)}
                  </span>
                </div>
                <div style={{
                  height: 3, background: 'rgba(255,255,255,0.03)', borderRadius: 2,
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%', borderRadius: 2,
                    width: `${Math.min(100, displayPct)}%`,
                    background: `linear-gradient(90deg, ${meta.color}60, ${meta.color})`,
                    boxShadow: `0 0 8px ${meta.color}40`,
                    transition: 'width 0.4s ease',
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Gene parameters — compact scrollable grid */}
      <details style={{ marginBottom: 0 }}>
        <summary style={{
          color: '#3d4556', fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
          cursor: 'pointer', marginBottom: 6, userSelect: 'none' as const,
          listStyle: 'none',
          display: 'flex', alignItems: 'center', gap: 4,
        }}>
          <span style={{ fontSize: 8, transition: 'transform 0.2s' }}>&#x25B6;</span>
          PARAMETERS ({design.inputs.length} genes)
        </summary>
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2,
          maxHeight: 160, overflowY: 'auto' as const,
        }}>
          {design.inputs.map((inp, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between',
              padding: '3px 8px',
              background: 'rgba(255,255,255,0.02)',
              borderRadius: 4, fontSize: 10,
            }}>
              <span style={{ color: '#3d4556' }}>G{i}</span>
              <span style={{ color: '#8b95a8', fontFamily: 'ui-monospace, monospace' }}>
                {typeof inp[0] === 'number' ? inp[0].toFixed(2) : inp[0]}
              </span>
            </div>
          ))}
        </div>
      </details>

      {/* Meta info */}
      <div style={{
        marginTop: 10, paddingTop: 10,
        borderTop: '1px solid rgba(255,255,255,0.04)',
        display: 'flex', gap: 12, fontSize: 10, color: '#3d4556',
        fontFamily: 'ui-monospace, monospace',
      }}>
        <span>Gen {design.generation}</span>
        <span>Rank {design.rank}</span>
        <span>Pen {design.penalty.toFixed(2)}</span>
      </div>
    </div>
  );
});

DesignInspector.displayName = 'DesignInspector';
export default DesignInspector;
