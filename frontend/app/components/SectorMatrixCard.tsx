'use client';

import React from 'react';
import { Timer, ArrowRight, Award } from 'lucide-react';

interface SectorMatrixCardProps {
  telemetry: any;
}

export const SectorMatrixCard: React.FC<SectorMatrixCardProps> = ({ telemetry }) => {
  if (!telemetry || typeof telemetry !== 'object') return null;

  const primaryCode = telemetry.driver || 'PRI';
  const compData = telemetry.comparison_driver;
  const compCode = compData?.driver || null;

  const pS1 = telemetry.sector1_seconds;
  const pS2 = telemetry.sector2_seconds;
  const pS3 = telemetry.sector3_seconds;
  const pLap = telemetry.fastest_lap_time_seconds;

  const cS1 = compData?.sector1_seconds;
  const cS2 = compData?.sector2_seconds;
  const cS3 = compData?.sector3_seconds;
  const cLap = compData?.fastest_lap_time_seconds;

  // Best sector logic (lower is faster)
  const bestS1 = Math.min(...[pS1, cS1].filter((v) => typeof v === 'number' && v > 0));
  const bestS2 = Math.min(...[pS2, cS2].filter((v) => typeof v === 'number' && v > 0));
  const bestS3 = Math.min(...[pS3, cS3].filter((v) => typeof v === 'number' && v > 0));
  const bestLap = Math.min(...[pLap, cLap].filter((v) => typeof v === 'number' && v > 0));

  const formatSec = (val?: number | null) => (val && val > 0 ? `${val.toFixed(3)}s` : '—');

  const getStyle = (val?: number | null, bestVal?: number) => {
    if (!val || val <= 0) return { color: '#5A5A5A' };
    if (val === bestVal) return { color: '#A855F7', fontWeight: 800 }; // Purple overall best
    return { color: '#22C55E', fontWeight: 700 }; // Green personal best
  };

  return (
    <div style={{
      background: '#111111',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '10px',
      overflow: 'hidden',
      marginBottom: '16px',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        background: '#161616',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Timer size={13} style={{ color: '#E10600' }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#F5F5F5', letterSpacing: '0.02em' }}>
            Sector Pace & Delta Matrix
          </span>
        </div>
        <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#5A5A5A' }}>
          {compCode ? `${primaryCode} vs ${compCode}` : primaryCode}
        </span>
      </div>

      {/* Table grid */}
      <div style={{ padding: '14px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', color: '#5A5A5A', fontSize: '10px', textAlign: 'left' }}>
              <th style={{ paddingBottom: '8px' }}>DRIVER</th>
              <th style={{ paddingBottom: '8px' }}>SECTOR 1</th>
              <th style={{ paddingBottom: '8px' }}>SECTOR 2</th>
              <th style={{ paddingBottom: '8px' }}>SECTOR 3</th>
              <th style={{ paddingBottom: '8px', textAlign: 'right' }}>BEST LAP</th>
            </tr>
          </thead>
          <tbody>
            {/* Primary Driver Row */}
            <tr style={{ borderBottom: compCode ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
              <td style={{ padding: '10px 0', fontWeight: 800, color: '#E10600' }}>
                {primaryCode}
              </td>
              <td style={{ padding: '10px 0', ...getStyle(pS1, bestS1) }}>
                {formatSec(pS1)}
              </td>
              <td style={{ padding: '10px 0', ...getStyle(pS2, bestS2) }}>
                {formatSec(pS2)}
              </td>
              <td style={{ padding: '10px 0', ...getStyle(pS3, bestS3) }}>
                {formatSec(pS3)}
              </td>
              <td style={{ padding: '10px 0', textAlign: 'right', ...getStyle(pLap, bestLap) }}>
                {formatSec(pLap)}
              </td>
            </tr>

            {/* Comparison Driver Row */}
            {compCode && (
              <tr>
                <td style={{ padding: '10px 0', fontWeight: 800, color: '#F59E0B' }}>
                  {compCode}
                </td>
                <td style={{ padding: '10px 0', ...getStyle(cS1, bestS1) }}>
                  {formatSec(cS1)}
                </td>
                <td style={{ padding: '10px 0', ...getStyle(cS2, bestS2) }}>
                  {formatSec(cS2)}
                </td>
                <td style={{ padding: '10px 0', ...getStyle(cS3, bestS3) }}>
                  {formatSec(cS3)}
                </td>
                <td style={{ padding: '10px 0', textAlign: 'right', ...getStyle(cLap, bestLap) }}>
                  {formatSec(cLap)}
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.04)', fontSize: '10px', color: '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#A855F7', display: 'inline-block' }} />
            <span>Session Best Sector</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22C55E', display: 'inline-block' }} />
            <span>Driver Personal Best</span>
          </div>
        </div>
      </div>
    </div>
  );
};
