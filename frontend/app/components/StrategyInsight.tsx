'use client';

import React, { useState } from 'react';
import { Cpu, Copy, Check, Loader2 } from 'lucide-react';

interface StrategyInsightProps {
  insightText: string;
  streaming: boolean;
}

const parseInlineFormatting = (text: string) => {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i} style={{ fontWeight: 700, color: '#F5F5F5' }}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={i} style={{ color: '#FCD34D', fontStyle: 'italic' }}>{part.slice(1, -1)}</em>;
    if (part.startsWith('`') && part.endsWith('`'))
      return (
        <code key={i} style={{
          background: 'rgba(225,6,0,0.10)',
          color: '#FCA5A5',
          padding: '1px 6px',
          borderRadius: '3px',
          fontSize: '11px',
          fontFamily: 'JetBrains Mono, monospace',
          border: '1px solid rgba(225,6,0,0.20)',
        }}>
          {part.slice(1, -1)}
        </code>
      );
    return part;
  });
};

const renderLine = (line: string, index: number) => {
  if (line.startsWith('### ') || line.startsWith('## ')) {
    const title = line.replace(/^#+\s*/, '');
    return (
      <div key={index} style={{ marginTop: '20px', marginBottom: '8px' }}>
        <div style={{
          fontSize: '11px',
          fontWeight: 700,
          color: '#E10600',
          letterSpacing: '0.10em',
          textTransform: 'uppercase',
          fontFamily: 'JetBrains Mono, monospace',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          <span style={{ width: '16px', height: '1px', background: '#E10600', display: 'inline-block', flexShrink: 0 }} />
          {title}
        </div>
      </div>
    );
  }
  if (line.startsWith('#### ')) {
    return (
      <div key={index} style={{ fontWeight: 600, fontSize: '13px', color: '#F5F5F5', marginTop: '10px', marginBottom: '4px' }}>
        {line.replace(/^#+\s*/, '')}
      </div>
    );
  }
  if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
    return (
      <div key={index} style={{ display: 'flex', gap: '8px', fontSize: '13px', color: '#9A9A9A', marginBottom: '4px', lineHeight: 1.6 }}>
        <span style={{ color: '#E10600', flexShrink: 0, marginTop: '1px' }}>—</span>
        <span>{parseInlineFormatting(line.trim().replace(/^[-*]\s*/, ''))}</span>
      </div>
    );
  }
  if (line.trim().length === 0) return <div key={index} style={{ height: '8px' }} />;
  return (
    <p key={index} style={{ fontSize: '13px', color: '#C0C0C0', lineHeight: 1.7, marginBottom: '6px' }}>
      {parseInlineFormatting(line)}
    </p>
  );
};

export const StrategyInsight: React.FC<StrategyInsightProps> = ({ insightText, streaming }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!insightText) return;
    navigator.clipboard.writeText(insightText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        background: '#111111',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '10px',
        overflow: 'hidden',
      }}
    >
      {/* Header bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: '#161616',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={13} style={{ color: '#E10600' }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#F5F5F5', letterSpacing: '0.03em' }}>
            Strategy Intelligence
          </span>
          {streaming && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#E10600', display: 'inline-block', animation: 'pulse-dot 1s infinite' }} />
              <span style={{ fontSize: '10px', color: '#E10600', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.05em' }}>STREAMING</span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {insightText && (
            <button
              onClick={handleCopy}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: copied ? '#22C55E' : '#5A5A5A',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '20px', minHeight: '200px' }}>
        {insightText ? (
          <div>
            {insightText.split('\n').map((line, idx) => renderLine(line, idx))}
            {streaming && <span className="stream-cursor" />}
          </div>
        ) : streaming ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#5A5A5A', paddingTop: '40px', justifyContent: 'center' }}>
            <Loader2 size={14} style={{ animation: 'spin 1s linear infinite', color: '#E10600' }} />
            <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' }}>Processing strategy insight...</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingTop: '60px', gap: '10px', color: '#5A5A5A' }}>
            <Cpu size={28} style={{ opacity: 0.2, color: '#E10600' }} />
            <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.05em' }}>
              Awaiting query
            </span>
            <span style={{ fontSize: '11px', color: '#3A3A3A', textAlign: 'center', maxWidth: '300px', lineHeight: 1.6 }}>
              Select a session in the Session tab and type a question in the query bar below.
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
