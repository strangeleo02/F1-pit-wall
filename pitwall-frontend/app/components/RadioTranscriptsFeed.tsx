'use client';

import React, { useState } from 'react';
import { Radio, Volume2, Star, ChevronDown, ChevronUp, User, ShieldAlert } from 'lucide-react';

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

interface RadioTranscriptsFeedProps {
  transcripts: RadioItem[];
}

export const RadioTranscriptsFeed: React.FC<RadioTranscriptsFeedProps> = ({ transcripts }) => {
  const [expanded, setExpanded] = useState<boolean>(true);

  if (!transcripts || transcripts.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel rounded-2xl p-5 mb-6 border border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <span>Team Radio Communications & FIA Control</span>
              <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-500/20 text-amber-300">
                {transcripts.length} Transcripts
              </span>
            </h3>
            <p className="text-xs text-slate-400 font-mono">Qdrant Vector Database Context Matches</p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Transcript Cards List */}
      {expanded && (
        <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
          {transcripts.map((t, idx) => {
            const driverCode = t.driver || 'FIA';
            const isRaceControl = t.source === 'race_control' || driverCode === 'FIA';
            let textContent = t.transcript_text || t.text || t.message || '';
            const audioUrl = t.recording_url || (textContent.includes('http') ? textContent.match(/https?:\/\/[^\s"]+/)?.[0] : undefined);

            if (textContent.startsWith('Team radio audio:') || textContent.includes('http')) {
              textContent = `Driver ${driverCode} (${t.team || 'PitWall'}) Team Radio Transmission`;
            }

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border transition-all ${
                  t.correlated_anomaly
                    ? 'bg-amber-500/10 border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.15)]'
                    : isRaceControl
                    ? 'bg-slate-900/80 border-slate-700/80'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-2 font-mono text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded font-bold ${isRaceControl ? 'bg-red-600/30 text-red-300' : 'bg-blue-600/30 text-blue-300'}`}>
                      {driverCode}
                    </span>
                    {t.team && <span className="text-slate-400 text-[11px]">{t.team}</span>}
                    {t.lap_start && <span className="text-amber-400 font-semibold">Lap {t.lap_start}</span>}
                  </div>

                  {t.correlated_anomaly && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-amber-400 bg-amber-500/20 px-2 py-0.5 rounded border border-amber-500/30">
                      <Star className="w-3 h-3 fill-amber-400" /> Correlated Anomaly
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-200 leading-relaxed font-sans mb-2">
                  "{textContent}"
                </p>

                {/* Built-in HTML5 Audio Player */}
                {audioUrl && (
                  <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center gap-2">
                    <Volume2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <audio controls src={audioUrl} className="w-full h-7 rounded opacity-90 scale-95 origin-left" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
