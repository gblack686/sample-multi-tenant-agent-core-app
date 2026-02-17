# Meeting Transcripts

This directory contains meeting transcripts and their AI-generated summaries for the EAGLE project.

## Folder Structure

```
meeting-transcripts/
├── README.md
├── YYYYMMDD-meeting-title/
│   ├── raw-transcripts/
│   │   └── Original Meeting File.docx
│   └── summaries/
│       └── SUMMARY-YYYYMMDD-meeting-title.md
├── 20260121-eagle-requirement-discussion/
│   ├── raw-transcripts/
│   │   └── EAGLE - 20260121 - Requirement Discussion.docx
│   └── summaries/
│       └── SUMMARY-20260121-eagle-requirement-discussion.md
└── ...
```

**Date-first naming** (`YYYYMMDD-title`) ensures folders sort chronologically.

## Adding New Transcripts

1. Drop `.docx` transcript files into this directory
2. Run `git pull` or the processor hook will detect new files
3. Files are automatically organized into dated folders
4. Summaries are generated via `/summarize_meeting` command

## Summary Format

Generated summaries include:
- Executive summary
- Attendee list with roles
- Key discussion points
- Decisions made
- Action items with owners
- Technical notes
- Risks & blockers
- Next steps

## Automations

### Meeting Transcript Processor Hook

**Location:** `.claude/hooks/meeting_transcript_processor.py`

**Trigger:** Fires after `git pull` or file copy operations

**Processing Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. DETECT                                                  │
│     Post-tool hook fires after git pull / file operations   │
│     Scans meeting-transcripts/ for unprocessed .docx files  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. NORMALIZE                                               │
│     Extract date from filename (YYYYMMDD pattern)           │
│     Generate folder name: {date}-{title-slug}               │
│     Example: "EAGLE - 20260121 - Req Discussion.docx"       │
│           → "20260121-eagle-req-discussion"                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. ORGANIZE                                                │
│     Create folder structure:                                │
│       {date}-{title}/                                       │
│         ├── raw-transcripts/                                │
│         └── summaries/                                      │
│     Move .docx to raw-transcripts/                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. CHECK SUMMARY                                           │
│     Look for existing SUMMARY-*.md in summaries/            │
│     If missing, flag for summarization                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. NOTIFY                                                  │
│     Output system reminder listing transcripts needing      │
│     summaries with suggested /summarize_meeting commands    │
└─────────────────────────────────────────────────────────────┘
```

### Manual Processing

Run the processor directly:

```bash
python .claude/hooks/meeting_transcript_processor.py
```

### Summarize Meeting Command

**Usage:** `/summarize_meeting "path/to/transcript.docx"`

Generates a structured markdown summary with:
- Meeting metadata (date, duration, type)
- Attendee table
- Discussion points organized by topic
- Decision log
- Action items table with owners and priorities
- Technical notes and architecture decisions
- Risk register
- Next steps

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Folder | `YYYYMMDD-title-slug` | `20260121-eagle-sync` |
| Raw transcript | Original filename | `EAGLE sync.docx` |
| Summary | `SUMMARY-YYYYMMDD-title.md` | `SUMMARY-20260121-eagle-sync.md` |

## Supported File Types

| Format | Extension | Notes |
|--------|-----------|-------|
| Word Document | `.docx` | Primary format (Teams exports) |
| Word Legacy | `.doc` | May need conversion |
| Plain Text | `.txt` | Direct processing |
| Markdown | `.md` | Direct processing |

## Migration Notes

Existing files in the root directory:
- `.docx` files → Auto-organized by processor
- `SUMMARY-*.md` files → Move manually to corresponding `summaries/` folder
- `.txt` files → Move manually or leave in root

## Related Documentation

- [EAGLE POC Implementation Plan](../EAGLE-POC-implementation-plan.md)
- [Summarize Meeting Command](../../.claude/commands/summarize_meeting.md)
