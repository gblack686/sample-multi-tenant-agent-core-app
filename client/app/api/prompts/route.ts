import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

// Maps prompt keys to their file paths (relative to project root)
const PROMPT_FILES: Record<string, { title: string; path: string }> = {
  supervisor: {
    title: 'EAGLE Supervisor Agent',
    path: 'eagle-plugin/agent/supervisor.md',
  },
  intake: {
    title: 'OA Intake Skill',
    path: 'eagle-plugin/skills/oa-intake/SKILL.md',
  },
  docgen: {
    title: 'Document Generator Skill',
    path: 'eagle-plugin/skills/document-generator/SKILL.md',
  },
  compliance: {
    title: 'Compliance Skill',
    path: 'eagle-plugin/skills/compliance/SKILL.md',
  },
  'tech-review': {
    title: 'Tech Review Skill',
    path: 'eagle-plugin/skills/tech-review/SKILL.md',
  },
  'knowledge-retrieval': {
    title: 'Knowledge Retrieval Skill',
    path: 'eagle-plugin/skills/knowledge-retrieval/SKILL.md',
  },
};

export async function GET() {
  const projectRoot = join(process.cwd(), '..');
  const results: Record<string, { title: string; file: string; content: string }> = {};

  for (const [key, meta] of Object.entries(PROMPT_FILES)) {
    try {
      const filePath = join(projectRoot, meta.path);
      const content = await readFile(filePath, 'utf-8');
      results[key] = {
        title: meta.title,
        file: meta.path,
        content,
      };
    } catch {
      results[key] = {
        title: meta.title,
        file: meta.path,
        content: `[Error: Could not read ${meta.path}]`,
      };
    }
  }

  return NextResponse.json(results);
}
