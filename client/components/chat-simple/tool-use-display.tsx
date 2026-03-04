'use client';

import { useState } from 'react';
import { ClientToolResult } from '@/lib/client-tools';

export type ToolStatus = 'pending' | 'running' | 'done' | 'error';

interface ToolUseDisplayProps {
  toolName: string;
  input: Record<string, unknown>;
  status: ToolStatus;
  result?: ClientToolResult | null;
  /** True when the tool ran in the browser; false when it ran on the server. */
  isClientSide?: boolean;
}

/** Compact one-liner summary of tool input for display in the header row. */
function summarizeInput(toolName: string, input: Record<string, unknown>): string {
  if (!input || Object.keys(input).length === 0) return '';

  switch (toolName) {
    case 'think': {
      const thought = String(input.thought ?? '');
      return thought.length > 80 ? thought.slice(0, 80) + '...' : thought;
    }
    case 'code': {
      const lang = String(input.language ?? '');
      const lines = String(input.source ?? '').split('\n').length;
      return `${lang} (${lines} line${lines !== 1 ? 's' : ''})`;
    }
    case 'editor': {
      const cmd = String(input.command ?? '');
      const path = String(input.path ?? '');
      return `${cmd} ${path}`;
    }
    default: {
      const first = Object.entries(input)[0];
      if (!first) return '';
      return `${first[0]}: ${JSON.stringify(first[1]).slice(0, 60)}`;
    }
  }
}

/** Short status badge for the tool execution state. */
function StatusBadge({ status }: { status: ToolStatus }) {
  const base = 'inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full';

  if (status === 'pending') {
    return (
      <span className={`${base} bg-gray-100 text-gray-500`}>
        <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
        queued
      </span>
    );
  }
  if (status === 'running') {
    return (
      <span className={`${base} bg-blue-50 text-blue-600`}>
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
        running
      </span>
    );
  }
  if (status === 'error') {
    return (
      <span className={`${base} bg-red-50 text-red-600`}>
        <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
        error
      </span>
    );
  }
  return (
    <span className={`${base} bg-green-50 text-green-700`}>
      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
      done
    </span>
  );
}

/**
 * Displays a single tool invocation — name, input summary, execution status,
 * and a collapsible result preview.
 *
 * Client-side tools (think, code, editor) get a distinct "browser" badge.
 * Server-side tools show a "server" badge.
 */
export default function ToolUseDisplay({
  toolName,
  input,
  status,
  result,
  isClientSide = false,
}: ToolUseDisplayProps) {
  const [expanded, setExpanded] = useState(false);
  const summary = summarizeInput(toolName, input);

  const hasResult = result !== undefined && result !== null;
  const resultText =
    hasResult && result.result !== null && result.result !== undefined
      ? JSON.stringify(result.result, null, 2)
      : null;
  const errorText = hasResult ? result.error : null;

  return (
    <div className="my-1 rounded-lg border border-[#E5E9F0] bg-[#F8FAFC] text-xs overflow-hidden">
      {/* Header row */}
      <div className="flex items-center gap-2 px-3 py-2">
        {/* Tool type badge */}
        <span
          className={`shrink-0 text-[9px] font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded ${
            isClientSide
              ? 'bg-purple-100 text-purple-700'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          {isClientSide ? 'browser' : 'server'}
        </span>

        {/* Tool name */}
        <span className="font-mono font-semibold text-[#003366] shrink-0">
          {toolName}
        </span>

        {/* Input summary */}
        {summary && (
          <span className="text-gray-500 truncate min-w-0 flex-1">{summary}</span>
        )}

        {/* Status badge */}
        <StatusBadge status={status} />

        {/* Expand toggle — only shown when there is a result to show */}
        {(status === 'done' || status === 'error') && (resultText || errorText) && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="ml-auto shrink-0 text-gray-400 hover:text-gray-600 transition-colors px-1"
            aria-label={expanded ? 'Collapse result' : 'Expand result'}
          >
            {expanded ? '▲' : '▼'}
          </button>
        )}
      </div>

      {/* Collapsible result panel */}
      {expanded && (
        <div className="border-t border-[#E5E9F0] px-3 py-2 bg-white">
          {errorText ? (
            <p className="text-red-600 font-mono text-[11px] whitespace-pre-wrap break-all">
              {errorText}
            </p>
          ) : resultText ? (
            <pre className="text-gray-700 font-mono text-[11px] whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
              {resultText}
            </pre>
          ) : null}
        </div>
      )}
    </div>
  );
}
