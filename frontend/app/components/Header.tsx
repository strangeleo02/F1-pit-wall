'use client';

import React, { useState, useEffect } from 'react';
import { Activity, Radio, Sliders, CalendarDays, BarChart2, Wifi, Clock, Flag } from 'lucide-react';

export type TrackFlagState = 'GREEN' | 'YELLOW' | 'RED' | 'SC' | 'VSC';
export type TabId = 'RACE_INTEL' | 'TELEMETRY' | 'PIT_STRATEGY' | 'SESSION';

interface HeaderProps {
  backendConnected: boolean;
  onRefreshBackend: () => void;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  weather?: {
    track_temp_celsius?: number;
    air_temp_celsius?: number;
    rainfall?: boolean;
    status?: string;
  } | null;
}

const TABS: { id: TabId; label: string; icon: React.FC<{ size?: number; className?: string }> }[] = [
  { id: 'SESSION',      label: 'Session',      icon: CalendarDays },
  { id: 'RACE_INTEL',   label: 'Race Intel',   icon: Radio },
  { id: 'TELEMETRY',    label: 'Telemetry',    icon: Activity },
  { id: 'PIT_STRATEGY', label: 'Pit Strategy', icon: Sliders },
];

const FLAG_CONFIG: Record<TrackFlagState, { label: string; className: string }> = {
  GREEN:  { label: 'GREEN',  className: 'flag-green' },
  YELLOW: { label: 'YELLOW', className: 'flag-yellow' },
  RED:    { label: 'RED',    className: 'flag-red' },
  SC:     { label: 'SAFETY CAR', className: 'flag-sc' },
  VSC:    { label: 'VSC',    className: 'flag-vsc' },
};

export const Header: React.FC<HeaderProps> = ({
  backendConnected,
  onRefreshBackend,
  activeTab,
  onTabChange,
  weather,
}) => {
  const [timeString, setTimeString] = useState<string>('');
  const [flagState, setFlagState] = useState<TrackFlagState>('GREEN');
  const [flagMenuOpen, setFlagMenuOpen] = useState(false);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTimeString(now.toISOString().split('T')[1].slice(0, 8) + ' UTC');
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const currentFlag = FLAG_CONFIG[flagState];

  return (
    <header
      style={{
        background: '#111111',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        height: '52px',
      }}
    >
      <div
        style={{
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '0 20px',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '0',
        }}
      >
        {/* ── Wordmark ───────────────────────────────────────────── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginRight: '32px', flexShrink: 0 }}>
          <div
            style={{
              width: '30px',
              height: '30px',
              borderRadius: '5px',
              background: '#E10600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ fontWeight: 900, fontSize: '13px', color: '#fff', fontStyle: 'italic', letterSpacing: '-0.5px' }}>F1</span>
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '14px', color: '#F5F5F5', letterSpacing: '0.04em' }}>
              PITWALL<span style={{ color: '#E10600' }}>.AI</span>
            </div>
            <div style={{ fontSize: '9px', color: '#5A5A5A', letterSpacing: '0.06em', lineHeight: 1, fontFamily: 'JetBrains Mono, monospace' }}>
              STRATEGY CONSOLE
            </div>
          </div>
        </div>

        {/* ── Tab Navigation ─────────────────────────────────────── */}
        <nav style={{ display: 'flex', alignItems: 'stretch', height: '100%', gap: '2px', flex: 1 }}>
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`f1-tab${isActive ? ' active' : ''}`}
              >
                <Icon size={12} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* ── Right side status strip ─────────────────────────────── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0, marginLeft: '16px' }}>

          {/* Session Weather status pill */}
          {weather && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '10px',
              fontFamily: 'JetBrains Mono, monospace',
              fontWeight: 600,
              color: '#F59E0B',
              background: 'rgba(245,158,11,0.08)',
              border: '1px solid rgba(245,158,11,0.20)',
              padding: '3px 9px',
              borderRadius: '4px',
            }}>
              <span>TRACK {weather.track_temp_celsius ?? 38}°C</span>
              <span style={{ opacity: 0.3 }}>|</span>
              <span>AIR {weather.air_temp_celsius ?? 26}°C</span>
              <span style={{ opacity: 0.3 }}>|</span>
              <span>{weather.status || 'DRY 🌤️'}</span>
            </div>
          )}

          {/* Track flag indicator + dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setFlagMenuOpen((v) => !v)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '4px 0',
              }}
            >
              <Flag size={11} className={currentFlag.className} />
              <span
                style={{
                  fontSize: '10px',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                }}
                className={currentFlag.className}
              >
                {currentFlag.label}
              </span>
            </button>

            {flagMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '28px',
                  background: '#1a1a1a',
                  border: '1px solid rgba(255,255,255,0.10)',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  zIndex: 200,
                  minWidth: '130px',
                }}
              >
                {(Object.keys(FLAG_CONFIG) as TrackFlagState[]).map((f) => (
                  <button
                    key={f}
                    onClick={() => { setFlagState(f); setFlagMenuOpen(false); }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      width: '100%',
                      padding: '9px 14px',
                      background: flagState === f ? 'rgba(255,255,255,0.05)' : 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '11px',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontWeight: 600,
                      letterSpacing: '0.05em',
                      color: flagState === f ? '#F5F5F5' : '#5A5A5A',
                      textAlign: 'left',
                    }}
                  >
                    <Flag size={10} className={FLAG_CONFIG[f].className} />
                    {FLAG_CONFIG[f].label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Backend status */}
          <button
            onClick={onRefreshBackend}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 0',
            }}
            title="Click to refresh backend connection"
          >
            <span className={`status-dot ${backendConnected ? 'online' : 'offline'}`} />
            <Wifi size={11} style={{ color: backendConnected ? '#22C55E' : '#EF4444' }} />
          </button>

          {/* Clock */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px',
              color: '#5A5A5A',
            }}
          >
            <Clock size={11} style={{ color: '#E10600' }} />
            {timeString || '00:00:00 UTC'}
          </div>
        </div>
      </div>
    </header>
  );
};
