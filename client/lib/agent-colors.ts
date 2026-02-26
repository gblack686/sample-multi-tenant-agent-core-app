/**
 * Multi-Agent Color Configuration
 *
 * Each agent in the EAGLE system has a unique color scheme for visual tracking
 * in the chat interface and audit logs.
 *
 * Colors align with backend schema definitions in:
 * .claude/commands/experts/backend/expertise.yaml
 */

import {
  SubmissionSource,
  ReviewStatus,
  SUBMISSION_SOURCE_COLORS,
  REVIEW_STATUS_COLORS,
  SUBMISSION_SOURCE_CLASSES,
  REVIEW_STATUS_CLASSES,
} from '@/types/schema';

// Re-export schema colors for convenience
export {
  SUBMISSION_SOURCE_COLORS,
  REVIEW_STATUS_COLORS,
  SUBMISSION_SOURCE_CLASSES,
  REVIEW_STATUS_CLASSES,
};

export interface AgentColorScheme {
  bg: string;
  text: string;
  border: string;
  badge: string;
  icon: string;
  gradient: string;
}

// Helper to get submission source styling
export function getSubmissionSourceClass(source: SubmissionSource): string {
  return SUBMISSION_SOURCE_CLASSES[source] || SUBMISSION_SOURCE_CLASSES.user;
}

// Helper to get review status styling
export function getReviewStatusClass(status: ReviewStatus): string {
  return REVIEW_STATUS_CLASSES[status] || REVIEW_STATUS_CLASSES.pending;
}

export const AGENT_COLORS: Record<string, AgentColorScheme> = {
  // Supervisor Agent - Gray (orchestration layer)
  'supervisor': {
    bg: 'bg-gray-50',
    text: 'text-gray-700',
    border: 'border-gray-200',
    badge: 'bg-gray-100 text-gray-600',
    icon: 'bg-gray-600',
    gradient: 'from-gray-500 to-gray-600',
  },
  
  // OA Intake Agent - Blue (primary interaction)
  'oa-intake': {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-700',
    icon: 'bg-blue-600',
    gradient: 'from-blue-500 to-blue-600',
  },
  
  // Knowledge Retrieval Agent - Green (RAG/search)
  'knowledge-retrieval': {
    bg: 'bg-green-50',
    text: 'text-green-700',
    border: 'border-green-200',
    badge: 'bg-green-100 text-green-700',
    icon: 'bg-green-600',
    gradient: 'from-green-500 to-green-600',
  },
  
  // Document Generator Agent - Purple (document creation)
  'document-generator': {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200',
    badge: 'bg-purple-100 text-purple-700',
    icon: 'bg-purple-600',
    gradient: 'from-purple-500 to-purple-600',
  },
  
  // Default/Unknown - Amber (fallback)
  'default': {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    badge: 'bg-amber-100 text-amber-700',
    icon: 'bg-amber-600',
    gradient: 'from-amber-500 to-amber-600',
  },
};

export const AGENT_NAMES: Record<string, string> = {
  'supervisor': 'Supervisor',
  'oa-intake': 'OA Intake Agent',
  'knowledge-retrieval': 'Knowledge Retrieval',
  'document-generator': 'Document Generator',
};

export const AGENT_ICONS: Record<string, string> = {
  'supervisor': 'S',
  'oa-intake': 'E',  // EAGLE
  'knowledge-retrieval': 'K',
  'document-generator': 'D',
};

export function getAgentColors(agentId: string): AgentColorScheme {
  return AGENT_COLORS[agentId] || AGENT_COLORS['default'];
}

export function getAgentName(agentId: string): string {
  return AGENT_NAMES[agentId] || agentId;
}

export function getAgentIcon(agentId: string): string {
  return AGENT_ICONS[agentId] || agentId.charAt(0).toUpperCase();
}


