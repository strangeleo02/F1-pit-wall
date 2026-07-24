"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import { Sliders, Flame, Gauge, CloudRain, CheckCircle2, XCircle, Activity, HeartPulse, Flag, Thermometer, Maximize2, X } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Brush } from "recharts";
import { API_BASE_URL } from "../config";

interface UndercutSimulatorProps {
  primaryDriver?: string;
  comparisonDriver?: string;
  grandPrix?: string;
  year?: number;
  /** Pass already-fetched weather from parent to avoid a duplicate API call */
  sessionWeatherProp?: any;
}

export const UndercutSimulator: React.FC<UndercutSimulatorProps> = ({
  primaryDriver = "VER",
  comparisonDriver = "HAM",
  grandPrix = "Monza",
  year = 2024,
  sessionWeatherProp
}) => {
  // Input Controls State
  const [targetDriver, setTargetDriver] = useState<string>(primaryDriver);
  const [rivalDriver, setRivalDriver] = useState<string>(comparisonDriver);
  const [currentLap, setCurrentLap] = useState<number>(15);
  const [targetPitLap, setTargetPitLap] = useState<number>(18);
  const [initialGap, setInitialGap] = useState<number>(1.8);
  const [pitDuration, setPitDuration] = useState<number>(2.4);
  const [targetNewTyre, setTargetNewTyre] = useState<string>("HARD");
  const [trackTemp, setTrackTemp] = useState<number>(38);
  const [rainIntensity, setRainIntensity] = useState<number>(0.0);
  const [chartMode, setChartMode] = useState<"pace" | "health">("pace");
  const [isChartMagnified, setIsChartMagnified] = useState<boolean>(false);

  // API Fetched Session Info State
  const [sessionWeather, setSessionWeather] = useState<any>(null);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [tyreDegData, setTyreDegData] = useState<any>(null);
  const [crossoverData, setCrossoverData] = useState<any>(null);

  const API_BASE = API_BASE_URL;

  // Sync drivers when props update
  useEffect(() => {
    if (primaryDriver) setTargetDriver(primaryDriver);
    if (comparisonDriver) setRivalDriver(comparisonDriver);
  }, [primaryDriver, comparisonDriver]);

  // 1. Use weather from parent prop if available, otherwise fetch once per (year, grandPrix)
  useEffect(() => {
    if (sessionWeatherProp) {
      // Reuse already-fetched data from page.tsx — no extra API call
      setSessionWeather(sessionWeatherProp);
      if (sessionWeatherProp.track_temp_celsius) setTrackTemp(sessionWeatherProp.track_temp_celsius);
      if (sessionWeatherProp.rainfall_intensity_mm_per_min !== undefined)
        setRainIntensity(sessionWeatherProp.rainfall_intensity_mm_per_min);
      return;
    }

    // Fallback: fetch directly only if prop not provided
    let isMounted = true;
    fetch(`${API_BASE}/api/v1/simulation/session-weather?year=${year}&grand_prix=${encodeURIComponent(grandPrix)}&session_type=Race`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data) {
          setSessionWeather(data);
          if (data.track_temp_celsius) setTrackTemp(data.track_temp_celsius);
          if (data.rainfall_intensity_mm_per_min !== undefined) setRainIntensity(data.rainfall_intensity_mm_per_min);
        }
      })
      .catch((err) => console.warn("Session weather API fetch warning:", err));
    return () => { isMounted = false; };
  }, [year, grandPrix, sessionWeatherProp]);

  // 2. Run Undercut Simulation & Tyre Deg — debounced 500ms to prevent API flood on slider drag
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Cancel any pending debounced call
    if (debounceRef.current) clearTimeout(debounceRef.current);

    let isMounted = true;

    debounceRef.current = setTimeout(() => {
      if (!isMounted) return;

      // Run Undercut Simulation
      fetch(`${API_BASE}/api/v1/simulation/undercut`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_driver: targetDriver,
          rival_driver: rivalDriver,
          grand_prix: grandPrix,
          current_lap: currentLap,
          target_pit_lap: targetPitLap,
          initial_gap_sec: initialGap,
          stationary_pit_duration: pitDuration,
          target_new_tyre: targetNewTyre,
          track_temp_celsius: trackTemp
        })
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => { if (isMounted && data) setSimulationResult(data); })
        .catch((err) => console.warn("Undercut sim error:", err));

      // Tyre Degradation Curves (SOFT, MEDIUM, HARD)
      fetch(
        `${API_BASE}/api/v1/simulation/tyre-deg?compound=${encodeURIComponent(targetNewTyre)}&grand_prix=${encodeURIComponent(grandPrix)}&stint_laps=30&track_temp_celsius=${trackTemp}`
      )
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => { if (isMounted && data) setTyreDegData(data); })
        .catch(() => {});

      // Weather Crossover Analysis
      fetch(
        `${API_BASE}/api/v1/simulation/crossover?rainfall_mm_per_min=${rainIntensity}&track_temp_celsius=${trackTemp}`
      )
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => { if (isMounted && data) setCrossoverData(data); })
        .catch(() => {});

    }, 500); // 500ms debounce — waits until slider stops moving

    return () => {
      isMounted = false;
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [
    targetDriver,
    rivalDriver,
    grandPrix,
    year,
    currentLap,
    targetPitLap,
    initialGap,
    pitDuration,
    targetNewTyre,
    trackTemp,
    rainIntensity
  ]);

  const isSuccess = simulationResult?.is_successful_undercut;
  const projectedGap = simulationResult?.projected_gap_after_pits_sec || 0;
  const circuitProfile = tyreDegData?.circuit_profile || simulationResult?.circuit_profile;
  const totalRaceLaps = sessionWeather?.total_laps || circuitProfile?.total_laps || 57;

  // Chart data source (multi-compound SOFT, MEDIUM, HARD comparison)
  const chartData = useMemo(() => {
    return tyreDegData?.multi_compound_comparison || [];
  }, [tyreDegData]);

  return (
    <div className="bg-[#12161F]/95 border border-slate-800 rounded-2xl p-5 shadow-2xl backdrop-blur-md space-y-6">
      {/* Header Title Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide font-mono">
            {year} {grandPrix} GP Strategy & Tyre Degradation Simulator
          </h3>
        </div>

        {/* API Session & Weather Badges */}
        <div className="flex items-center space-x-2 flex-wrap gap-2">
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
            <Flag className="w-3.5 h-3.5 text-cyan-400" />
            <span>Race Distance: {totalRaceLaps} Laps</span>
          </div>

          {sessionWeather && (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
              <Thermometer className="w-3.5 h-3.5" />
              <span>Track Temp: {sessionWeather.track_temp_celsius}°C</span>
            </div>
          )}

          {crossoverData && (
            <div
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold ${
                crossoverData.recommended_compound === "DRY_SLICK"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  : crossoverData.recommended_compound === "INTERMEDIATE"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "bg-blue-500/20 text-blue-300 border border-blue-500/40"
              }`}
            >
              <CloudRain className="w-3.5 h-3.5" />
              <span>Track: {crossoverData.crossover_state}</span>
            </div>
          )}
        </div>
      </div>

      {/* Grid Layout: Controls & Strategy Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Column 1: Interactive Strategy Controls (4 cols) */}
        <div className="lg:col-span-4 bg-slate-950/80 rounded-xl p-4 border border-slate-800 space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="text-xs font-bold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Pit Strategy Controls
            </h4>
            {sessionWeather?.api_source && (
              <span className="text-[10px] font-mono text-cyan-400/80 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {sessionWeather.api_source}
              </span>
            )}
          </div>

          {/* Current Lap Slider */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Current Race Lap:</span>
              <strong className="text-slate-200 font-bold">Lap {currentLap} / {totalRaceLaps}</strong>
            </div>
            <input
              type="range"
              min={1}
              max={totalRaceLaps - 5}
              value={currentLap}
              onChange={(e) => {
                const newLap = Number(e.target.value);
                setCurrentLap(newLap);
                if (targetPitLap <= newLap) setTargetPitLap(newLap + 3);
              }}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-slate-400"
            />
          </div>

          {/* Target Pit Lap Slider */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Target Pit Lap:</span>
              <strong className="text-cyan-400 font-bold">Lap {targetPitLap} / {totalRaceLaps}</strong>
            </div>
            <input
              type="range"
              min={currentLap + 1}
              max={Math.min(totalRaceLaps, currentLap + 25)}
              value={targetPitLap}
              onChange={(e) => setTargetPitLap(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
          </div>

          {/* Initial Gap Input */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Initial Gap ({targetDriver} trailing {rivalDriver}):</span>
              <strong className="text-amber-400 font-bold">+{initialGap.toFixed(1)}s</strong>
            </div>
            <input
              type="range"
              min={0.2}
              max={10.0}
              step={0.1}
              value={initialGap}
              onChange={(e) => setInitialGap(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
            />
          </div>

          {/* Pit Stop Duration Slider */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Pit Stop Duration:</span>
              <strong className="text-purple-400 font-bold">{pitDuration.toFixed(1)}s</strong>
            </div>
            <input
              type="range"
              min={1.8}
              max={6.0}
              step={0.1}
              value={pitDuration}
              onChange={(e) => setPitDuration(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"
            />
          </div>

          {/* New Compound Selector */}
          <div className="space-y-1.5 pt-1">
            <label className="text-xs font-mono text-slate-300 block font-semibold">New Tyre Compound:</label>
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              {[
                { name: "SOFT", color: "bg-red-500/20 text-red-400 border-red-500/50" },
                { name: "MEDIUM", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50" },
                { name: "HARD", color: "bg-slate-200/20 text-cyan-300 border-cyan-400/50" }
              ].map((c) => (
                <button
                  key={c.name}
                  onClick={() => setTargetNewTyre(c.name)}
                  className={`py-2 px-2 rounded-lg font-bold border transition-all text-center ${
                    targetNewTyre === c.name ? `${c.color} shadow-lg ring-1 ring-white/20` : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>
          </div>

          {/* Real Weather Parameters */}
          <div className="pt-3 border-t border-slate-800/80 space-y-3">
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>Session Track Temperature:</span>
                <span className="text-red-400 font-bold">{trackTemp}°C</span>
              </div>
              <input
                type="range"
                min={20}
                max={55}
                value={trackTemp}
                onChange={(e) => setTrackTemp(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-red-500"
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>Live Rainfall Intensity:</span>
                <span className="text-blue-400 font-bold">{rainIntensity} mm/min</span>
              </div>
              <input
                type="range"
                min={0.0}
                max={5.0}
                step={0.1}
                value={rainIntensity}
                onChange={(e) => setRainIntensity(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-400"
              />
            </div>
          </div>
        </div>

        {/* Column 2: Undercut Outcome Banner & Recommendation Matrix (8 cols) */}
        <div className="lg:col-span-8 space-y-5 flex flex-col justify-between">
          {/* Outcome Gauge Card */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
              isSuccess
                ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                : "bg-rose-950/40 border-rose-500/40 text-rose-300"
            }`}
          >
            <div className="flex items-center space-x-3.5">
              {isSuccess ? (
                <CheckCircle2 className="w-9 h-9 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-9 h-9 text-rose-400 shrink-0" />
              )}
              <div>
                <div className="text-xs font-mono uppercase tracking-wider font-bold opacity-80">
                  {isSuccess ? "Undercut Advantage Projected" : "Overcut Deficit Warning"}
                </div>
                <div className="text-xl font-black font-mono tracking-tight">
                  {isSuccess
                    ? `-${Math.abs(projectedGap).toFixed(2)}s Track Lead Projected`
                    : `+${projectedGap.toFixed(2)}s Track Deficit Projected`}
                </div>
                <div className="text-xs font-mono mt-0.5 opacity-90">
                  {simulationResult?.outcome_summary}
                </div>
              </div>
            </div>

            <div className="text-right hidden sm:block font-mono">
              <div className="text-[10px] text-slate-400 uppercase">Target Pit Window</div>
              <div className="text-base font-bold text-cyan-400">Lap {targetPitLap} / {totalRaceLaps}</div>
            </div>
          </div>

          {/* Pit Window Recommendation Pills */}
          <div>
            <span className="text-xs font-mono text-slate-300 font-bold block mb-2">
              Candidate Pit Window Success Probabilities ({year} {grandPrix}):
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-xs font-mono">
              {simulationResult?.pit_window_recommendations?.map((rec: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    rec.is_optimal
                      ? "bg-cyan-500/20 border-cyan-500/60 text-cyan-300 ring-1 ring-cyan-400/30"
                      : "bg-slate-900/80 border-slate-800 text-slate-400"
                  }`}
                >
                  <div className="text-[10px] text-slate-400">Lap {rec.pit_lap}</div>
                  <div className={`font-bold mt-0.5 ${rec.undercut_probability_pct > 70 ? "text-emerald-400" : "text-amber-400"}`}>
                    {rec.undercut_probability_pct}%
                  </div>
                  {rec.is_optimal && <div className="text-[9px] text-cyan-400 font-black">OPTIMAL</div>}
                </div>
              ))}
            </div>
          </div>

          {/* Multi-Compound Tyre Degradation Chart */}
          <div className={`bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3 transition-all ${
            isChartMagnified ? "fixed inset-4 z-50 bg-[#0b0f17]/98 overflow-y-auto border-cyan-500/50 shadow-2xl p-8 space-y-6" : ""
          }`}>
            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-800 pb-2">
              <div className="flex items-center space-x-2">
                <Flame className="w-4 h-4 text-red-400" />
                <h4 className="text-xs font-bold text-slate-200 uppercase font-mono tracking-wider">
                  {year} {grandPrix} Tyre Degradation Wear & Pace Curves (30 Laps)
                </h4>
              </div>

              <div className="flex items-center space-x-3 flex-wrap gap-2">
                {/* Toggle Chart View Mode: Pace (s) vs Tyre Health (%) */}
                <div className="flex items-center space-x-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs font-mono">
                  <button
                    onClick={() => setChartMode("pace")}
                    className={`px-2.5 py-1 rounded-md transition-all font-bold ${
                      chartMode === "pace" ? "bg-cyan-500/30 text-cyan-300 border border-cyan-500/50" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    <Activity className="w-3 h-3 inline mr-1" /> Lap Pace (s)
                  </button>
                  <button
                    onClick={() => setChartMode("health")}
                    className={`px-2.5 py-1 rounded-md transition-all font-bold ${
                      chartMode === "health" ? "bg-purple-500/30 text-purple-300 border border-purple-500/50" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    <HeartPulse className="w-3 h-3 inline mr-1" /> Tyre Health (%)
                  </button>
                </div>

                {/* Magnify Chart Toggle Button */}
                <button
                  onClick={() => setIsChartMagnified(!isChartMagnified)}
                  className="flex items-center space-x-1 px-3 py-1 bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-500/40 rounded-lg text-xs font-mono font-bold transition-all"
                >
                  {isChartMagnified ? (
                    <>
                      <X className="w-3.5 h-3.5" /> <span>Close</span>
                    </>
                  ) : (
                    <>
                      <Maximize2 className="w-3.5 h-3.5 text-cyan-400" /> <span>Magnify</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Recharts Multi-Compound Curves */}
            <div className={isChartMagnified ? "h-96 w-full" : "h-48 w-full"}>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis
                      dataKey="stint_lap"
                      stroke="#475569"
                      tick={{ fontSize: 10 }}
                      label={{ value: 'Stint Lap Number (1-30 Laps)', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      tick={{ fontSize: 10 }}
                      domain={chartMode === "pace" ? ["auto", "auto"] : [0, 100]}
                      tickFormatter={(val: number) => (chartMode === "pace" ? `${val.toFixed(1)}s` : `${val}%`)}
                      label={{
                        value: chartMode === "pace" ? 'Lap Pace (Seconds)' : 'Remaining Tyre Health (%)',
                        angle: -90,
                        position: 'insideLeft',
                        offset: 10,
                        fill: '#94a3b8',
                        fontSize: 10,
                        fontFamily: 'monospace'
                      }}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                      formatter={(val: any, name: any) => [
                        chartMode === "pace" ? `${val}s` : `${val}%`,
                        String(name || "").replace("_pace", "").replace("_health", "")
                      ]}
                      labelFormatter={(l: any) => `Stint Lap: ${l}`}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />

                    {chartMode === "pace" ? (
                      <>
                        <Line type="monotone" dataKey="SOFT_pace" stroke="#EF4444" strokeWidth={2.5} dot={false} name="SOFT Compound Pace" />
                        <Line type="monotone" dataKey="MEDIUM_pace" stroke="#EAB308" strokeWidth={2.5} dot={false} name="MEDIUM Compound Pace" />
                        <Line type="monotone" dataKey="HARD_pace" stroke="#38BDF8" strokeWidth={2.5} dot={false} name="HARD Compound Pace" />
                      </>
                    ) : (
                      <>
                        <Line type="monotone" dataKey="SOFT_health" stroke="#EF4444" strokeWidth={2.5} dot={false} name="SOFT Health (%)" />
                        <Line type="monotone" dataKey="MEDIUM_health" stroke="#EAB308" strokeWidth={2.5} dot={false} name="MEDIUM Health (%)" />
                        <Line type="monotone" dataKey="HARD_health" stroke="#38BDF8" strokeWidth={2.5} dot={false} name="HARD Health (%)" />
                      </>
                    )}
                    <Brush dataKey="stint_lap" height={20} stroke="#334155" fill="#0f172a" tickFormatter={(l) => `L${l}`} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs font-mono text-slate-500">
                  Loading multi-compound degradation model...
                </div>
              )}
            </div>

            {/* Bottom Legend Readout */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
              <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span><span>Soft Cliff: Lap {tyreDegData?.cliff_threshold_lap || 14}</span></span>
              <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span><span>Track Abrasion: {circuitProfile?.abrasion_factor || 1.0}x</span></span>
              <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span><span>Pit Loss: {circuitProfile?.pit_loss_sec || 21.5}s</span></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
