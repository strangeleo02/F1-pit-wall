"use client";

import React, { useEffect, useState, useMemo } from "react";
import { MapPin, Timer } from "lucide-react";
import { API_BASE_URL } from "../config";

// Module-level cache — survives re-renders, cleared only on page reload.
// Circuit data and pitstop averages are static historical data; no need to refetch.
const _circuitCache = new Map<string, any>();
const _pitstopCache = new Map<number, string | null>();

interface Corner {
  number: string;
  name: string;
  distance_pct: number;
  type: string;
}

interface CircuitData {
  grand_prix: string;
  circuit_key: string;
  corners: Corner[];
  points: Array<{ x: number; y: number; distance_pct: number }>;
}

interface CircuitMapProps {
  grandPrix: string;
  year: number;
  hoverDistancePct?: number | null;
  driverCode?: string;
  comparisonDriverCode?: string;
  telemetry?: any;
  onHoverDistancePctChange?: (distPct: number | null) => void;
}

export const CircuitMap: React.FC<CircuitMapProps> = ({
  grandPrix,
  year,
  hoverDistancePct,
  driverCode = "VER",
  comparisonDriverCode,
  telemetry,
  onHoverDistancePctChange
}) => {
  const [circuitMeta, setCircuitMeta] = useState<CircuitData | null>(null);
  const [pitstopAvg, setPitstopAvg] = useState<string | null>(null);

  const API_BASE = API_BASE_URL;

  // Fetch circuit landmark corners and pit stop benchmarks — cached per (grandPrix, year)
  useEffect(() => {
    let isMounted = true;

    // Circuit meta — keyed by grandPrix (track layout doesn't change year-to-year)
    if (_circuitCache.has(grandPrix)) {
      setCircuitMeta(_circuitCache.get(grandPrix));
    } else {
      fetch(`${API_BASE}/api/v1/meta/circuit?grand_prix=${encodeURIComponent(grandPrix)}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (isMounted && data) {
            _circuitCache.set(grandPrix, data);
            setCircuitMeta(data);
          }
        })
        .catch((err) => console.warn("Circuit meta fetch error:", err));
    }

    // Pitstop averages — keyed by year
    if (_pitstopCache.has(year)) {
      setPitstopAvg(_pitstopCache.get(year) ?? null);
    } else {
      fetch(`${API_BASE}/api/v1/history/pitstops?year=${year}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (isMounted && data?.pitstops?.length > 0) {
            const validStops = data.pitstops
              .map((s: any) => parseFloat(s.duration))
              .filter((d: number) => !isNaN(d) && d > 1.5 && d < 15.0);
            if (validStops.length > 0) {
              const avg = validStops.reduce((a: number, b: number) => a + b, 0) / validStops.length;
              const avgStr = avg.toFixed(2);
              _pitstopCache.set(year, avgStr);
              if (isMounted) setPitstopAvg(avgStr);
            } else {
              _pitstopCache.set(year, null);
            }
          }
        })
        .catch(() => {});
    }

    return () => { isMounted = false; };
  }, [grandPrix, year]);

  // Helper engine to fit ANY set of 2D points to fill the 500x320 SVG canvas full-size
  const fitPointsToCanvas = <T extends { x: number; y: number; distance_pct?: number }>(rawPts: T[]) => {
    if (!rawPts || rawPts.length < 3) return [];

    const xVals = rawPts.map((p) => p.x);
    const yVals = rawPts.map((p) => p.y);

    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const minY = Math.min(...yVals);
    const maxY = Math.max(...yVals);

    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    const width = 500;
    const height = 320;
    const padding = 35;

    const availW = width - padding * 2;
    const availH = height - padding * 2;

    const scale = Math.min(availW / rangeX, availH / rangeY);

    const offsetX = (width - rangeX * scale) / 2;
    const offsetY = (height - rangeY * scale) / 2;

    return rawPts.map((p, i) => ({
      ...p,
      x: (p.x - minX) * scale + offsetX,
      y: height - ((p.y - minY) * scale + offsetY),
      distance_pct: p.distance_pct !== undefined ? p.distance_pct : (i / (rawPts.length - 1)) * 100
    }));
  };

  // Extract Real Track Geometry from Telemetry (x_m, y_m)
  const realTrackData = useMemo(() => {
    const rawStream = telemetry?.telemetry_stream || {};
    const xCoords: number[] = rawStream.x_m || [];
    const yCoords: number[] = rawStream.y_m || [];
    const speedKph: number[] = rawStream.speed_kph || [];

    if (xCoords.length < 10 || yCoords.length < 10) return null;

    const raw = xCoords.map((x, i) => ({
      x,
      y: yCoords[i],
      speed: speedKph[i] || 200,
      distance_pct: (i / (xCoords.length - 1)) * 100
    }));

    return fitPointsToCanvas<{ x: number; y: number; speed: number; distance_pct: number }>(raw);
  }, [telemetry]);

  // Extract comparison driver telemetry coordinates
  const compTrackData = useMemo(() => {
    const compStream = telemetry?.comparison_driver?.telemetry_stream || {};
    const xCoords: number[] = compStream.x_m || [];
    const yCoords: number[] = compStream.y_m || [];

    if (!realTrackData || xCoords.length < 10 || yCoords.length < 10) return null;

    const raw = xCoords.map((x, i) => ({
      x,
      y: yCoords[i],
      distance_pct: (i / (xCoords.length - 1)) * 100
    }));

    return fitPointsToCanvas(raw);
  }, [telemetry, realTrackData]);

  // Fallback points scaled to fill 500x320 canvas
  const scaledFallbackPoints = useMemo(() => {
    if (!circuitMeta?.points || circuitMeta.points.length === 0) return [];
    return fitPointsToCanvas(circuitMeta.points);
  }, [circuitMeta]);

  // Active points array to render
  const activePoints = realTrackData || scaledFallbackPoints;
  const corners = circuitMeta?.corners || [];

  // SVG Path string
  const pathD = useMemo(() => {
    if (activePoints.length === 0) return "M 50 160 Q 250 20 450 160 Q 250 300 50 160 Z";
    return activePoints.reduce((acc, pt, idx) => `${acc} ${idx === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`, "") + " Z";
  }, [activePoints]);

  const getSpeedColor = (speed: number) => {
    if (speed < 140) return "#EF4444"; // Heavy braking (Red)
    if (speed < 240) return "#EAB308"; // Apex (Yellow)
    return "#27F4D2"; // High speed (Cyan)
  };

  // Driver positions on track layout
  const activeDriverPoint = useMemo(() => {
    if (hoverDistancePct === undefined || hoverDistancePct === null || activePoints.length === 0) return null;
    const idx = Math.min(activePoints.length - 1, Math.max(0, Math.floor((hoverDistancePct / 100) * activePoints.length)));
    return activePoints[idx];
  }, [hoverDistancePct, activePoints]);

  const compDriverPoint = useMemo(() => {
    if (!compTrackData || hoverDistancePct === undefined || hoverDistancePct === null) return null;
    const idx = Math.min(compTrackData.length - 1, Math.max(0, Math.floor((hoverDistancePct / 100) * compTrackData.length)));
    return compTrackData[idx];
  }, [hoverDistancePct, compTrackData]);

  // Interactive SVG hover / click
  const handleSvgMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!activePoints.length || !onHoverDistancePctChange) return;

    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const clickX = ((e.clientX - rect.left) / rect.width) * 500;
    const clickY = ((e.clientY - rect.top) / rect.height) * 320;

    let closestDist = Infinity;
    let closestPct = 0;

    activePoints.forEach((pt) => {
      const d = Math.hypot(pt.x - clickX, pt.y - clickY);
      if (d < closestDist) {
        closestDist = d;
        closestPct = pt.distance_pct;
      }
    });

    if (closestDist < 60) {
      onHoverDistancePctChange(closestPct);
    }
  };

  const compCode = comparisonDriverCode || telemetry?.comparison_driver?.driver;

  return (
    <div style={{
      background: '#111111',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '10px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: '#161616',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <MapPin size={12} style={{ color: '#E10600' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#F5F5F5', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.03em' }}>
            {grandPrix} Circuit
          </span>
        </div>
        {pitstopAvg && (
          <span style={{
            fontSize: '10px',
            fontFamily: 'JetBrains Mono, monospace',
            color: '#9A9A9A',
          }}>
            <Timer size={10} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle', color: '#5A5A5A' }} />
            Avg Stop: <strong style={{ color: '#F5F5F5' }}>{pitstopAvg}s</strong>
          </span>
        )}
      </div>

      {/* Driver Legend */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#27F4D2', fontWeight: 600 }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#27F4D2', display: 'inline-block' }} />
            {driverCode}
          </span>
          {compCode && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#F59E0B', fontWeight: 600 }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B', display: 'inline-block' }} />
              {compCode}
            </span>
          )}
        </div>
        <span style={{ fontSize: '9px', color: '#3A3A3A', fontFamily: 'JetBrains Mono, monospace' }}>hover to inspect</span>
      </div>

      {/* SVG Map Canvas */}
      <div style={{ position: 'relative', width: '100%', height: '280px', background: '#0D0D0D', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
        <svg
          viewBox="0 0 500 320"
          className="w-full h-full cursor-crosshair overflow-visible"
          onMouseMove={handleSvgMouseMove}
          onMouseLeave={() => onHoverDistancePctChange?.(null)}
        >
          <defs>
            <filter id="circuitGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Base Track Underlay Line */}
          <path
            d={pathD}
            fill="none"
            stroke="#1E293B"
            strokeWidth="10"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Telemetry Colored Speed Track Line */}
          {realTrackData && realTrackData.length > 1 ? (
            realTrackData.map((pt, idx) => {
              if (idx === realTrackData.length - 1) return null;
              const nextPt = realTrackData[idx + 1];
              return (
                <line
                  key={idx}
                  x1={pt.x}
                  y1={pt.y}
                  x2={nextPt.x}
                  y2={nextPt.y}
                  stroke={getSpeedColor((pt.speed + nextPt.speed) / 2)}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                />
              );
            })
          ) : (
            <path
              d={pathD}
              fill="none"
              stroke="#27F4D2"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Turn Landmark Corner Annotations */}
          {corners.map((c, i) => {
            const cornerIdx = Math.min(
              activePoints.length - 1,
              Math.max(0, Math.floor((c.distance_pct / 100) * activePoints.length))
            );
            const cornerPt = activePoints[cornerIdx] || { x: 250, y: 160 };
            return (
              <g key={i}>
                <circle cx={cornerPt.x} cy={cornerPt.y} r="3.5" fill="#FF8000" stroke="#000" strokeWidth="1" />
                <text
                  x={cornerPt.x + 5}
                  y={cornerPt.y - 4}
                  fill="#E2E8F0"
                  fontSize="9.5"
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  {c.number}
                </text>
              </g>
            );
          })}

          {/* Comparison Driver Position Marker */}
          {compDriverPoint && (
            <g className="transition-all duration-75 ease-out">
              <circle cx={compDriverPoint.x} cy={compDriverPoint.y} r="10" fill="#F59E0B" fillOpacity="0.3" className="animate-ping" />
              <circle cx={compDriverPoint.x} cy={compDriverPoint.y} r="5" fill="#F59E0B" stroke="#FFFFFF" strokeWidth="1.5" />
              <text
                x={compDriverPoint.x + 6}
                y={compDriverPoint.y + 3}
                fill="#F59E0B"
                fontSize="10"
                fontWeight="900"
                fontFamily="monospace"
              >
                {compCode}
              </text>
            </g>
          )}

          {/* Primary Driver Hover Marker */}
          {activeDriverPoint && (
            <g className="transition-all duration-75 ease-out">
              <circle cx={activeDriverPoint.x} cy={activeDriverPoint.y} r="12" fill="#27F4D2" fillOpacity="0.35" className="animate-ping" />
              <circle cx={activeDriverPoint.x} cy={activeDriverPoint.y} r="6" fill="#27F4D2" stroke="#FFFFFF" strokeWidth="2" filter="url(#circuitGlow)" />
              <text
                x={activeDriverPoint.x + 7}
                y={activeDriverPoint.y - 4}
                fill="#27F4D2"
                fontSize="11"
                fontWeight="900"
                fontFamily="monospace"
              >
                {driverCode}
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Footer — Speed legend & track position */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 14px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#5A5A5A' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#27F4D2', display: 'inline-block' }} />&gt;240</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#EAB308', display: 'inline-block' }} />140–240</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#EF4444', display: 'inline-block' }} />&lt;140 km/h</span>
        </div>
        <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: hoverDistancePct !== null && hoverDistancePct !== undefined ? '#27F4D2' : '#3A3A3A' }}>
          {hoverDistancePct !== null && hoverDistancePct !== undefined ? `${hoverDistancePct.toFixed(1)}%` : '—'}
        </span>
      </div>
    </div>
  );
};
