'use client';

import React, { useState } from 'react';
import { Cpu, Copy, Check, Radio, Gauge, Zap } from 'lucide-react';

interface StrategyInsightProps {
  insightText: string;
  streaming: boolean;
  intent?: string;
}

export const StrategyInsight: React.FC<StrategyInsightProps> = ({ insightText, streaming, intent }) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = () => {
    if (!insightText) return;
    navigator.clipboard.writeText(insightText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getIntentBadge = () => {
    if (!intent) return null;
    const norm = intent.toUpperCase();
    if (norm.includes('MULTI_MODAL') || norm.includes('RAG')) {
      return (
        <span className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-mono font-semibold">
          <Zap className="w-3 h-3 text-purple-400" /> MULTI_MODAL_RAG
        </span>
      );
    }
    if (norm.includes('TELEMETRY')) {
      return (
        <span className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[11px] font-mono font-semibold">
          <Gauge className="w-3 h-3 text-cyan-400" /> TELEMETRY_ONLY
        </span>
      );
    }
    if (norm.includes('RADIO')) {
      return (
        <span className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-mono font-semibold">
          <Radio className="w-3 h-3 text-amber-400" /> RADIO_TRANSCRIPTS
        </span>
      );
    }
    return null;
  };

  return (
    <div className="glass-panel rounded-2xl p-6 mb-6 border border-white/10 relative">
      {/* Card Header */}
      <div className="flex items-center justify-between gap-4 mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-base text-white tracking-wide flex items-center gap-2">
              <span>PitWall Strategy Insight</span>
              {streaming && (
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
              )}
            </h2>
            <p className="text-xs text-slate-400 font-mono">Groq Llama 3.3 70B Multi-Modal Reasoning</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {getIntentBadge()}
          {insightText && (
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
              title="Copy strategy insight"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Insight Text Viewer */}
      <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans min-h-[120px]">
        {insightText ? (
          <div>
            {insightText}
            {streaming && <span className="inline-block w-2 h-4 ml-1 bg-red-500 animate-pulse" />}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-slate-500 text-center font-mono">
            <Cpu className="w-10 h-10 mb-2 stroke-1 opacity-40 text-red-400" />
            <p className="text-xs">Awaiting Strategy Query Execution</p>
            <p className="text-[11px] text-slate-600 mt-1">Select year, GP, and driver above to generate RAG insights.</p>
          </div>
        )}
      </div>
    </div>
  );
};
