'use client';

import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import { Activity, Gauge, Zap, Flame, Award, ShieldAlert, Compass, Users } from 'lucide-react';

interface TelemetryChartsProps {
  telemetry: any;
}

export const TelemetryCharts: React.FC<TelemetryChartsProps> = ({ telemetry }) => {
  if (!telemetry || typeof telemetry !== 'object' || Object.keys(telemetry).length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6 mb-6 text-center text-slate-500 font-mono text-xs">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-30 text-cyan-400 animate-pulse" />
        <p>No Telemetry Stream Data Available For Current Query</p>
      </div>
    );
  }

  const primaryDriver = telemetry.driver || 'Primary Driver';
  const compDriverData = telemetry.comparison_driver;
  const compDriverCode = compDriverData?.driver;

  // Format telemetry stream data points for Primary Driver
  const rawStream = telemetry.telemetry_stream || {};
  const timeSecs: number[] = rawStream.time_seconds || [];
  const distMeters: number[] = rawStream.distance_meters || [];
  const speedKph: number[] = rawStream.speed_kph || [];
  const throttlePct: number[] = rawStream.throttle_percentage || [];
  const brakeArr: boolean[] = rawStream.brake || [];
  const xCoords: number[] = rawStream.x_m || [];
  const yCoords: number[] = rawStream.y_m || [];

  // Format Comparison Driver stream
  const compStream = compDriverData?.telemetry_stream || {};
  const compSpeedKph: number[] = compStream.speed_kph || [];
  const compThrottlePct: number[] = compStream.throttle_percentage || [];

  const streamData = timeSecs.map((t, idx) => ({
    time: Math.round((t || 0) * 10) / 10,
    dist: Math.round(distMeters[idx] || idx * 10),
    speed: Math.round(speedKph[idx] || 0),
    throttle: Math.round(throttlePct[idx] || 0),
    brake: brakeArr[idx] ? 100 : 0,
    compSpeed: compSpeedKph[idx] !== undefined ? Math.round(compSpeedKph[idx]) : undefined,
    compThrottle: compThrottlePct[idx] !== undefined ? Math.round(compThrottlePct[idx]) : undefined
  }));

  // Format lap timing data
  const rawLaps: any[] = telemetry.laps || [];
  const lapsData = rawLaps
    .map((l) => {
      const lapNum = l.LapNumber ?? l.lap_number ?? 0;
      const lapTime = l.LapTime ?? l.lap_time_seconds ?? 0;
      return {
        lap: `L${lapNum}`,
        lapNumber: Number(lapNum),
        time: typeof lapTime === 'number' ? Math.round(lapTime * 1000) / 1000 : 0
      };
    })
    .filter((l) => l.lapNumber > 0 && l.time > 0);

  const fastestLapNum = telemetry.fastest_lap_number;

  // 2D Track Geometry Calculation
  const hasTrackCoordinates = xCoords.length > 5 && yCoords.length > 5;
  let trackSegments: Array<{ x1: number; y1: number; x2: number; y2: number; speed: number }> = [];

  if (hasTrackCoordinates) {
    const minX = Math.min(...xCoords);
    const maxX = Math.max(...xCoords);
    const minY = Math.min(...yCoords);
    const maxY = Math.max(...yCoords);

    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    // Scale to SVG 500x320 with padding
    const scale = Math.min(420 / rangeX, 260 / rangeY);
    const offsetX = (500 - rangeX * scale) / 2;
    const offsetY = (320 - rangeY * scale) / 2;

    const scaledPoints = xCoords.map((x, i) => ({
      x: (x - minX) * scale + offsetX,
      y: 320 - ((yCoords[i] - minY) * scale + offsetY),
      speed: speedKph[i] || 200
    }));

    for (let i = 0; i < scaledPoints.length - 1; i++) {
      trackSegments.push({
        x1: scaledPoints[i].x,
        y1: scaledPoints[i].y,
        x2: scaledPoints[i + 1].x,
        y2: scaledPoints[i + 1].y,
        speed: (scaledPoints[i].speed + scaledPoints[i + 1].speed) / 2
      });
    }
  }

  const getSpeedColor = (spd: number) => {
    if (spd < 140) return '#ef4444'; // Heavy braking / slow corner (Red)
    if (spd < 240) return '#eab308'; // Medium speed apex (Yellow)
    return '#06b6d4'; // High speed straight (Cyan)
  };

  return (
    <div className="space-y-6 mb-6">
      {/* Telemetry Key Metric Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel rounded-xl p-4 border border-cyan-500/20">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-1">
            <span>MAX SPEED</span>
            <Gauge className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {telemetry.max_speed_kph !== undefined && telemetry.max_speed_kph !== null
              ? `${Math.round(telemetry.max_speed_kph)}`
              : 'N/A'}{' '}
            <span className="text-xs font-normal text-cyan-400">km/h</span>
          </div>
          {compDriverData && (
            <div className="text-[11px] text-amber-400 font-mono mt-0.5">
              VS {compDriverCode}: {compDriverData.max_speed_kph ? `${Math.round(compDriverData.max_speed_kph)} km/h` : 'N/A'}
            </div>
          )}
        </div>

        <div className="glass-panel rounded-xl p-4 border border-yellow-500/20">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-1">
            <span>FASTEST LAP</span>
            <Award className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {telemetry.fastest_lap_time_seconds
              ? `${Number(telemetry.fastest_lap_time_seconds).toFixed(3)}s`
              : 'N/A'}
          </div>
          {compDriverData ? (
            <div className="text-[11px] text-amber-400 font-mono mt-0.5">
              VS {compDriverCode}: {compDriverData.fastest_lap_time_seconds ? `${Number(compDriverData.fastest_lap_time_seconds).toFixed(3)}s` : 'N/A'}
            </div>
          ) : (
            fastestLapNum && <div className="text-[10px] text-yellow-400 font-mono mt-0.5">Lap {fastestLapNum}</div>
          )}
        </div>

        <div className="glass-panel rounded-xl p-4 border border-red-500/20">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-1">
            <span>AVG THROTTLE</span>
            <Flame className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {telemetry.avg_throttle_percentage !== undefined && telemetry.avg_throttle_percentage !== null
              ? `${telemetry.avg_throttle_percentage}%`
              : 'N/A'}
          </div>
          {compDriverData && (
            <div className="text-[11px] text-amber-400 font-mono mt-0.5">
              VS {compDriverCode}: {compDriverData.avg_throttle_percentage !== undefined ? `${compDriverData.avg_throttle_percentage}%` : 'N/A'}
            </div>
          )}
        </div>

        <div className="glass-panel rounded-xl p-4 border border-emerald-500/20">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-1">
            <span>BRAKING ZONES</span>
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {telemetry.braking_zones_count !== undefined && telemetry.braking_zones_count !== null
              ? `${telemetry.braking_zones_count}`
              : 'N/A'}{' '}
            <span className="text-xs font-normal text-emerald-400">zones</span>
          </div>
        </div>
      </div>

      {/* 2D Circuit Track Map Visualization */}
      {hasTrackCoordinates && (
        <div className="glass-panel rounded-2xl p-5 border border-cyan-500/30">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <Compass className="w-4 h-4 text-cyan-400" />
              <span>Interactive 2D Circuit Map & Spatial Speed Heatmap</span>
            </h3>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span> High Speed (&gt;240km/h)</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-400"></span> Mid Apex (140-240km/h)</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Heavy Braking (&lt;140km/h)</span>
            </div>
          </div>

          <div className="relative w-full h-80 bg-slate-950/80 rounded-xl overflow-hidden flex items-center justify-center border border-slate-800">
            <svg viewBox="0 0 500 320" className="w-full h-full p-2">
              <defs>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Background Track Glow */}
              {trackSegments.map((seg, idx) => (
                <line
                  key={`glow-${idx}`}
                  x1={seg.x1}
                  y1={seg.y1}
                  x2={seg.x2}
                  y2={seg.y2}
                  stroke={getSpeedColor(seg.speed)}
                  strokeWidth="8"
                  strokeOpacity="0.15"
                />
              ))}

              {/* Main Track Colored Speed Segments */}
              {trackSegments.map((seg, idx) => (
                <line
                  key={`seg-${idx}`}
                  x1={seg.x1}
                  y1={seg.y1}
                  x2={seg.x2}
                  y2={seg.y2}
                  stroke={getSpeedColor(seg.speed)}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                />
              ))}
            </svg>

            <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur px-3 py-1.5 rounded-lg border border-slate-700 text-[11px] font-mono text-slate-300">
              <span className="text-cyan-400 font-bold">{primaryDriver}</span> Spatial Track Telemetry
            </div>
          </div>
        </div>
      )}

      {/* Speed & Throttle Time-Series Overlay Chart (Supporting Comparison Driver) */}
      {streamData.length > 0 && (
        <div className="glass-panel rounded-2xl p-5 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <Zap className="w-4 h-4 text-cyan-400" />
              <span>
                Telemetry Stream {compDriverCode ? `Comparison: ${primaryDriver} vs ${compDriverCode}` : `(Speed & Throttle Profile)`}
              </span>
            </h3>
            {compDriverCode && (
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="text-cyan-400 font-bold flex items-center gap-1"><Users className="w-3 h-3" /> {primaryDriver} (Cyan)</span>
                <span className="text-amber-400 font-bold flex items-center gap-1"><Users className="w-3 h-3" /> {compDriverCode} (Amber)</span>
              </div>
            )}
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={streamData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="dist" stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: 'Distance (m)', position: 'insideBottomRight', offset: -5, fill: '#64748b', fontSize: 10 }} />
                <YAxis yAxisId="speed" stroke="#00e5ff" tick={{ fontSize: 10 }} domain={[0, 'auto']} />
                <YAxis yAxisId="throttle" orientation="right" stroke="#ff1801" tick={{ fontSize: 10 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  labelFormatter={(v) => `Distance: ${v}m`}
                />
                <Line yAxisId="speed" type="monotone" dataKey="speed" stroke="#00e5ff" strokeWidth={2} dot={false} name={`${primaryDriver} Speed (km/h)`} />
                {compDriverCode && (
                  <Line yAxisId="speed" type="monotone" dataKey="compSpeed" stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" dot={false} name={`${compDriverCode} Speed (km/h)`} />
                )}
                <Line yAxisId="throttle" type="monotone" dataKey="throttle" stroke="#ff1801" strokeWidth={1.2} dot={false} name={`${primaryDriver} Throttle (%)`} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Stint Lap Time Consistency Bar Chart */}
      {lapsData.length > 0 && (
        <div className="glass-panel rounded-2xl p-5 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Stint Lap Time Profile ({primaryDriver})</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">{lapsData.length} Total Laps Recorded</span>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lapsData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="lap" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 10 }} domain={['dataMin - 1', 'dataMax + 1']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val: any) => [val ? `${val}s` : 'N/A', 'Lap Time']}
                />
                <Bar dataKey="time" radius={[4, 4, 0, 0]}>
                  {lapsData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.lapNumber === fastestLapNum ? '#ffd700' : '#3b82f6'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
