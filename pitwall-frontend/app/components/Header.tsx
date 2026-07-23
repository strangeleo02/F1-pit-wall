'use client';

import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Wifi, Cpu, Clock, RefreshCw } from 'lucide-react';

interface HeaderProps {
  backendConnected: boolean;
  onRefreshBackend: () => void;
}

export const Header: React.FC<HeaderProps> = ({ backendConnected, onRefreshBackend }) => {
  const [timeString, setTimeString] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeString(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-4 py-3 mb-6">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-red-600/20 border border-red-500/40 text-red-500 shadow-[0_0_15px_rgba(255,24,1,0.3)]">
            <span className="font-black text-xl italic tracking-tighter">F1</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-black text-xl tracking-wider text-white uppercase italic">
                PitWall<span className="text-red-500 font-sans not-italic">.AI</span>
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-600/30 text-red-400 border border-red-500/30 rounded uppercase tracking-widest">
                Multi-Modal RAG
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">Formula 1 Strategy & Real-Time Telemetry Correlation</p>
          </div>
        </div>

        {/* Live Status Indicators */}
        <div className="flex items-center gap-4 text-xs font-mono">
          {/* Backend Status */}
          <button
            onClick={onRefreshBackend}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${
              backendConnected
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
            <Wifi className="w-3.5 h-3.5" />
            <span>{backendConnected ? 'BACKEND ONLINE' : 'DISCONNECTED'}</span>
            <RefreshCw className="w-3 h-3 opacity-60 hover:opacity-100" />
          </button>

          {/* Qdrant Status */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>QDRANT CLOUD</span>
          </div>

          {/* Groq Llama 3.3 Status */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300">
            <Cpu className="w-3.5 h-3.5" />
            <span>LLAMA 3.3 70B</span>
          </div>

          {/* Session Clock */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/60 text-slate-300">
            <Clock className="w-3.5 h-3.5 text-red-500" />
            <span>{timeString || '00:00:00 UTC'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
