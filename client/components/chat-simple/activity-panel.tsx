'use client';

import { useState, useMemo } from 'react';
import { FileText, Bell, Terminal, Cpu, Cloud, PanelRightClose, PanelRightOpen, ChevronDown, ChevronRight, BookOpen } from 'lucide-react';
import { AuditLogEntry } from '@/types/stream';
import { DocumentInfo } from '@/types/chat';
import { useNotifications, type AppNotification } from '@/contexts/notification-context';
import AgentLogs from './agent-logs';
import BedrockLogs from './bedrock-logs';
import CloudWatchLogs from './cloudwatch-logs';
import type { KnowledgeSource } from './tool-use-display';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ActivityPanelProps {
  logs: AuditLogEntry[];
  clearLogs: () => void;
  documents: Record<string, DocumentInfo[]>;
  sessionId?: string;
  isStreaming: boolean;
  isOpen: boolean;
  onToggle: () => void;
  /** Raw Bedrock trace payloads collected via onBedrockTrace. */
  bedrockTraces?: Record<string, unknown>[];
  /** Knowledge sources from knowledge_search/fetch/search_far results. */
  knowledgeSources?: KnowledgeSource[];
}

type TabId = 'documents' | 'notifications' | 'logs' | 'bedrock' | 'cloudwatch' | 'sources';

interface TabDef {
  id: TabId;
  label: string;
  icon: typeof FileText;
}

const TABS: TabDef[] = [
  { id: 'documents',     label: 'Documents',     icon: FileText },
  { id: 'sources',       label: 'Sources',       icon: BookOpen },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'logs',          label: 'Agent Logs',    icon: Terminal },
  { id: 'bedrock',       label: 'Bedrock',       icon: Cpu },
  { id: 'cloudwatch',    label: 'CloudWatch',    icon: Cloud },
];

// ---------------------------------------------------------------------------
// Document type icon helper
// ---------------------------------------------------------------------------

import { DOCUMENT_TYPE_ICONS, type DocumentType } from '@/types/schema';

function getDocIcon(type: string): string {
  return DOCUMENT_TYPE_ICONS[type as DocumentType] ?? '\u{1F4C4}';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function DocumentsTab({
  documents,
  sessionId,
}: {
  documents: Record<string, DocumentInfo[]>;
  sessionId?: string;
}) {
  const allDocs = Object.values(documents).flat();

  const openDoc = (doc: DocumentInfo) => {
    const raw = doc.s3_key || doc.document_id || doc.title;
    const docId = encodeURIComponent(raw);
    const params = new URLSearchParams();
    if (sessionId) params.set('session', sessionId);
    window.open(`/documents/${docId}?${params.toString()}`, '_blank');
  };

  if (allDocs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-center px-4">
        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mb-3">
          <FileText className="w-5 h-5 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">No documents generated yet.</p>
        <p className="text-xs text-gray-400 mt-1">Documents will appear here as they&apos;re created.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {allDocs.map((doc, i) => (
        <button
          key={doc.document_id ?? i}
          type="button"
          onClick={() => openDoc(doc)}
          className="w-full text-left rounded-lg border border-[#D8DEE6] bg-white p-3 hover:shadow-sm transition"
          title="Open document"
        >
          <div className="flex items-start gap-2">
            <span className="text-lg shrink-0">{getDocIcon(doc.document_type)}</span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-[#003366] truncate">{doc.title}</p>
              <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-400">
                <span className="uppercase font-medium">{doc.document_type.replace(/_/g, ' ')}</span>
                {doc.word_count && <span>&middot; {doc.word_count.toLocaleString()} words</span>}
                {doc.status && (
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-medium ${
                    doc.status === 'saved' ? 'bg-green-100 text-green-700' :
                    doc.status === 'template' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {doc.status}
                  </span>
                )}
              </div>
              {doc.generated_at && (
                <p className="text-[10px] text-gray-400 mt-0.5">
                  {new Date(doc.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              )}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

/** Notification entry for document, package, and feedback updates. */
interface Notification {
  id: string;
  icon: 'doc_created' | 'doc_updated' | 'pkg_created' | 'feedback_sent';
  title: string;
  detail: string;
  status?: string;
  timestamp: string;
  payload?: Record<string, unknown>;
}

/** Document types that are part of an acquisition package vs standalone docs. */
const PACKAGE_DOC_TYPES = new Set([
  'sow', 'igce', 'acquisition_plan', 'justification', 'eval_criteria',
]);

function NotificationCard({ n, iconStyles }: {
  n: Notification;
  iconStyles: Record<Notification['icon'], { bg: string; glyph: string }>;
}) {
  const [expanded, setExpanded] = useState(false);
  const style = iconStyles[n.icon];

  return (
    <div
      key={n.id}
      className={`rounded-lg border border-[#D8DEE6] bg-white hover:shadow-sm transition ${n.payload ? 'cursor-pointer' : ''}`}
      onClick={() => n.payload && setExpanded(!expanded)}
    >
      <div className="flex items-start gap-2.5 px-3 py-2.5">
        <span className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm ${style.bg}`}>
          {style.glyph}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1">
            <p className="text-xs font-semibold text-[#003366]">{n.title}</p>
            {n.payload && (
              expanded
                ? <ChevronDown className="w-3 h-3 text-gray-400" />
                : <ChevronRight className="w-3 h-3 text-gray-400" />
            )}
          </div>
          <p className="text-[11px] text-gray-500 truncate">{n.detail}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {n.status && (
              <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-medium ${
                n.status === 'saved' ? 'bg-green-100 text-green-700' :
                n.status === 'template' ? 'bg-amber-100 text-amber-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {n.status}
              </span>
            )}
            <p className="text-[10px] text-gray-400">
              {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </p>
          </div>
        </div>
      </div>
      {expanded && n.payload && (
        <div className="border-t border-[#D8DEE6] px-3 py-2">
          <pre className="text-[10px] text-gray-600 font-mono whitespace-pre-wrap break-all bg-gray-50 rounded p-2 max-h-48 overflow-y-auto">
            {JSON.stringify(n.payload, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function NotificationsTab({ documents, appNotifications }: {
  documents: Record<string, DocumentInfo[]>;
  appNotifications: AppNotification[];
}) {
  const notifications = useMemo(() => {
    const items: Notification[] = [];
    const allDocs = Object.values(documents).flat();

    // Track package doc types seen — if multiple, it's a package update
    const packageTypes = allDocs.filter(d => PACKAGE_DOC_TYPES.has(d.document_type));

    // Package-level notification if 2+ package docs exist
    if (packageTypes.length >= 2) {
      const latest = packageTypes.reduce((a, b) =>
        new Date(b.generated_at ?? 0).getTime() > new Date(a.generated_at ?? 0).getTime() ? b : a
      );
      items.push({
        id: 'pkg-update',
        icon: 'pkg_created',
        title: 'Acquisition package updated',
        detail: `${packageTypes.length} documents — ${packageTypes.map(d => d.document_type.replace(/_/g, ' ')).join(', ')}`,
        timestamp: latest.generated_at ?? new Date().toISOString(),
      });
    }

    // Individual document notifications
    for (const doc of allDocs) {
      items.push({
        id: `doc-${doc.document_id ?? doc.title}`,
        icon: 'doc_created',
        title: doc.title,
        detail: doc.document_type.replace(/_/g, ' '),
        status: doc.status,
        timestamp: doc.generated_at ?? new Date().toISOString(),
      });
    }

    // Feedback notifications from the app notification context
    for (const an of appNotifications) {
      items.push({
        id: an.id,
        icon: an.icon,
        title: an.title,
        detail: an.detail,
        timestamp: an.timestamp,
        payload: an.payload,
      });
    }

    // Sort newest first
    items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return items;
  }, [documents, appNotifications]);

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-center px-4">
        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mb-3">
          <Bell className="w-5 h-5 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">No notifications yet.</p>
        <p className="text-xs text-gray-400 mt-1">Document updates and feedback confirmations will appear here.</p>
      </div>
    );
  }

  const iconStyles: Record<Notification['icon'], { bg: string; glyph: string }> = {
    doc_created:    { bg: 'bg-blue-100',    glyph: '\u{1F4C4}' },
    doc_updated:    { bg: 'bg-amber-100',   glyph: '\u{1F4DD}' },
    pkg_created:    { bg: 'bg-indigo-100',  glyph: '\u{1F4E6}' },
    feedback_sent:  { bg: 'bg-emerald-100', glyph: '\u{2705}' },
  };

  return (
    <div className="space-y-1.5">
      {notifications.map((n) => (
        <NotificationCard key={n.id} n={n} iconStyles={iconStyles} />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sources Tab
// ---------------------------------------------------------------------------

const SOURCE_TOOL_LABELS: Record<string, { icon: string; label: string }> = {
  knowledge_search: { icon: '🔎', label: 'KB Search' },
  knowledge_fetch:  { icon: '📖', label: 'KB Read' },
  search_far:       { icon: '📜', label: 'FAR Search' },
};

const AUTHORITY_COLORS: Record<string, string> = {
  mandatory: 'bg-red-100 text-red-700',
  regulatory: 'bg-orange-100 text-orange-700',
  policy: 'bg-blue-100 text-blue-700',
  guidance: 'bg-green-100 text-green-700',
  reference: 'bg-gray-100 text-gray-600',
  template: 'bg-violet-100 text-violet-700',
};

function SourcesTab({ sources }: { sources: KnowledgeSource[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-center px-4">
        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mb-3">
          <BookOpen className="w-5 h-5 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">No knowledge sources yet.</p>
        <p className="text-xs text-gray-400 mt-1">
          Documents referenced by the agent will appear here.
        </p>
      </div>
    );
  }

  // Group by source_tool
  const byTool = new Map<string, KnowledgeSource[]>();
  for (const src of sources) {
    const arr = byTool.get(src.source_tool) ?? [];
    arr.push(src);
    byTool.set(src.source_tool, arr);
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-3 text-[10px] text-gray-500">
        <span>{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
        {byTool.has('knowledge_search') && (
          <span>{byTool.get('knowledge_search')!.length} searched</span>
        )}
        {byTool.has('knowledge_fetch') && (
          <span>{byTool.get('knowledge_fetch')!.length} read</span>
        )}
        {byTool.has('search_far') && (
          <span>{byTool.get('search_far')!.length} FAR sections</span>
        )}
      </div>

      {/* Source cards */}
      <div className="space-y-1.5">
        {sources.map((src) => {
          const toolMeta = SOURCE_TOOL_LABELS[src.source_tool] || { icon: '📄', label: src.source_tool };
          const isExpanded = expandedId === src.document_id;

          return (
            <div
              key={src.document_id || src.title}
              className="rounded-lg border border-gray-200 bg-white hover:shadow-sm transition"
            >
              <button
                type="button"
                className="w-full text-left px-3 py-2.5"
                onClick={() => setExpandedId(isExpanded ? null : src.document_id)}
              >
                <div className="flex items-start gap-2">
                  <span className="text-sm shrink-0 mt-0.5">{toolMeta.icon}</span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-[#003366] truncate">{src.title}</p>
                    {src.summary && (
                      <p className="text-[10px] text-gray-500 mt-0.5 line-clamp-2">{src.summary}</p>
                    )}
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      <span className="text-[8px] text-gray-400 bg-gray-50 px-1 rounded uppercase font-bold">
                        {toolMeta.label}
                      </span>
                      {src.authority_level && (
                        <span className={`px-1 py-0.5 rounded text-[8px] font-bold uppercase ${
                          AUTHORITY_COLORS[src.authority_level] ?? AUTHORITY_COLORS.reference
                        }`}>
                          {src.authority_level}
                        </span>
                      )}
                      {src.document_type && src.document_type !== 'far_regulation' && (
                        <span className="text-[9px] text-gray-400 font-mono">{src.document_type}</span>
                      )}
                      {src.confidence_score ? (
                        <span className={`text-[9px] font-mono ${
                          src.confidence_score >= 0.8 ? 'text-green-600' :
                          src.confidence_score >= 0.5 ? 'text-amber-600' : 'text-gray-400'
                        }`}>
                          {(src.confidence_score * 100).toFixed(0)}%
                        </span>
                      ) : null}
                      {src.primary_agent && (
                        <span className="text-[9px] text-violet-500">agent: {src.primary_agent}</span>
                      )}
                      {src.content_length ? (
                        <span className="text-[9px] text-gray-400">
                          {src.content_length.toLocaleString()} chars
                        </span>
                      ) : null}
                    </div>
                  </div>
                  {src.s3_key && (
                    <span
                      className="text-[9px] text-blue-500 hover:text-blue-700 shrink-0 mt-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(`/documents/${encodeURIComponent(src.s3_key!)}`, '_blank');
                      }}
                    >
                      View →
                    </span>
                  )}
                </div>
              </button>

              {/* Expanded content preview */}
              {isExpanded && (
                <div className="border-t border-gray-200 px-3 py-2 bg-gray-50/50">
                  {src.content ? (
                    <pre className="text-[10px] font-mono text-gray-700 whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                      {src.content.slice(0, 2000)}
                      {src.content.length > 2000 ? '\n\n... [truncated]' : ''}
                    </pre>
                  ) : src.keywords && src.keywords.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {src.keywords.map((kw, i) => (
                        <span key={i} className="text-[9px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                          {kw}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[10px] text-gray-400 italic">No preview available</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Panel
// ---------------------------------------------------------------------------

export default function ActivityPanel({
  logs,
  clearLogs,
  documents,
  sessionId,
  isStreaming,
  isOpen,
  onToggle,
  bedrockTraces = [],
  knowledgeSources = [],
}: ActivityPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>('logs');
  const { notifications: appNotifications } = useNotifications();

  const docCount = Object.values(documents).flat().length;

  const notifCount = docCount + appNotifications.length;

  // Collapsed strip
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="w-9 shrink-0 border-l border-[#D8DEE6] bg-[#F5F7FA] hover:bg-[#EDF0F4] transition flex flex-col items-center justify-center gap-1.5 cursor-pointer"
        title="Open panel"
      >
        <PanelRightOpen className="w-4 h-4 text-gray-400" />
      </button>
    );
  }

  return (
    <div className="w-[380px] shrink-0 border-l border-[#D8DEE6] bg-white flex flex-col">
      {/* Tab bar */}
      <div className="flex flex-wrap items-center gap-1 p-2 bg-[#F5F7FA] border-b border-[#D8DEE6]">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          // Badge counts
          const bedrockCount = bedrockTraces.length > 0 ? bedrockTraces.length : logs.filter(l => l.type === 'bedrock_trace').length;
          const badge =
            tab.id === 'logs'      && logs.length > 0       ? logs.length :
            tab.id === 'bedrock'   && bedrockCount > 0      ? bedrockCount :
            tab.id === 'documents' && docCount > 0          ? docCount :
            tab.id === 'notifications' && notifCount > 0    ? notifCount :
            tab.id === 'sources'   && knowledgeSources.length > 0 ? knowledgeSources.length :
            0;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition ${
                activeTab === tab.id
                  ? 'bg-white text-[#003366] shadow-sm border border-[#D8DEE6]'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              {badge > 0 && (
                <span className="ml-0.5 px-1.5 py-0.5 rounded-full text-[9px] bg-[#003366] text-white font-bold min-w-[18px] text-center">
                  {badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Collapse toggle */}
        <button
          onClick={onToggle}
          className="ml-auto p-1 text-gray-400 hover:text-gray-600 rounded transition"
          title="Collapse panel"
        >
          <PanelRightClose className="w-4 h-4" />
        </button>
      </div>

      {/* Tab-specific header (Agent Logs clear button) */}
      {activeTab === 'logs' && logs.length > 0 && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#D8DEE6]">
          <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">
            {logs.length} event{logs.length !== 1 ? 's' : ''}
            {isStreaming && <span className="ml-2 inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />}
          </span>
          <button
            onClick={clearLogs}
            className="text-[10px] text-red-500 hover:text-red-700 font-medium"
          >
            Clear
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'documents'     && <DocumentsTab documents={documents} sessionId={sessionId} />}
        {activeTab === 'notifications' && <NotificationsTab documents={documents} appNotifications={appNotifications} />}
        {activeTab === 'logs'          && <AgentLogs logs={logs} />}
        {activeTab === 'bedrock'       && <BedrockLogs bedrockTraces={bedrockTraces} logs={logs} />}
        {activeTab === 'cloudwatch'    && <CloudWatchLogs sessionId={sessionId} />}
        {activeTab === 'sources'       && <SourcesTab sources={knowledgeSources} />}
      </div>
    </div>
  );
}
