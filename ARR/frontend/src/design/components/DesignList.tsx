import React from 'react';
import type { DesignData } from '../lib/types';

const ALGO_COLORS: Record<string, string> = {
  additive: '#60a5fa', subtractive: '#a78bfa', grid: '#34d399',
  lshape: '#f97316', ushape: '#06b6d4', cross: '#ef4444',
  courtyard: '#f472b6', tower_podium: '#eab308', hshape: '#8b5cf6',
  radial: '#14b8a6',
};

const ALGO_LABELS: Record<string, string> = {
  additive: '자유', subtractive: '감산', grid: '격자',
  lshape: 'ㄱ자', ushape: 'ㄷ자', cross: '십자',
  courtyard: '중정', tower_podium: '타워', hshape: 'H형',
  radial: '방사',
};

interface Props {
  designs: DesignData[];
  selectedId: number | null;
  onSelect: (design: DesignData) => void;
  objectiveNames: string[];
}

const OBJ_LABELS: Record<string, string> = {
  floor_area: '연면적',
  daylight_score: '일조',
  landscaping_pct: '외부공간',
  setback: '이격',
};

const DesignList: React.FC<Props> = React.memo(({ designs, selectedId, onSelect, objectiveNames }) => {
  if (designs.length === 0) return null;

  const obj0 = objectiveNames[0] || 'floor_area';
  const obj1 = objectiveNames[1] || 'daylight_score';

  return (
    <div style={{
      background: 'linear-gradient(180deg, #0c1120 0%, #0e1525 100%)',
      borderRadius: 12,
      border: '1px solid rgba(255,255,255,0.06)',
      boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        <span style={{ color: '#8b95a8', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em' }}>
          DESIGN LIST
        </span>
        <span style={{
          padding: '2px 8px', borderRadius: 10,
          background: 'rgba(96,200,255,0.08)', color: '#60c8ff',
          fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: 600,
        }}>
          {designs.length}
        </span>
      </div>

      {/* Column headers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '32px 42px 1fr 1fr 52px',
        gap: 0,
        padding: '6px 10px',
        fontSize: 9, color: '#475569', fontWeight: 600, letterSpacing: '0.05em',
        borderBottom: '1px solid rgba(255,255,255,0.03)',
      }}>
        <span>#</span>
        <span>형태</span>
        <span>{OBJ_LABELS[obj0] || obj0}</span>
        <span>{OBJ_LABELS[obj1] || obj1}</span>
        <span>상태</span>
      </div>

      {/* Scrollable list */}
      <div style={{ maxHeight: 240, overflowY: 'auto' }}>
        {designs.map((d, i) => {
          const isSelected = d.id === selectedId;
          const algo = (d as any).algorithm || 'additive';
          const algoColor = ALGO_COLORS[algo] || '#60a5fa';
          const algoLabel = ALGO_LABELS[algo] || algo;

          return (
            <div
              key={d.id}
              onClick={() => onSelect(d)}
              style={{
                display: 'grid',
                gridTemplateColumns: '32px 42px 1fr 1fr 52px',
                gap: 0,
                padding: '7px 10px',
                cursor: 'pointer',
                fontSize: 11,
                fontFamily: 'ui-monospace, monospace',
                background: isSelected
                  ? 'rgba(96,200,255,0.08)'
                  : i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                borderLeft: isSelected ? '2px solid #60c8ff' : '2px solid transparent',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => {
                if (!isSelected) (e.currentTarget.style.background = 'rgba(255,255,255,0.03)');
              }}
              onMouseLeave={e => {
                if (!isSelected) (e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)');
              }}
            >
              <span style={{ color: isSelected ? '#60c8ff' : '#5a6577' }}>
                {i + 1}
              </span>
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: algoColor, display: 'inline-block',
                  flexShrink: 0,
                }} />
                <span style={{ color: algoColor, fontSize: 9 }}>
                  {algoLabel}
                </span>
              </span>
              <span style={{ color: '#e2e8f0' }}>
                {d.objectives[0] >= 1000
                  ? (d.objectives[0] / 1000).toFixed(1) + 'k'
                  : d.objectives[0]?.toFixed(0)}
              </span>
              <span style={{ color: '#e2e8f0' }}>
                {d.objectives[1]?.toFixed(1)}
              </span>
              <span style={{
                fontSize: 9,
                color: d.feasible ? '#34d399' : '#f87171',
              }}>
                {d.feasible ? 'OK' : 'X'}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
});

DesignList.displayName = 'DesignList';
export default DesignList;
