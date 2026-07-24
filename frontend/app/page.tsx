'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Header, TabId } from './components/Header';
import { ControlsPanel, StrategyParams, ScheduleEvent, DriverItem } from './components/ControlsPanel';
import { StrategyInsight } from './components/StrategyInsight';
import { TelemetryCharts } from './components/TelemetryCharts';
import { RadioTranscriptsFeed, RadioItem } from './components/RadioTranscriptsFeed';
import { CircuitMap } from './components/CircuitMap';
import { UndercutSimulator } from './components/UndercutSimulator';
import { Send, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { API_BASE_URL, API_ENDPOINTS } from './config';

// Module-level caches — persist for the entire browser session.
// Avoids re-fetching identical data when the user switches tabs or tweaks params.
const _scheduleCache = new Map<number, any[]>();
const _driversCache = new Map<string, any[]>();
const _weatherCache = new Map<string, any>();

const PRESETS = [
  'Why did Max complain about tire degradation on laps 15–20?',
  'Compare Hamilton vs Verstappen speed profile at Monza',
  'Analyze pace delta and braking efficiency',
  'Summarize team radio during safety car restart',
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>('SESSION');
  const [backendConnected, setBackendConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  const [params, setParams] = useState<StrategyParams>({
    year: 2023,
    grandPrix: 'Monza',
    sessionType: 'R',
    driverCode: 'VER',
    comparisonDriverCode: 'HAM',
    query: '',
  });

  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([]);
  const [driverLineup, setDriverLineup] = useState<DriverItem[]>([]);
  const [loadingSchedule, setLoadingSchedule] = useState(false);
  const [loadingDrivers, setLoadingDrivers] = useState(false);

  const [insightText, setInsightText] = useState('');
  const [telemetry, setTelemetry] = useState<any>(null);
  const [transcripts, setTranscripts] = useState<RadioItem[]>([]);
  const [sessionWeather, setSessionWeather] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hoverDistancePct, setHoverDistancePct] = useState<number | null>(null);
  const queryRef = useRef<HTMLInputElement>(null);

  // ── Backend health check + warmup ping ───────────────────────
  const checkBackendHealth = async () => {
    try {
      const res = await fetch(API_ENDPOINTS.HEALTH);
      setBackendConnected(res.ok);
      if (res.ok) {
        // Fire a warmup ping to trigger lazy imports on the backend
        // so the first real user request doesn't pay the import tax.
        fetch(`${API_BASE_URL}/api/v1/meta/schedule?year=${params.year}`)
          .then((r) => r.ok ? r.json() : null)
          .then((data) => {
            if (data?.events?.length > 0) {
              _scheduleCache.set(params.year, data.events);
              setScheduleEvents(data.events);
              const validCompleted = data.events.filter((ev: ScheduleEvent) => ev.has_passed !== false);
              const currentValid = data.events.find(
                (ev: ScheduleEvent) => (ev.search_key === params.grandPrix || ev.location === params.grandPrix) && ev.has_passed !== false
              );
              if (!currentValid && validCompleted.length > 0) {
                const fallbackEv = validCompleted[validCompleted.length - 1];
                setParams((p) => ({ ...p, grandPrix: fallbackEv.search_key || fallbackEv.location }));
              }
            }
          })
          .catch(() => {})
          .finally(() => setLoadingSchedule(false));
      }
    } catch {
      setBackendConnected(false);
    }
  };

  useEffect(() => {
    setLoadingSchedule(true);
    checkBackendHealth();
  }, []);

  // ── F1 Calendar (cache-first, warmup handles the initial fetch) ──
  useEffect(() => {
    if (_scheduleCache.has(params.year)) {
      const cached = _scheduleCache.get(params.year)!;
      setScheduleEvents(cached);
      const validCompleted = cached.filter((ev: ScheduleEvent) => ev.has_passed !== false);
      const currentValid = cached.find(
        (ev: ScheduleEvent) => (ev.search_key === params.grandPrix || ev.location === params.grandPrix) && ev.has_passed !== false
      );
      if (!currentValid && validCompleted.length > 0) {
        const fallbackEv = validCompleted[validCompleted.length - 1];
        setParams((p) => ({ ...p, grandPrix: fallbackEv.search_key || fallbackEv.location }));
      }
      return;
    }
    // Not cached yet — fetch directly (year changed)
    setLoadingSchedule(true);
    fetch(`${API_BASE_URL}/api/v1/meta/schedule?year=${params.year}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.events?.length > 0) {
          _scheduleCache.set(params.year, data.events);
          setScheduleEvents(data.events);
          const validCompleted = data.events.filter((ev: ScheduleEvent) => ev.has_passed !== false);
          const currentValid = data.events.find(
            (ev: ScheduleEvent) => (ev.search_key === params.grandPrix || ev.location === params.grandPrix) && ev.has_passed !== false
          );
          if (!currentValid) {
            const fallbackEv = validCompleted.length > 0 ? validCompleted[validCompleted.length - 1] : data.events[0];
            setParams((p) => ({ ...p, grandPrix: fallbackEv.search_key || fallbackEv.location }));
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoadingSchedule(false));
  }, [params.year]);

  // ── Drivers + Weather in parallel (cache-first, AbortController timeout) ──
  useEffect(() => {
    if (!params.grandPrix) return;

    const driversKey = `${params.year}|${params.grandPrix}|${params.sessionType}`;
    const weatherKey = `${params.year}|${params.grandPrix}`;

    const needDrivers = !_driversCache.has(driversKey);
    const needWeather = !_weatherCache.has(weatherKey);

    // Serve from cache immediately
    if (!needDrivers) {
      const cached = _driversCache.get(driversKey)!;
      setDriverLineup(cached);
      const exists = cached.some((d: DriverItem) => d.code === params.driverCode);
      if (!exists && cached.length > 0) setParams((p) => ({ ...p, driverCode: cached[0].code }));
    }
    if (!needWeather) {
      setSessionWeather(_weatherCache.get(weatherKey));
    }
    if (!needDrivers && !needWeather) return;

    // Fetch missing data in parallel with a 15s timeout
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);

    setLoadingDrivers(needDrivers);

    const fetches: Promise<void>[] = [];

    if (needDrivers) {
      fetches.push(
        fetch(`${API_BASE_URL}/api/v1/meta/drivers?year=${params.year}&grand_prix=${encodeURIComponent(params.grandPrix)}&session_type=${params.sessionType}`, { signal: controller.signal })
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data?.drivers?.length > 0) {
              _driversCache.set(driversKey, data.drivers);
              setDriverLineup(data.drivers);
              const exists = data.drivers.some((d: DriverItem) => d.code === params.driverCode);
              if (!exists) setParams((p) => ({ ...p, driverCode: data.drivers[0].code }));
            }
          })
          .catch(() => {})
      );
    }

    if (needWeather) {
      fetches.push(
        fetch(`${API_BASE_URL}/api/v1/meta/weather?year=${params.year}&grand_prix=${encodeURIComponent(params.grandPrix)}&session_type=${params.sessionType}`, { signal: controller.signal })
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data) {
              _weatherCache.set(weatherKey, data);
              setSessionWeather(data);
            }
          })
          .catch(() => {})
      );
    }

    Promise.all(fetches).finally(() => {
      clearTimeout(timer);
      setLoadingDrivers(false);
    });

    return () => { controller.abort(); clearTimeout(timer); };
  }, [params.year, params.grandPrix, params.sessionType]);


  // ── Query execution ──────────────────────────────────────────
  const executeQuery = async () => {
    if (!params.query.trim()) {
      queryRef.current?.focus();
      return;
    }

    setLoading(true);
    setStreaming(true);
    setInsightText('');

    setTelemetry(null);
    setTranscripts([]);
    setErrorMessage(null);

    // Auto-switch to Race Intel to show results
    setActiveTab('RACE_INTEL');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/strategy/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: params.year,
          grand_prix: params.grandPrix,
          session_type: params.sessionType,
          driver_code: params.driverCode.toUpperCase(),
          comparison_driver_code: params.comparisonDriverCode?.toUpperCase(),
          query: params.query,
        }),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const rawData = trimmed.slice(6).trim();
          if (rawData === '[DONE]') { setStreaming(false); break; }

          try {
            const parsed = JSON.parse(rawData);
            if (parsed.type === 'metadata' && parsed.data) {
              if (parsed.data.telemetry) setTelemetry(parsed.data.telemetry);
              if (parsed.data.radio_transcripts) setTranscripts(parsed.data.radio_transcripts);

            } else {
              if (parsed.telemetry) setTelemetry(parsed.telemetry);
              if (parsed.radio_transcripts) setTranscripts(parsed.radio_transcripts);

            }
            if (parsed.type === 'token' && parsed.content !== undefined) setInsightText((p) => p + parsed.content);
            else if (parsed.token !== undefined) setInsightText((p) => p + parsed.token);
            else if (parsed.content !== undefined) setInsightText((p) => p + parsed.content);
          } catch {
            if (rawData && rawData !== '[DONE]') setInsightText((p) => p + rawData);
          }
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to stream strategy insight.');
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); executeQuery(); }
  };

  // ── Tab content ──────────────────────────────────────────────
  const renderTab = () => {
    switch (activeTab) {
      case 'RACE_INTEL':
        return (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', alignItems: 'start' }}>
            <div>
              <StrategyInsight insightText={insightText} streaming={streaming} />
            </div>
            <div>
              <RadioTranscriptsFeed transcripts={transcripts} />
            </div>
          </div>
        );

      case 'TELEMETRY':
        return (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px', alignItems: 'start' }}>
            <TelemetryCharts telemetry={telemetry} onHoverDistancePctChange={setHoverDistancePct} />
            <CircuitMap
              grandPrix={params.grandPrix}
              year={params.year}
              driverCode={params.driverCode}
              hoverDistancePct={hoverDistancePct}
            />
          </div>
        );

      case 'PIT_STRATEGY':
        return (
          <UndercutSimulator
            primaryDriver={params.driverCode}
            comparisonDriver={params.comparisonDriverCode}
            grandPrix={params.grandPrix}
            year={params.year}
            sessionWeatherProp={sessionWeather}
          />
        );

      case 'SESSION':
        return (
          <ControlsPanel
            params={params}
            onChange={(updated) => setParams((p) => ({ ...p, ...updated }))}
            scheduleEvents={scheduleEvents}
            driverLineup={driverLineup}
            loadingSchedule={loadingSchedule}
            loadingDrivers={loadingDrivers}
            onLaunchIntel={() => setActiveTab('RACE_INTEL')}
          />
        );
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        backendConnected={backendConnected}
        onRefreshBackend={checkBackendHealth}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        weather={sessionWeather}
      />

      {/* ── Error Banner ─────────────────────────────────────────── */}
      {errorMessage && (
        <div style={{
          margin: '12px 20px 0',
          padding: '10px 16px',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239,68,68,0.25)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '12px',
          color: '#FCA5A5',
          fontFamily: 'JetBrains Mono, monospace',
        }}>
          <AlertCircle size={14} style={{ color: '#EF4444', flexShrink: 0 }} />
          {errorMessage}
        </div>
      )}

      {/* ── Tab content area ─────────────────────────────────────── */}
      <main
        style={{
          flex: 1,
          maxWidth: '1400px',
          width: '100%',
          margin: '0 auto',
          padding: '24px 20px 100px', // bottom pad for sticky bar
        }}
      >
        {renderTab()}
      </main>

      {/* ── Sticky Query Bar ─────────────────────────────────────── */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 90,
          background: 'rgba(13,13,13,0.96)',
          borderTop: '1px solid rgba(255,255,255,0.07)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          padding: '10px 20px',
        }}
      >
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Preset chips */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <Sparkles size={11} style={{ color: '#E10600', flexShrink: 0 }} />
            {PRESETS.map((preset, i) => (
              <button
                key={i}
                onClick={() => setParams((p) => ({ ...p, query: preset }))}
                style={{
                  padding: '3px 10px',
                  borderRadius: '4px',
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.07)',
                  color: '#5A5A5A',
                  fontSize: '10px',
                  cursor: 'pointer',
                  fontFamily: 'JetBrains Mono, monospace',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={(e) => { (e.target as HTMLButtonElement).style.color = '#F5F5F5'; (e.target as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.14)'; }}
                onMouseLeave={(e) => { (e.target as HTMLButtonElement).style.color = '#5A5A5A'; (e.target as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.07)'; }}
              >
                {preset}
              </button>
            ))}
          </div>

          {/* Main input row */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input
                ref={queryRef}
                type="text"
                value={params.query}
                onChange={(e) => setParams((p) => ({ ...p, query: e.target.value }))}
                onKeyDown={handleKeyDown}
                placeholder="Ask PitWall AI — telemetry, strategy, radio, or lap time analysis..."
                className="f1-input"
                style={{ paddingRight: '14px', height: '42px', fontSize: '13px' }}
              />
            </div>

            {/* Session context pill */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: '#181818',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '7px',
              flexShrink: 0,
            }}>
              <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#E10600', fontWeight: 700 }}>{params.driverCode}</span>
              <span style={{ fontSize: '10px', color: '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>·</span>
              <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#5A5A5A' }}>{params.year} {params.grandPrix}</span>
            </div>

            <button
              onClick={executeQuery}
              disabled={loading || !params.query.trim()}
              className="f1-btn-primary"
              style={{ height: '42px', display: 'flex', alignItems: 'center', gap: '7px', paddingLeft: '20px', paddingRight: '20px', flexShrink: 0 }}
            >
              {loading ? (
                <>
                  <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Analyzing</span>
                </>
              ) : (
                <>
                  <Send size={13} />
                  <span>Execute</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
