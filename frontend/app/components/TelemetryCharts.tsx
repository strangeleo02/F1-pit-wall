'use client';

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
  ReferenceLine,
  Brush
} from 'recharts';
import { Activity, Gauge, Zap, Flame, Award, Users, Layers, Cpu, Maximize2, Minimize2, ZoomIn, X } from 'lucide-react';
import { SectorMatrixCard } from './SectorMatrixCard';

interface TelemetryChartsProps {
  telemetry: any;
  onHoverDistancePctChange?: (distPct: number | null) => void;
}

export const TelemetryCharts: React.FC<TelemetryChartsProps> = ({ telemetry, onHoverDistancePctChange }) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [sectorFilter, setSectorFilter] = useState<'ALL' | 'S1' | 'S2' | 'S3'>('ALL');

  if (!telemetry || typeof telemetry !== 'object' || Object.keys(telemetry).length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-8 mb-6 text-center text-slate-500 font-mono text-xs border border-white/10">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-30 text-cyan-400 animate-pulse" />
        <p>No Telemetry Stream Data Available For Current Query</p>
        <p className="text-[11px] text-slate-600 mt-1">Execute a strategy query to stream high-frequency telemetry.</p>
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
  const rawGears: number[] = rawStream.n_gear || rawStream.gear || [];
  const rawDrs: number[] = rawStream.drs || [];

  // Format Comparison Driver stream
  const compStream = compDriverData?.telemetry_stream || {};
  const compSpeedKph: number[] = compStream.speed_kph || [];
  const compThrottlePct: number[] = compStream.throttle_percentage || [];
  const compBrakeArr: boolean[] = compStream.brake || [];
  const compGears: number[] = compStream.n_gear || compStream.gear || [];

  const maxDist = distMeters.length > 0 ? Math.max(...distMeters) : 5000;

  // Helper to estimate gear from speed if missing
  const getGear = (speed: number, idx: number, gearArr?: number[]) => {
    if (gearArr && gearArr[idx] !== undefined && gearArr[idx] > 0) return gearArr[idx];
    if (speed < 80) return 1;
    if (speed < 120) return 2;
    if (speed < 160) return 3;
    if (speed < 200) return 4;
    if (speed < 240) return 5;
    if (speed < 280) return 6;
    if (speed < 310) return 7;
    return 8;
  };

  // Helper to estimate DRS state if missing
  const getDrs = (speed: number, throttle: number, idx: number) => {
    if (rawDrs[idx] !== undefined) return rawDrs[idx] > 8 ? 100 : 0;
    return speed > 270 && throttle > 90 ? 100 : 0;
  };

  const allStreamData = timeSecs.map((t, idx) => {
    const spd = Math.round(speedKph[idx] || 0);
    const throt = Math.round(throttlePct[idx] || 0);
    const cSpd = compSpeedKph[idx] !== undefined ? Math.round(compSpeedKph[idx]) : undefined;
    const cThrot = compThrottlePct[idx] !== undefined ? Math.round(compThrottlePct[idx]) : undefined;
    const cBrake = compBrakeArr[idx] !== undefined ? (compBrakeArr[idx] ? 100 : 0) : undefined;
    const cGear = compSpeedKph[idx] !== undefined ? getGear(compSpeedKph[idx], idx, compGears) : undefined;
    const delta = cSpd !== undefined ? Math.round((spd - cSpd) * 10) / 10 : undefined;
    const dVal = Math.round(distMeters[idx] || idx * 10);

    return {
      index: idx,
      time: Math.round((t || 0) * 10) / 10,
      dist: dVal,
      speed: spd,
      throttle: throt,
      brake: brakeArr[idx] ? 100 : 0,
      gear: getGear(spd, idx, rawGears),
      drs: getDrs(spd, throt, idx),
      compSpeed: cSpd,
      compThrottle: cThrot,
      compBrake: cBrake,
      compGear: cGear,
      deltaSpeed: delta
    };
  });

  // Filter dataset by Sector if selected
  const streamData = allStreamData.filter((d) => {
    if (sectorFilter === 'S1') return d.dist <= maxDist * 0.33;
    if (sectorFilter === 'S2') return d.dist > maxDist * 0.33 && d.dist <= maxDist * 0.66;
    if (sectorFilter === 'S3') return d.dist > maxDist * 0.66;
    return true;
  });

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

  // Propagate hover callback to parent & CircuitMap
  const handleChartHover = (idx: number | null) => {
    setHoverIndex(idx);
    if (onHoverDistancePctChange) {
      if (idx !== null && streamData.length > 0) {
        const pct = (idx / Math.max(1, streamData.length - 1)) * 100;
        onHoverDistancePctChange(pct);
      } else {
        onHoverDistancePctChange(null);
      }
    }
  };

  const activeHoverData = hoverIndex !== null && streamData[hoverIndex] ? streamData[hoverIndex] : null;

  return (
    <div className="space-y-6 mb-6">
      {/* Telemetry Key Metric Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel rounded-xl p-4 border border-cyan-500/20 shadow-lg">
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

        <div className="glass-panel rounded-xl p-4 border border-yellow-500/20 shadow-lg">
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

        <div className="glass-panel rounded-xl p-4 border border-red-500/20 shadow-lg">
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

        <div className="glass-panel rounded-xl p-4 border border-emerald-500/20 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-1">
            <span>DRIVER COMPARISON</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-black text-white font-mono flex items-center gap-1">
            <span className="text-cyan-400">{primaryDriver}</span>
            {compDriverCode && <span className="text-slate-400 font-normal">vs <strong className="text-amber-400">{compDriverCode}</strong></span>}
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-0.5">Synchronized Multi-Trace</div>
        </div>
      </div>

      {/* Sector Pace Matrix */}
      <SectorMatrixCard telemetry={telemetry} />

      {/* Main Console Box */}
      {streamData.length > 0 && (
        <div className={`glass-panel rounded-2xl p-5 border border-white/10 space-y-5 transition-all ${
          isFullscreen ? "fixed inset-2 z-50 bg-[#0b0f17]/98 overflow-y-auto border-cyan-500/50 shadow-2xl p-8" : ""
        }`}>
          {/* Console Header with Sector Zoom Controls & Fullscreen Button */}
          <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-wrap gap-2">
            <div className="flex items-center space-x-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide">
                <Layers className="w-4 h-4 text-red-500" />
                <span>Multi-Trace Synchronized Driver Comparison Console</span>
              </h3>
              {isFullscreen && <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 font-mono text-[10px] rounded border border-cyan-500/40">MAGNIFIED FULLSCREEN VIEW</span>}
            </div>

            <div className="flex items-center space-x-3 flex-wrap gap-2">
              {/* Sector Zoom Selector */}
              <div className="flex items-center space-x-1 bg-slate-900/90 p-0.5 rounded-lg border border-slate-800 text-xs font-mono">
                <span className="text-[10px] text-slate-400 px-1.5 flex items-center gap-1"><ZoomIn className="w-3 h-3 text-cyan-400" /> Zoom:</span>
                {(['ALL', 'S1', 'S2', 'S3'] as const).map((sec) => (
                  <button
                    key={sec}
                    onClick={() => setSectorFilter(sec)}
                    className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all ${
                      sectorFilter === sec
                        ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/50'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {sec === 'ALL' ? 'Full Lap' : sec}
                  </button>
                ))}
              </div>

              {/* Fullscreen Magnify Button */}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="flex items-center space-x-1 px-3 py-1 bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-500/40 rounded-lg text-xs font-mono font-bold transition-all shadow-md"
              >
                {isFullscreen ? (
                  <>
                    <X className="w-3.5 h-3.5" /> <span>Close Magnifier</span>
                  </>
                ) : (
                  <>
                    <Maximize2 className="w-3.5 h-3.5 text-cyan-400" /> <span>Magnify Graph</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Legend readout */}
          <div className="flex items-center justify-between text-xs font-mono pt-1 text-slate-400 flex-wrap gap-2">
            <div className="flex items-center gap-4">
              <span className="text-cyan-400 font-bold flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block" /> {primaryDriver} (Primary Solid Line)
              </span>
              {compDriverCode && (
                <span className="text-amber-400 font-bold flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" /> {compDriverCode} (Comparison Dashed Line)
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400">
              Drag bottom slider or select S1/S2/S3 to magnify corner entries.
            </div>
          </div>

          {/* Trace 1: Speed Comparison (km/h) */}
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between text-xs font-mono mb-2 text-slate-400">
              <span className="text-cyan-400 font-bold flex items-center gap-1.5 tracking-wider">
                <Zap className="w-3.5 h-3.5" /> TRACE 1: Speed Profile (km/h)
              </span>
              {activeHoverData && (
                <div className="flex items-center gap-3 text-xs font-mono bg-slate-900 px-3 py-1 rounded border border-slate-800">
                  <span className="text-cyan-400">{primaryDriver}: <strong className="text-white">{activeHoverData.speed} km/h</strong></span>
                  {compDriverCode && activeHoverData.compSpeed !== undefined && (
                    <span className="text-amber-400">{compDriverCode}: <strong className="text-white">{activeHoverData.compSpeed} km/h</strong></span>
                  )}
                  {activeHoverData.deltaSpeed !== undefined && (
                    <span className={`font-bold ${activeHoverData.deltaSpeed >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      Delta: {activeHoverData.deltaSpeed >= 0 ? `+${activeHoverData.deltaSpeed}` : activeHoverData.deltaSpeed} km/h
                    </span>
                  )}
                </div>
              )}
            </div>
            <div className={isFullscreen ? "h-64 w-full" : "h-40 w-full"}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={streamData}
                  margin={{ top: 5, right: 15, left: 10, bottom: 5 }}
                  onMouseMove={(e: any) => {
                    if (e && e.activeTooltipIndex !== undefined) handleChartHover(e.activeTooltipIndex);
                  }}
                  onMouseLeave={() => handleChartHover(null)}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis
                    dataKey="dist"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    stroke="#475569"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}km` : `${Math.round(val)}m`)}
                    label={{ value: 'Lap Distance (Meters)', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <YAxis
                    stroke="#27f4d2"
                    tick={{ fontSize: 10 }}
                    domain={[0, 'auto']}
                    label={{ value: 'Speed (km/h)', angle: -90, position: 'insideLeft', offset: 10, fill: '#27f4d2', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                    formatter={(val: any, name: any) => [`${val} km/h`, String(name || "")]}
                    labelFormatter={(label: any) => `Distance: ${Math.round(label)} m`}
                  />
                  <Line type="monotone" dataKey="speed" stroke="#27f4d2" strokeWidth={2.5} dot={false} name={`${primaryDriver} Speed`} />
                  {compDriverCode && (
                    <Line type="monotone" dataKey="compSpeed" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} name={`${compDriverCode} Speed`} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trace 2: Throttle % & Brake Comparison */}
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between text-xs font-mono mb-2 text-slate-400">
              <span className="text-red-400 font-bold flex items-center gap-1.5 tracking-wider">
                <Flame className="w-3.5 h-3.5" /> TRACE 2: Throttle Application (%) & Braking Zones
              </span>
              {activeHoverData && (
                <div className="flex items-center gap-3 text-xs font-mono bg-slate-900 px-3 py-1 rounded border border-slate-800">
                  <span className="text-cyan-400">{primaryDriver}: <strong className="text-white">Throttle {activeHoverData.throttle}% | Brake {activeHoverData.brake > 0 ? 'ON' : 'OFF'}</strong></span>
                  {compDriverCode && activeHoverData.compThrottle !== undefined && (
                    <span className="text-amber-400">{compDriverCode}: <strong className="text-white">Throttle {activeHoverData.compThrottle}% | Brake {(activeHoverData.compBrake ?? 0) > 0 ? 'ON' : 'OFF'}</strong></span>
                  )}
                </div>
              )}
            </div>
            <div className={isFullscreen ? "h-56 w-full" : "h-36 w-full"}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={streamData}
                  margin={{ top: 5, right: 15, left: 10, bottom: 5 }}
                  onMouseMove={(e: any) => {
                    if (e && e.activeTooltipIndex !== undefined) handleChartHover(e.activeTooltipIndex);
                  }}
                  onMouseLeave={() => handleChartHover(null)}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis
                    dataKey="dist"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    stroke="#475569"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}km` : `${Math.round(val)}m`)}
                    label={{ value: 'Lap Distance (Meters)', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <YAxis
                    stroke="#ef4444"
                    tick={{ fontSize: 10 }}
                    domain={[0, 100]}
                    label={{ value: 'Pedal Input (%)', angle: -90, position: 'insideLeft', offset: 10, fill: '#ef4444', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                    formatter={(val: any, name: any) => [`${val}%`, String(name || "")]}
                    labelFormatter={(label: any) => `Distance: ${Math.round(label)} m`}
                  />
                  <Line type="monotone" dataKey="throttle" stroke="#27f4d2" strokeWidth={2} dot={false} name={`${primaryDriver} Throttle`} />
                  <Line type="stepAfter" dataKey="brake" stroke="#ef4444" strokeWidth={2} dot={false} name={`${primaryDriver} Brake`} />
                  {compDriverCode && (
                    <Line type="monotone" dataKey="compThrottle" stroke="#f59e0b" strokeWidth={1.8} strokeDasharray="4 4" dot={false} name={`${compDriverCode} Throttle`} />
                  )}
                  {compDriverCode && (
                    <Line type="stepAfter" dataKey="compBrake" stroke="#f97316" strokeWidth={1.8} strokeDasharray="3 3" dot={false} name={`${compDriverCode} Brake`} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trace 3: Gear Selection & DRS Status */}
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between text-xs font-mono mb-2 text-slate-400">
              <span className="text-purple-400 font-bold flex items-center gap-1.5 tracking-wider">
                <Cpu className="w-3.5 h-3.5" /> TRACE 3: Gear Selection (1-8) & DRS Activation
              </span>
              {activeHoverData && (
                <div className="flex items-center gap-3 text-xs font-mono bg-slate-900 px-3 py-1 rounded border border-slate-800">
                  <span className="text-cyan-400">{primaryDriver}: <strong className="text-white">Gear {activeHoverData.gear} | DRS {activeHoverData.drs > 0 ? 'ON' : 'OFF'}</strong></span>
                  {compDriverCode && activeHoverData.compGear !== undefined && (
                    <span className="text-amber-400">{compDriverCode}: <strong className="text-white">Gear {activeHoverData.compGear}</strong></span>
                  )}
                </div>
              )}
            </div>
            <div className={isFullscreen ? "h-48 w-full" : "h-32 w-full"}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={streamData}
                  margin={{ top: 5, right: 15, left: 10, bottom: 5 }}
                  onMouseMove={(e: any) => {
                    if (e && e.activeTooltipIndex !== undefined) handleChartHover(e.activeTooltipIndex);
                  }}
                  onMouseLeave={() => handleChartHover(null)}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis
                    dataKey="dist"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    stroke="#475569"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}km` : `${Math.round(val)}m`)}
                    label={{ value: 'Lap Distance (Meters)', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <YAxis
                    stroke="#a855f7"
                    tick={{ fontSize: 10 }}
                    domain={[1, 8]}
                    label={{ value: 'Gear Ratio', angle: -90, position: 'insideLeft', offset: 10, fill: '#a855f7', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                    formatter={(val: any, name: any) => [val, String(name || "")]}
                    labelFormatter={(label: any) => `Distance: ${Math.round(label)} m`}
                  />
                  <Line type="stepAfter" dataKey="gear" stroke="#27f4d2" strokeWidth={2} dot={false} name={`${primaryDriver} Gear`} />
                  {compDriverCode && (
                    <Line type="stepAfter" dataKey="compGear" stroke="#f59e0b" strokeWidth={1.8} strokeDasharray="4 4" dot={false} name={`${compDriverCode} Gear`} />
                  )}
                  <Line type="stepAfter" dataKey="drs" stroke="#38bdf8" strokeWidth={2} dot={false} name="DRS Zone Active" />
                  <Brush dataKey="dist" height={20} stroke="#334155" fill="#0f172a" tickFormatter={(v) => `${Math.round(v)}m`} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trace 4: Speed Delta Comparison */}
          {compDriverCode && (
            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-xs font-mono mb-2 text-slate-400">
                <span className="text-amber-400 font-bold flex items-center gap-1.5 tracking-wider">
                  <Users className="w-3.5 h-3.5" /> TRACE 4: Speed Delta Gap ({primaryDriver} vs {compDriverCode})
                </span>
                {activeHoverData && activeHoverData.deltaSpeed !== undefined && (
                  <span className={`font-bold text-xs font-mono px-2 py-0.5 rounded border bg-slate-900 ${
                    activeHoverData.deltaSpeed >= 0 ? 'text-emerald-400 border-emerald-500/40' : 'text-rose-400 border-rose-500/40'
                  }`}>
                    Delta: {activeHoverData.deltaSpeed >= 0 ? `+${activeHoverData.deltaSpeed}` : activeHoverData.deltaSpeed} km/h
                  </span>
                )}
              </div>
              <div className={isFullscreen ? "h-40 w-full" : "h-28 w-full"}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={streamData}
                    margin={{ top: 5, right: 15, left: 10, bottom: 5 }}
                    onMouseMove={(e: any) => {
                      if (e && e.activeTooltipIndex !== undefined) handleChartHover(e.activeTooltipIndex);
                    }}
                    onMouseLeave={() => handleChartHover(null)}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis
                      dataKey="dist"
                      type="number"
                      domain={['dataMin', 'dataMax']}
                      stroke="#475569"
                      tick={{ fontSize: 10 }}
                      tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}km` : `${Math.round(val)}m`)}
                      label={{ value: 'Lap Distance (Meters)', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                    />
                    <YAxis
                      stroke="#f59e0b"
                      tick={{ fontSize: 10 }}
                      label={{ value: 'Speed Delta (km/h)', angle: -90, position: 'insideLeft', offset: 10, fill: '#f59e0b', fontSize: 10, fontFamily: 'monospace' }}
                    />
                    <ReferenceLine y={0} stroke="#64748b" strokeDasharray="3 3" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                      formatter={(val: any) => [`${val} km/h`, `Speed Delta (${primaryDriver} - ${compDriverCode})`]}
                    />
                    <Line type="monotone" dataKey="deltaSpeed" stroke="#f59e0b" strokeWidth={2} dot={false} name={`Delta (${primaryDriver} - ${compDriverCode})`} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stint Lap Time Consistency Bar Chart */}
      {lapsData.length > 0 && (
        <div className="glass-panel rounded-2xl p-5 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Stint Lap Time Profile ({primaryDriver})</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">{lapsData.length} Total Laps Recorded</span>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lapsData} margin={{ top: 5, right: 15, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="lap" stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: 'Stint Lap Number', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 10 }} domain={['dataMin - 1', 'dataMax + 1']} label={{ value: 'Lap Time (Seconds)', angle: -90, position: 'insideLeft', offset: 10, fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px', fontFamily: 'monospace' }}
                  formatter={(val: any) => [val ? `${val}s` : 'N/A', 'Lap Time']}
                />
                <Bar dataKey="time" radius={[4, 4, 0, 0]}>
                  {lapsData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.lapNumber === fastestLapNum ? '#eab308' : '#27f4d2'}
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
