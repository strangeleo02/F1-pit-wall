'use client';

import React, { useState } from 'react';
import { Radio, Volume2, Star, AlertCircle, Wrench, Zap, Disc, ChevronDown, ChevronUp } from 'lucide-react';

export interface RadioItem {
  driver?: string;
  session?: string;
  year?: number;
  grand_prix?: string;
  lap_start?: number | null;
  lap_end?: number | null;
  team?: string;
  transcript_text?: string;
  text?: string;
  message?: string;
  recording_url?: string;
  source?: string;
  correlated_anomaly?: boolean;
}

type SentimentCategory = 'ALL' | 'COMPLAINTS' | 'PIT_REQUESTS' | 'STRATEGY' | 'TYRE_FEEDBACK';

interface RadioTranscriptsFeedProps {
  transcripts: RadioItem[];
}

const CATEGORY_FILTERS: Array<{ id: SentimentCategory; label: string }> = [
  { id: 'ALL',          label: 'All' },
  { id: 'TYRE_FEEDBACK',label: 'Tyre' },
  { id: 'PIT_REQUESTS', label: 'Pit' },
  { id: 'STRATEGY',     label: 'Strategy' },
  { id: 'COMPLAINTS',   label: 'Complaint' },
];

const getSentimentCategory = (text: string): SentimentCategory => {
  const lower = text.toLowerCase();
  if (lower.match(/tyre|tire|deg|vibrat|grain|blister|grip/)) return 'TYRE_FEEDBACK';
  if (lower.match(/box|pit|wing|damage|puncture/))           return 'PIT_REQUESTS';
  if (lower.match(/complain|slow|issue|power|problem|pushed off|illegal/)) return 'COMPLAINTS';
  return 'STRATEGY';
};

const CATEGORY_COLORS: Record<SentimentCategory, { bg: string; text: string; border: string; icon: React.ReactNode }> = {
  ALL:           { bg: '', text: '', border: '', icon: null },
  TYRE_FEEDBACK: { bg: 'rgba(245,158,11,0.08)', text: '#FCD34D', border: 'rgba(245,158,11,0.20)', icon: <Disc size={9} /> },
  PIT_REQUESTS:  { bg: 'rgba(59,130,246,0.08)',  text: '#93C5FD', border: 'rgba(59,130,246,0.20)', icon: <Wrench size={9} /> },
  STRATEGY:      { bg: 'rgba(168,85,247,0.08)',  text: '#C084FC', border: 'rgba(168,85,247,0.20)', icon: <Zap size={9} /> },
  COMPLAINTS:    { bg: 'rgba(239,68,68,0.08)',   text: '#FCA5A5', border: 'rgba(239,68,68,0.20)',  icon: <AlertCircle size={9} /> },
};

export const RadioTranscriptsFeed: React.FC<RadioTranscriptsFeedProps> = ({ transcripts }) => {
  const [activeCategory, setActiveCategory] = useState<SentimentCategory>('ALL');
  const [collapsed, setCollapsed] = useState(false);

  if (!transcripts || transcripts.length === 0) return null;

  const filtered = transcripts.filter((t) => {
    if (activeCategory === 'ALL') return true;
    const text = t.transcript_text || t.text || t.message || '';
    return getSentimentCategory(text) === activeCategory;
  });

  return (
    <div style={{
      background: '#111111',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '10px',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: '#161616',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={12} style={{ color: '#F59E0B' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#F5F5F5' }}>Team Radio</span>
          <span style={{
            fontSize: '9px',
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 700,
            color: '#F59E0B',
            background: 'rgba(245,158,11,0.10)',
            border: '1px solid rgba(245,158,11,0.20)',
            padding: '1px 6px',
            borderRadius: '3px',
          }}>
            {transcripts.length}
          </span>
        </div>
        <button
          onClick={() => setCollapsed((v) => !v)}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#5A5A5A', display: 'flex' }}
        >
          {collapsed ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
        </button>
      </div>

      {!collapsed && (
        <>
          {/* Category Filter Strip */}
          <div style={{
            display: 'flex',
            gap: '4px',
            padding: '8px 14px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            overflowX: 'auto',
          }}>
            {CATEGORY_FILTERS.map((cat) => {
              const isActive = activeCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  style={{
                    padding: '3px 10px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontWeight: isActive ? 700 : 400,
                    background: isActive ? 'rgba(255,255,255,0.07)' : 'transparent',
                    color: isActive ? '#F5F5F5' : '#5A5A5A',
                    border: `1px solid ${isActive ? 'rgba(255,255,255,0.14)' : 'transparent'}`,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.12s ease',
                  }}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>

          {/* Transcript list */}
          <div style={{ maxHeight: '480px', overflowY: 'auto', padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filtered.length > 0 ? (
              filtered.map((t, idx) => {
                const driverCode = t.driver || 'FIA';
                const isRaceControl = t.source === 'race_control' || driverCode === 'FIA';
                let textContent = t.transcript_text || t.text || t.message || '';
                const category = getSentimentCategory(textContent);
                const catStyle = CATEGORY_COLORS[category];
                const audioUrl = t.recording_url ||
                  (textContent.includes('http') ? textContent.match(/https?:\/\/[^\s"]+/)?.[0] : undefined);

                if (textContent.startsWith('Team radio audio:') || textContent.includes('http')) {
                  textContent = `${driverCode} (${t.team || 'PitWall'}) — Team Radio`;
                }

                return (
                  <div
                    key={idx}
                    style={{
                      padding: '10px 12px',
                      borderRadius: '7px',
                      background: t.correlated_anomaly ? 'rgba(245,158,11,0.06)' : '#181818',
                      border: `1px solid ${t.correlated_anomaly ? 'rgba(245,158,11,0.25)' : 'rgba(255,255,255,0.06)'}`,
                    }}
                  >
                    {/* Meta row */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '10px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontWeight: 700,
                        color: isRaceControl ? '#E10600' : '#F5F5F5',
                        background: isRaceControl ? 'rgba(225,6,0,0.12)' : 'rgba(255,255,255,0.07)',
                        border: `1px solid ${isRaceControl ? 'rgba(225,6,0,0.25)' : 'rgba(255,255,255,0.08)'}`,
                        padding: '1px 7px',
                        borderRadius: '3px',
                      }}>
                        {driverCode}
                      </span>

                      {t.team && (
                        <span style={{ fontSize: '10px', color: '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>
                          {t.team}
                        </span>
                      )}

                      {t.lap_start && (
                        <span style={{ fontSize: '10px', color: '#F59E0B', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
                          L{t.lap_start}
                        </span>
                      )}

                      {/* Category pill */}
                      {category !== 'STRATEGY' && (
                        <span style={{
                          fontSize: '9px',
                          fontFamily: 'JetBrains Mono, monospace',
                          fontWeight: 700,
                          color: catStyle.text,
                          background: catStyle.bg,
                          border: `1px solid ${catStyle.border}`,
                          padding: '1px 6px',
                          borderRadius: '3px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '3px',
                        }}>
                          {catStyle.icon}
                          {category.replace('_', ' ')}
                        </span>
                      )}

                      {t.correlated_anomaly && (
                        <span style={{
                          marginLeft: 'auto',
                          fontSize: '9px',
                          fontFamily: 'JetBrains Mono, monospace',
                          fontWeight: 700,
                          color: '#FCD34D',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '3px',
                        }}>
                          <Star size={9} style={{ fill: '#FCD34D', color: '#FCD34D' }} />
                          ANOMALY
                        </span>
                      )}
                    </div>

                    {/* Transcript text */}
                    <p style={{ fontSize: '12px', color: '#C0C0C0', lineHeight: 1.55, margin: 0 }}>
                      "{textContent}"
                    </p>

                    {/* Audio player */}
                    {audioUrl && (
                      <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Volume2 size={11} style={{ color: '#F59E0B', flexShrink: 0 }} />
                        <audio controls src={audioUrl} style={{ width: '100%', height: '28px', borderRadius: '4px' }} />
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', fontSize: '11px', color: '#5A5A5A', fontFamily: 'JetBrains Mono, monospace' }}>
                No transcripts for "{activeCategory}"
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
