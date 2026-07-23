'use client';

import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ControlsPanel, StrategyParams, ScheduleEvent, DriverItem } from './components/ControlsPanel';
import { StrategyInsight } from './components/StrategyInsight';
import { TelemetryCharts } from './components/TelemetryCharts';
import { RadioTranscriptsFeed, RadioItem } from './components/RadioTranscriptsFeed';
import { AlertCircle } from 'lucide-react';

const BACKEND_URL = 'http://localhost:8000';

export default function Home() {
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [streaming, setStreaming] = useState<boolean>(false);

  const [params, setParams] = useState<StrategyParams>({
    year: 2023,
    grandPrix: 'Monza',
    sessionType: 'R',
    driverCode: 'VER',
    comparisonDriverCode: 'HAM',
    query: 'Why did Max Verstappen complain about tire degradation on lap 15 to 20?'
  });

  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([]);
  const [driverLineup, setDriverLineup] = useState<DriverItem[]>([]);
  const [loadingSchedule, setLoadingSchedule] = useState<boolean>(false);
  const [loadingDrivers, setLoadingDrivers] = useState<boolean>(false);

  const [insightText, setInsightText] = useState<string>('');
  const [queryIntent, setQueryIntent] = useState<string>('MULTI_MODAL_RAG');
  const [telemetry, setTelemetry] = useState<any>(null);
  const [transcripts, setTranscripts] = useState<RadioItem[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Check backend health (60 second interval to avoid spamming server)
  const checkBackendHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        setBackendConnected(true);
        setErrorMessage(null);
      } else {
        setBackendConnected(false);
      }
    } catch {
      setBackendConnected(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 60000);
    return () => clearInterval(interval);
  }, []);

  // Fetch official F1 calendar schedule dynamically when year changes
  useEffect(() => {
    const fetchSchedule = async () => {
      setLoadingSchedule(true);
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/meta/schedule?year=${params.year}`);
        if (res.ok) {
          const data = await res.json();
          if (data.events && data.events.length > 0) {
            setScheduleEvents(data.events);
            const exists = data.events.some(
              (ev: ScheduleEvent) => ev.search_key === params.grandPrix || ev.location === params.grandPrix
            );
            if (!exists) {
              setParams((prev) => ({ ...prev, grandPrix: data.events[0].search_key || data.events[0].location }));
            }
          }
        }
      } catch (e) {
        console.warn('Schedule fetch failed:', e);
      } finally {
        setLoadingSchedule(false);
      }
    };

    fetchSchedule();
  }, [params.year]);

  // Fetch participating driver lineup dynamically when year, GP, or session changes
  useEffect(() => {
    const fetchDrivers = async () => {
      if (!params.grandPrix) return;
      setLoadingDrivers(true);
      try {
        const res = await fetch(
          `${BACKEND_URL}/api/v1/meta/drivers?year=${params.year}&grand_prix=${encodeURIComponent(
            params.grandPrix
          )}&session_type=${params.sessionType}`
        );
        if (res.ok) {
          const data = await res.json();
          if (data.drivers && data.drivers.length > 0) {
            setDriverLineup(data.drivers);
            const exists = data.drivers.some((d: DriverItem) => d.code === params.driverCode);
            if (!exists) {
              setParams((prev) => ({ ...prev, driverCode: data.drivers[0].code }));
            }
          }
        }
      } catch (e) {
        console.warn('Drivers fetch failed:', e);
      } finally {
        setLoadingDrivers(false);
      }
    };

    fetchDrivers();
  }, [params.year, params.grandPrix, params.sessionType]);

  const handleParamChange = (updated: Partial<StrategyParams>) => {
    setParams((prev) => ({ ...prev, ...updated }));
  };

  // Execute strategy query with SSE streaming chunk-by-chunk
  const executeQuery = async () => {
    if (!params.query.trim()) return;

    setLoading(true);
    setStreaming(true);
    setInsightText('');
    setQueryIntent('MULTI_MODAL_RAG');
    setTelemetry(null);
    setTranscripts([]);
    setErrorMessage(null);

    const payload = {
      year: params.year,
      grand_prix: params.grandPrix,
      session_type: params.sessionType,
      driver_code: params.driverCode.toUpperCase(),
      comparison_driver_code: params.comparisonDriverCode ? params.comparisonDriverCode.toUpperCase() : undefined,
      query: params.query
    };

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/strategy/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned status ${response.status}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported by response');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const rawData = trimmed.slice(6);
            if (rawData === '[DONE]') {
              setStreaming(false);
              break;
            }

            try {
              const parsed = JSON.parse(rawData);
              if (parsed.telemetry) {
                setTelemetry(parsed.telemetry);
              }
              if (parsed.radio_transcripts) {
                setTranscripts(parsed.radio_transcripts);
              }
              if (parsed.intent) {
                setQueryIntent(parsed.intent);
              }
              if (parsed.token) {
                setInsightText((prev) => prev + parsed.token);
              }
            } catch (err) {
              // Plain string token fallback
              setInsightText((prev) => prev + rawData);
            }
          }
        }
      }
    } catch (err: any) {
      console.warn('Strategy Streaming API error:', err);
      setErrorMessage(err.message || 'Failed to stream strategy insight from PitWall backend.');
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  return (
    <div className="min-h-screen pb-16">
      <Header backendConnected={backendConnected} onRefreshBackend={checkBackendHealth} />

      <main className="max-w-7xl mx-auto px-4">
        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage} (Ensure PitWall backend is running at http://localhost:8000)</span>
          </div>
        )}

        {/* Controls Panel */}
        <ControlsPanel
          params={params}
          onChange={handleParamChange}
          onSubmit={executeQuery}
          loading={loading}
          scheduleEvents={scheduleEvents}
          driverLineup={driverLineup}
          loadingSchedule={loadingSchedule}
          loadingDrivers={loadingDrivers}
        />

        {/* Multi-Modal Output Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Insight & Telemetry Column (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            <StrategyInsight insightText={insightText} streaming={streaming} intent={queryIntent} />
            <TelemetryCharts telemetry={telemetry} />
          </div>

          {/* Radio Transcripts Feed Column (4 cols) */}
          <div className="lg:col-span-4">
            <RadioTranscriptsFeed transcripts={transcripts} />
          </div>
        </div>
      </main>
    </div>
  );
}
