'use client';

import React from 'react';
import { CalendarDays, Flag, User, Loader2, CheckCircle2, Zap, ArrowRight, ShieldAlert } from 'lucide-react';

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
  has_passed?: boolean;
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
  scheduleEvents: ScheduleEvent[];
  driverLineup: DriverItem[];
  loadingSchedule: boolean;
  loadingDrivers: boolean;
  onLaunchIntel?: () => void;
}

const YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018];

const SESSIONS = [
  { id: 'R',   label: 'Race',          short: 'R',   desc: 'Grand Prix Race' },
  { id: 'Q',   label: 'Qualifying',    short: 'Q',   desc: 'Pole Position Battle' },
  { id: 'FP1', label: 'Practice 1',    short: 'FP1', desc: 'Free Practice 1' },
  { id: 'FP2', label: 'Practice 2',    short: 'FP2', desc: 'Free Practice 2' },
  { id: 'FP3', label: 'Practice 3',    short: 'FP3', desc: 'Free Practice 3' },
];

// Team color map
const TEAM_COLORS: Record<string, string> = {
  'Red Bull Racing': '#3671C6',
  'Ferrari': '#E8002D',
  'Mercedes': '#27F4D2',
  'McLaren': '#FF8000',
  'Aston Martin': '#229971',
  'Alpine': '#0093CC',
  'Williams': '#64C4FF',
  'RB': '#6692FF',
  'Kick Sauber': '#52E252',
  'Haas F1 Team': '#B6BABD',
};

const COUNTRY_FLAGS: Record<string, string> = {
  'bahrain': '🇧🇭', 'saudi arabia': '🇸🇦', 'australia': '🇦🇺', 'azerbaijan': '🇦🇿',
  'miami': '🇺🇸', 'usa': '🇺🇸', 'united states': '🇺🇸', 'monaco': '🇲🇨',
  'spain': '🇪🇸', 'canada': '🇨🇦', 'austria': '🇦🇹', 'great britain': '🇬🇧',
  'uk': '🇬🇧', 'hungary': '🇭🇺', 'belgium': '🇧🇪', 'netherlands': '🇳🇱',
  'italy': '🇮🇹', 'singapore': '🇸🇬', 'japan': '🇯🇵', 'qatar': '🇶🇦',
  'mexico': '🇲🇽', 'brazil': '🇧🇷', 'las vegas': '🇺🇸', 'abu dhabi': '🇦🇪',
  'china': '🇨🇳', 'emilia': '🇮🇹',
};

const getFlag = (country: string, location: string): string => {
  const key = (country + ' ' + location).toLowerCase();
  for (const [k, v] of Object.entries(COUNTRY_FLAGS)) {
    if (key.includes(k)) return v;
  }
  return '🏁';
};

export const ControlsPanel: React.FC<ControlsPanelProps> = ({
  params,
  onChange,
  scheduleEvents,
  driverLineup,
  loadingSchedule,
  loadingDrivers,
  onLaunchIntel,
}) => {
  const selectedEvent = scheduleEvents.find(
    (e) => e.search_key === params.grandPrix || e.location === params.grandPrix
  );
  const selectedSession = SESSIONS.find((s) => s.id === params.sessionType);

  const completedCount = scheduleEvents.filter((e) => e.has_passed !== false).length;
  const upcomingCount = scheduleEvents.length - completedCount;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* ── Season Selector Bar ──────────────────────────────────────── */}
      <div style={{
        background: '#111111',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '10px',
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <CalendarDays size={14} style={{ color: '#E10600' }} />
          <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>
            SEASON YEAR
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
          {YEARS.map((y) => {
            const active = params.year === y;
            return (
              <button
                key={y}
                onClick={() => onChange({ year: y })}
                style={{
                  padding: '5px 14px',
                  borderRadius: '5px',
                  fontSize: '12px',
                  fontWeight: active ? 700 : 500,
                  fontFamily: 'JetBrains Mono, monospace',
                  background: active ? '#E10600' : 'transparent',
                  color: active ? '#FFFFFF' : '#5A5A5A',
                  border: `1px solid ${active ? '#E10600' : 'transparent'}`,
                  cursor: 'pointer',
                  transition: 'all 0.12s ease',
                }}
                onMouseEnter={(e) => { if (!active) (e.currentTarget as HTMLButtonElement).style.color = '#9A9A9A'; }}
                onMouseLeave={(e) => { if (!active) (e.currentTarget as HTMLButtonElement).style.color = '#5A5A5A'; }}
              >
                {y}
              </button>
            );
          })}
        </div>

        <div style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#5A5A5A', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {loadingSchedule ? (
            <Loader2 size={12} style={{ color: '#E10600' }} className="animate-spin" />
          ) : (
            <>
              <span style={{ color: '#22C55E' }}>● {completedCount} Races Done</span>
              {upcomingCount > 0 && <span style={{ color: '#3A3A3A' }}>· {upcomingCount} Upcoming</span>}
            </>
          )}
        </div>
      </div>

      {/* ── Main Split Panel ────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>

        {/* ── LEFT: Grand Prix Calendar Selection ───────────────────── */}
        <div style={{
          background: '#111111',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '10px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          {/* Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            background: '#161616',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Flag size={13} style={{ color: '#E10600' }} />
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#F5F5F5', letterSpacing: '0.02em' }}>
                {params.year} Race Calendar
              </span>
            </div>
            <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#5A5A5A' }}>
              {scheduleEvents.length} Rounds
            </span>
          </div>

          {/* Race List Container */}
          <div style={{ padding: '10px', maxHeight: '520px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {loadingSchedule && scheduleEvents.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 0', gap: '10px', color: '#5A5A5A' }}>
                <Loader2 size={16} style={{ color: '#E10600' }} className="animate-spin" />
                <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' }}>Loading {params.year} calendar...</span>
              </div>
            ) : (
              scheduleEvents.map((ev) => {
                const isUpcoming = ev.has_passed === false;
                const isActive = (params.grandPrix === ev.search_key || params.grandPrix === ev.location) && !isUpcoming;
                const flag = getFlag(ev.country, ev.location);

                return (
                  <button
                    key={`${ev.round}-${ev.search_key}`}
                    disabled={isUpcoming}
                    onClick={() => {
                      if (isUpcoming) return;
                      onChange({ grandPrix: ev.search_key || ev.location });
                    }}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '7px',
                      background: isActive ? 'rgba(225,6,0,0.12)' : isUpcoming ? '#0E0E0E' : '#161616',
                      border: `1px solid ${isActive ? '#E10600' : isUpcoming ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.05)'}`,
                      opacity: isUpcoming ? 0.35 : 1,
                      cursor: isUpcoming ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.12s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive && !isUpcoming) {
                        (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.14)';
                        (e.currentTarget as HTMLButtonElement).style.background = '#1C1C1C';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive && !isUpcoming) {
                        (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.05)';
                        (e.currentTarget as HTMLButtonElement).style.background = '#161616';
                      }
                    }}
                  >
                    {/* Round number */}
                    <span style={{
                      fontSize: '10px',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontWeight: 800,
                      color: isActive ? '#E10600' : isUpcoming ? '#2A2A2A' : '#5A5A5A',
                      width: '26px',
                      flexShrink: 0,
                    }}>
                      R{String(ev.round).padStart(2, '0')}
                    </span>

                    {/* Flag emoji */}
                    <span style={{ fontSize: '14px', flexShrink: 0, opacity: isUpcoming ? 0.4 : 1 }}>
                      {flag}
                    </span>

                    {/* Event name & location */}
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <div style={{
                        fontSize: '12px',
                        fontWeight: isActive ? 700 : 500,
                        color: isActive ? '#FFFFFF' : isUpcoming ? '#4A4A4A' : '#D4D4D4',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {ev.event_name}
                      </div>
                      <div style={{ fontSize: '10px', color: isUpcoming ? '#333' : '#5A5A5A', fontFamily: 'JetBrains Mono, monospace', marginTop: '1px' }}>
                        {ev.location}
                      </div>
                    </div>

                    {/* Badge */}
                    {isActive ? (
                      <span style={{
                        fontSize: '9px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontWeight: 800,
                        color: '#E10600',
                        background: 'rgba(225,6,0,0.18)',
                        border: '1px solid rgba(225,6,0,0.30)',
                        padding: '2px 7px',
                        borderRadius: '3px',
                        letterSpacing: '0.06em',
                        flexShrink: 0,
                      }}>
                        SELECTED
                      </span>
                    ) : isUpcoming ? (
                      <span style={{
                        fontSize: '8px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontWeight: 600,
                        color: '#3A3A3A',
                        background: 'rgba(255,255,255,0.02)',
                        border: '1px solid rgba(255,255,255,0.04)',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        letterSpacing: '0.04em',
                        flexShrink: 0,
                      }}>
                        UPCOMING
                      </span>
                    ) : null}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ── RIGHT: Session Type & Driver Selection ────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* ── Card 1: Session Type ───────────────────────────────── */}
          <div style={{
            background: '#111111',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '10px',
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '12px 16px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              background: '#161616',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap size={13} style={{ color: '#E10600' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#F5F5F5' }}>
                  Session Type
                </span>
              </div>
              <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#E10600', fontWeight: 700 }}>
                {selectedSession?.label || params.sessionType}
              </span>
            </div>

            <div style={{ padding: '12px', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px' }}>
              {SESSIONS.map((s) => {
                const isActive = params.sessionType === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => onChange({ sessionType: s.id })}
                    style={{
                      padding: '10px 4px',
                      borderRadius: '6px',
                      background: isActive ? 'rgba(225,6,0,0.12)' : '#161616',
                      border: `1px solid ${isActive ? '#E10600' : 'rgba(255,255,255,0.05)'}`,
                      cursor: 'pointer',
                      textAlign: 'center',
                      transition: 'all 0.12s ease',
                    }}
                  >
                    <div style={{
                      fontSize: '14px',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontWeight: 800,
                      color: isActive ? '#E10600' : '#F5F5F5',
                    }}>
                      {s.short}
                    </div>
                    <div style={{ fontSize: '9px', color: isActive ? '#F5F5F5' : '#5A5A5A', marginTop: '2px' }}>
                      {s.label}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Card 2: Driver Lineup ──────────────────────────────── */}
          <div style={{
            background: '#111111',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '10px',
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '12px 16px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              background: '#161616',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <User size={13} style={{ color: '#E10600' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#F5F5F5' }}>
                  Driver Lineup
                </span>
              </div>
              {loadingDrivers && <Loader2 size={12} style={{ color: '#E10600' }} className="animate-spin" />}
            </div>

            <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

              {/* Primary Driver */}
              <div>
                <div style={{ fontSize: '10px', color: '#5A5A5A', marginBottom: '8px', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.06em', fontWeight: 600 }}>
                  PRIMARY DRIVER
                </div>

                {loadingDrivers ? (
                  <div style={{ padding: '16px 0', textAlign: 'center', fontSize: '11px', color: '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>
                    Loading lineup...
                  </div>
                ) : driverLineup.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: '6px' }}>
                    {driverLineup.map((d) => {
                      const isActive = params.driverCode === d.code;
                      const accentColor = TEAM_COLORS[d.team] || '#E10600';
                      return (
                        <button
                          key={d.code}
                          onClick={() => onChange({ driverCode: d.code })}
                          style={{
                            padding: '8px',
                            borderRadius: '6px',
                            background: isActive ? 'rgba(255,255,255,0.07)' : '#161616',
                            border: `1px solid ${isActive ? accentColor : 'rgba(255,255,255,0.05)'}`,
                            cursor: 'pointer',
                            textAlign: 'left',
                            position: 'relative',
                            overflow: 'hidden',
                            transition: 'all 0.12s ease',
                          }}
                        >
                          <div style={{
                            position: 'absolute', top: 0, left: 0, bottom: 0, width: '3px',
                            background: accentColor,
                          }} />
                          <div style={{ paddingLeft: '4px' }}>
                            <div style={{
                              fontSize: '13px',
                              fontWeight: 800,
                              fontFamily: 'JetBrains Mono, monospace',
                              color: isActive ? '#FFFFFF' : '#9A9A9A',
                            }}>
                              {d.code}
                            </div>
                            <div style={{ fontSize: '9px', color: '#5A5A5A', marginTop: '1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {d.name?.split(' ').pop() || d.code}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <select
                    value={params.driverCode}
                    onChange={(e) => onChange({ driverCode: e.target.value })}
                    className="f1-select"
                  >
                    <option value={params.driverCode}>{params.driverCode}</option>
                  </select>
                )}
              </div>

              {/* Comparison Driver */}
              <div>
                <div style={{ fontSize: '10px', color: '#5A5A5A', marginBottom: '8px', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.06em', fontWeight: 600 }}>
                  COMPARE WITH (OPTIONAL)
                </div>

                {loadingDrivers ? null : driverLineup.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: '6px' }}>
                    {/* None */}
                    <button
                      onClick={() => onChange({ comparisonDriverCode: undefined })}
                      style={{
                        padding: '8px',
                        borderRadius: '6px',
                        background: !params.comparisonDriverCode ? 'rgba(255,255,255,0.05)' : '#161616',
                        border: `1px solid ${!params.comparisonDriverCode ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.05)'}`,
                        cursor: 'pointer',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '12px', fontWeight: 700, color: !params.comparisonDriverCode ? '#FFFFFF' : '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>
                        —
                      </div>
                      <div style={{ fontSize: '9px', color: '#5A5A5A', marginTop: '1px' }}>None</div>
                    </button>

                    {driverLineup
                      .filter((d) => d.code !== params.driverCode)
                      .map((d) => {
                        const isActive = params.comparisonDriverCode === d.code;
                        const accentColor = TEAM_COLORS[d.team] || '#F59E0B';
                        return (
                          <button
                            key={`comp-${d.code}`}
                            onClick={() => onChange({ comparisonDriverCode: isActive ? undefined : d.code })}
                            style={{
                              padding: '8px',
                              borderRadius: '6px',
                              background: isActive ? 'rgba(245,158,11,0.10)' : '#161616',
                              border: `1px solid ${isActive ? '#F59E0B' : 'rgba(255,255,255,0.05)'}`,
                              cursor: 'pointer',
                              textAlign: 'left',
                              position: 'relative',
                              overflow: 'hidden',
                              transition: 'all 0.12s ease',
                            }}
                          >
                            <div style={{
                              position: 'absolute', top: 0, left: 0, bottom: 0, width: '3px',
                              background: accentColor,
                            }} />
                            <div style={{ paddingLeft: '4px' }}>
                              <div style={{
                                fontSize: '13px',
                                fontWeight: 800,
                                fontFamily: 'JetBrains Mono, monospace',
                                color: isActive ? '#F59E0B' : '#7A7A7A',
                              }}>
                                {d.code}
                              </div>
                              <div style={{ fontSize: '9px', color: '#5A5A5A', marginTop: '1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {d.name?.split(' ').pop() || d.code}
                              </div>
                            </div>
                          </button>
                        );
                      })}
                  </div>
                ) : (
                  <select
                    value={params.comparisonDriverCode || ''}
                    onChange={(e) => onChange({ comparisonDriverCode: e.target.value || undefined })}
                    className="f1-select"
                  >
                    <option value="">— None —</option>
                  </select>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Summary Banner & Launch Button ─────────────────────── */}
      {selectedEvent && selectedSession && params.driverCode && (
        <div style={{
          padding: '14px 20px',
          background: '#141414',
          border: '1px solid rgba(225,6,0,0.25)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <CheckCircle2 size={16} style={{ color: '#22C55E', flexShrink: 0 }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' }}>
              <span style={{ color: '#E10600', fontWeight: 800 }}>{params.year}</span>
              <span style={{ color: '#5A5A5A' }}>·</span>
              <span style={{ color: '#FFFFFF', fontWeight: 600 }}>
                {getFlag(selectedEvent.country, selectedEvent.location)} {selectedEvent.event_name}
              </span>
              <span style={{ color: '#5A5A5A' }}>·</span>
              <span style={{ color: '#9A9A9A' }}>{selectedSession.label}</span>
              <span style={{ color: '#5A5A5A' }}>·</span>
              <span style={{ color: '#E10600', fontWeight: 800 }}>{params.driverCode}</span>
              {params.comparisonDriverCode && (
                <>
                  <span style={{ color: '#5A5A5A' }}>vs</span>
                  <span style={{ color: '#F59E0B', fontWeight: 800 }}>{params.comparisonDriverCode}</span>
                </>
              )}
            </div>
          </div>

          {onLaunchIntel && (
            <button
              onClick={onLaunchIntel}
              className="f1-btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', fontSize: '12px' }}
            >
              <span>Launch Console</span>
              <ArrowRight size={13} />
            </button>
          )}
        </div>
      )}
    </div>
  );
};
