/**
 * @deprecated This file has been replaced by the new expertise system.
 *
 * The expertise system now tracks user behavioral data for personalization,
 * not static domain knowledge.
 *
 * See:
 * - /types/expertise.ts - Type definitions
 * - /hooks/use-expertise.ts - Hook for tracking actions
 * - Backend: /server/shared/expertise.py - Expertise store
 *
 * DELETE THIS FILE - it's only kept temporarily to avoid import errors.
 */

// Empty exports to prevent import errors
export const EXPERTISE_OVERVIEW = {};
export const PRODUCTION_DEPLOYMENT = { cloudfront_url: '', distribution_id: '' };
export const LOCAL_DEVELOPMENT = { directory: '', port: 0, commands: { dev: '' } };
export const COMPONENTS = {};
export const SCHEMA_TYPES = { entities: [], enums: [] };
export const UI_PATTERNS = { layout: { type: '' }, colors: {} };
export const DEPLOYMENT_WORKFLOW = {
  build: { command: '', output: '' },
  deploy: { command: '', actions: [] },
};
export const TROUBLESHOOTING: unknown[] = [];
export const BEST_PRACTICES = {};
