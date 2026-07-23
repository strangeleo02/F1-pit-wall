'use client';

import React from 'react';
import { Calendar, MapPin, Flag, User, Send, Sparkles, SlidersHorizontal, Loader2 } from 'lucide-react';

export interface StrategyParams {
  year: number;
  grandPrix: string;
  sessionType: string;
  driverCode: string;
  comparisonDriverCode?: string;
  query: string;
}

export interface ScheduleEvent {
  round: number;
  event_name: string;
  location: string;
  country: string;
  search_key: string;
}

export interface DriverItem {
  code: string;
  name: string;
  team: string;
  number: string;
}

interface ControlsPanelProps {
  params: StrategyParams;
  onChange: (updated: Partial<StrategyParams>) => void;
  onSubmit: () => void;
  loading: boolean;
  scheduleEvents: ScheduleEvent[];
  driverLineup: DriverItem[];
  loadingSchedule: boolean;
  loadingDrivers: boolean;
}

const YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018];

const SESSIONS = [
  { id: 'R', label: 'Race' },
  { id: 'Q', label: 'Qualifying' },
  { id: 'FP1', label: 'Practice 1' },
  { id: 'FP2', label: 'Practice 2' },
  { id: 'FP3', label: 'Practice 3' }
];

const PRESETS = [
  'Why did Max complain about tire degradation on laps 15 to 20?',
  'Compare Hamilton lap times and speed profile vs Verstappen at Monza',
  'Analyze driver pace delta and braking efficiency',
  'Summarize driver team radio feedback during safety car restart'
];

export const ControlsPanel: React.FC<ControlsPanelProps> = ({
  params,
  onChange,
  onSubmit,
  loading,
  scheduleEvents,
  driverLineup,
  loadingSchedule,
  loadingDrivers
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 mb-6 border border-white/10 shadow-2xl">
      <div className="flex items-center justify-between gap-2 mb-4 text-xs font-mono uppercase tracking-widest text-slate-400">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-red-500" />
          <span>Dynamic PitWall Strategy Parameters</span>
        </div>
        <span className="text-[11px] text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">
          ⚡ Multi-Driver Compare & SSE Stream Ready
        </span>
      </div>

      {/* Selectors Row (5 Grid Columns) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3.5 mb-5">
        {/* Year */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-red-400" />
            <span>Season Year</span>
          </label>
          <select
            value={params.year}
            onChange={(e) => onChange({ year: parseInt(e.target.value, 10) })}
            className="w-full bg-slate-900/90 border border-slate-700/70 rounded-xl px-2.5 py-2 text-xs text-slate-100 focus:outline-none focus:border-red-500 font-mono"
          >
            {YEARS.map((y) => (
              <option key={y} value={y}>
                {y} Season
              </option>
            ))}
          </select>
        </div>

        {/* Dynamic Grand Prix Calendar */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              <span>Official F1 Calendar</span>
            </span>
            {loadingSchedule && <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />}
          </label>
          <select
            value={params.grandPrix}
            onChange={(e) => onChange({ grandPrix: e.target.value })}
            disabled={loadingSchedule || scheduleEvents.length === 0}
            className="w-full bg-slate-900/90 border border-slate-700/70 rounded-xl px-2.5 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono disabled:opacity-60"
          >
            {scheduleEvents.length > 0 ? (
              scheduleEvents.map((ev) => (
                <option key={`${ev.round}-${ev.search_key}`} value={ev.search_key || ev.location}>
                  R{ev.round}: {ev.event_name} ({ev.location})
                </option>
              ))
            ) : (
              <option value={params.grandPrix}>{params.grandPrix}</option>
            )}
          </select>
        </div>

        {/* Session Type */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Flag className="w-3.5 h-3.5 text-emerald-400" />
            <span>Session</span>
          </label>
          <select
            value={params.sessionType}
            onChange={(e) => onChange({ sessionType: e.target.value })}
            className="w-full bg-slate-900/90 border border-slate-700/70 rounded-xl px-2.5 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          >
            {SESSIONS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label} ({s.id})
              </option>
            ))}
          </select>
        </div>

        {/* Primary Driver */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-purple-400" />
              <span>Primary Driver</span>
            </span>
            {loadingDrivers && <Loader2 className="w-3 h-3 text-purple-400 animate-spin" />}
          </label>
          <select
            value={params.driverCode}
            onChange={(e) => onChange({ driverCode: e.target.value })}
            disabled={loadingDrivers}
            className="w-full bg-slate-900/90 border border-slate-700/70 rounded-xl px-2.5 py-2 text-xs text-slate-100 focus:outline-none focus:border-purple-500 font-mono font-bold disabled:opacity-60"
          >
            {driverLineup.length > 0 ? (
              driverLineup.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.code} - {d.name}
                </option>
              ))
            ) : (
              <option value={params.driverCode}>{params.driverCode}</option>
            )}
          </select>
        </div>

        {/* Comparison Driver */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-amber-400" />
              <span>VS Driver (Compare)</span>
            </span>
          </label>
          <select
            value={params.comparisonDriverCode || ''}
            onChange={(e) => onChange({ comparisonDriverCode: e.target.value || undefined })}
            disabled={loadingDrivers}
            className="w-full bg-slate-900/90 border border-slate-700/70 rounded-xl px-2.5 py-2 text-xs text-slate-100 focus:outline-none focus:border-amber-500 font-mono font-bold disabled:opacity-60"
          >
            <option value="">None (Single Driver)</option>
            {driverLineup
              .filter((d) => d.code !== params.driverCode)
              .map((d) => (
                <option key={`comp-${d.code}`} value={d.code}>
                  VS {d.code} - {d.name}
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Query Bar */}
      <div className="relative mb-4">
        <input
          type="text"
          value={params.query}
          onChange={(e) => onChange({ query: e.target.value })}
          onKeyDown={handleKeyDown}
          placeholder="Ask PitWall AI a race strategy, telemetry, or radio query..."
          className="w-full bg-slate-900/90 border border-red-500/30 rounded-xl pl-4 pr-32 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all font-sans"
        />
        <button
          onClick={onSubmit}
          disabled={loading || !params.query.trim()}
          className="absolute right-2 top-2 bottom-2 px-5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(255,24,1,0.4)]"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing</span>
            </>
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
              <span>Execute</span>
            </>
          )}
        </button>
      </div>

      {/* Preset Suggestion Chips */}
      <div className="flex items-center gap-2 flex-wrap text-xs">
        <span className="text-slate-500 font-mono flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-red-400" /> Quick Queries:
        </span>
        {PRESETS.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => onChange({ query: preset })}
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/60 text-slate-300 transition-all text-[11px] truncate max-w-xs"
          >
            {preset}
          </button>
        ))}
      </div>
    </div>
  );
};
