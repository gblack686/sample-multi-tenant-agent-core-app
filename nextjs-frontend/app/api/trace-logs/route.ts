import { NextResponse } from 'next/server';
import { readFile, readdir, stat } from 'fs/promises';
import { join } from 'path';

const PROJECT_ROOT = join(process.cwd(), '..');

/**
 * GET /api/trace-logs
 *
 * Query params:
 *   ?list=1          → returns metadata for all trace_logs*.json files
 *   ?run=<filename>  → returns data from a specific file (e.g. trace_logs.json)
 *   (none)           → returns the latest trace_logs.json (backward compat)
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const listMode = searchParams.get('list');
  const runFile = searchParams.get('run');

  try {
    if (listMode) {
      // List all trace_logs*.json files with metadata
      const files = await readdir(PROJECT_ROOT);
      const traceFiles = files.filter(
        (f) => f.startsWith('trace_logs') && f.endsWith('.json')
      );

      const runs = await Promise.all(
        traceFiles.map(async (filename) => {
          const filePath = join(PROJECT_ROOT, filename);
          const fileStat = await stat(filePath);
          try {
            const content = JSON.parse(
              await readFile(filePath, 'utf-8')
            );
            return {
              filename,
              timestamp: content.timestamp || fileStat.mtime.toISOString(),
              run_id: content.run_id || filename,
              total_tests: content.total_tests ?? Object.keys(content.results || {}).length,
              passed: content.passed ?? 0,
              failed: content.failed ?? 0,
              skipped: content.skipped ?? 0,
              size_bytes: fileStat.size,
            };
          } catch {
            return {
              filename,
              timestamp: fileStat.mtime.toISOString(),
              run_id: filename,
              total_tests: 0,
              passed: 0,
              failed: 0,
              skipped: 0,
              size_bytes: fileStat.size,
              parse_error: true,
            };
          }
        })
      );

      // Sort newest first
      runs.sort(
        (a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      return NextResponse.json({ runs });
    }

    // Load a specific run or the default trace_logs.json
    const targetFile = runFile || 'trace_logs.json';
    // Prevent directory traversal
    if (targetFile.includes('..') || targetFile.includes('/') || targetFile.includes('\\')) {
      return NextResponse.json({ error: 'Invalid filename' }, { status: 400 });
    }

    const filePath = join(PROJECT_ROOT, targetFile);
    const content = await readFile(filePath, 'utf-8');
    const data = JSON.parse(content);
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      {
        error:
          'trace_logs.json not found. Run python test_eagle_sdk_eval.py to generate results.',
      },
      { status: 404 }
    );
  }
}
