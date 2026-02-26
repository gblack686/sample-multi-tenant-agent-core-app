# Plan: Fix Document Checklist Status & Linking

## Task Description
The document checklist in the acquisition pane (`document-checklist.tsx`) has two critical bugs:
1. **Wrong status logic** - Documents are marked "completed" based on intake field presence, not actual document generation
2. **Template content instead of generated docs** - Clicking a document shows hardcoded inline templates, not actual generated documents from `document-store.ts`

## Objective
Make the document checklist accurately reflect document generation status and link to actual generated documents when available.

## Problem Statement

### Current (Wrong) Behavior:
```typescript
// Status based on intake fields, NOT actual documents
const isSpecsDone = !!data.equipmentType;
status: isSpecsDone ? 'completed' : 'in-progress'

// Content from hardcoded templates
const getDocContent = (docId) => {
    'sow': `# Statement of Work: ${req}...`  // NOT the actual generated doc
}
```

### Expected Behavior:
| Status | Meaning |
|--------|---------|
| `pending` | Intake not started or minimal data collected |
| `in-progress` | Intake data being gathered, document not yet generated |
| `completed` | Actual document generated via `create_document` tool |

When a document is "completed", clicking it should:
1. If generated document exists: Open document viewer page (`/documents/${document_id}`)
2. If no document yet: Show template preview (current behavior, but label as "Preview")

## Solution Approach

1. **Accept `sessionId` prop** - Pass the current session ID to look up the package from `document-store.ts`
2. **Merge checklist data** - Combine the static document list with actual package checklist state from localStorage
3. **Fix status derivation** - A document is "completed" only when `PackageChecklist.document_id` exists
4. **Fix content source** - Fetch actual content from `getGeneratedDocument(document_id)` when available
5. **Add navigation** - "Completed" documents open in document viewer page; others show inline preview

## Relevant Files

### Files to Modify

- **`client/components/checklist/document-checklist.tsx`** - Main component with bugs
- **`client/components/chat/chat-interface.tsx`** - Parent component, needs to pass sessionId

### Supporting Files (Read-Only Reference)

- **`client/lib/document-store.ts`** - `getPackage()`, `getGeneratedDocument()` functions
- **`client/app/documents/[id]/page.tsx`** - Document viewer page (target for navigation)
- **`client/types/schema.ts`** - `DocumentType`, `DocumentStatus` types

## Implementation Phases

### Phase 1: Add sessionId Prop & Package Lookup
Pass session context to the checklist so it can look up actual package state.

### Phase 2: Fix Status Logic
Derive status from actual `PackageChecklist.document_id` presence, not intake fields.

### Phase 3: Fix Content & Navigation
Show actual generated document content and navigate to viewer for completed docs.

## Step by Step Tasks

### 1. Update DocumentChecklistProps Interface

In `document-checklist.tsx`:

- Add `sessionId?: string` to props interface
- Import `getPackage`, `getGeneratedDocument` from `@/lib/document-store`
- Import `DocumentType` from `@/types/schema`

```typescript
import { getPackage, getGeneratedDocument, PackageChecklist } from '@/lib/document-store';

interface DocumentChecklistProps {
    messages: Message[];
    data: AcquisitionData;
    sessionId?: string;  // NEW: for package lookup
}
```

### 2. Look Up Package Checklist State

Add package lookup at component start:

```typescript
export default function DocumentChecklist({ messages, data, sessionId }: DocumentChecklistProps) {
    // Look up actual package state from localStorage
    const packageData = sessionId ? getPackage(sessionId) : null;
    const packageChecklist = packageData?.checklist || [];

    // Create a map for quick lookup: document_type -> checklist item
    const checklistMap = new Map<string, PackageChecklist>();
    packageChecklist.forEach(item => {
        checklistMap.set(item.document_type, item);
    });
    // ...
}
```

### 3. Refactor Document Status Derivation

Replace the current intake-field-based logic with document-store-based logic:

```typescript
// Map document IDs to document_type keys used in document-store
const DOC_TYPE_MAP: Record<string, DocumentType> = {
    'sow': 'sow',
    'igce': 'igce',
    'market-research': 'market_research',
    'plan': 'acquisition_plan',
    'funding': 'funding_doc',
    'urgency': 'justification',  // urgency justification maps to justification type
};

// Derive status from actual package state
const getDocStatus = (docId: string): 'pending' | 'in-progress' | 'completed' => {
    const docType = DOC_TYPE_MAP[docId];
    const checklistItem = checklistMap.get(docType);

    // If document_id exists in checklist, it's completed
    if (checklistItem?.document_id) {
        return 'completed';
    }

    // Otherwise, use intake fields to determine in-progress vs pending
    const hasStartedIntake = messages.length > 0;
    const hasRelevantData = getRelevantDataForDoc(docId, data);

    if (hasRelevantData) return 'in-progress';
    if (hasStartedIntake) return 'in-progress';
    return 'pending';
};

// Helper to check if relevant intake data exists for a doc type
const getRelevantDataForDoc = (docId: string, data: AcquisitionData): boolean => {
    switch (docId) {
        case 'sow': return !!(data.requirement || data.equipmentType);
        case 'igce': return !!data.estimatedValue;
        case 'market-research': return !!(data.requirement || data.equipmentType);
        case 'plan': return !!(data.requirement && data.estimatedValue);
        case 'funding': return !!data.funding;
        case 'urgency': return !!data.urgency;
        default: return false;
    }
};
```

### 4. Update Documents Array to Use New Status Logic

Replace the static `documents` array with one that uses the new status derivation:

```typescript
const documents = [
    {
        id: 'sow',
        name: 'Statement of Work (SOW)',
        status: getDocStatus('sow'),
        description: 'Equipment specs, installation, training',
        documentId: checklistMap.get('sow')?.document_id,
    },
    {
        id: 'igce',
        name: 'Independent Government Cost Estimate (IGCE)',
        status: getDocStatus('igce'),
        description: 'Market research, vendor quotes',
        documentId: checklistMap.get('igce')?.document_id,
    },
    // ... repeat for all document types
];
```

### 5. Fix Content Retrieval & Navigation

Update click handler to navigate to document viewer for completed docs:

```typescript
const handleDocClick = (doc: typeof documents[0]) => {
    if (doc.status === 'completed' && doc.documentId) {
        // Open actual document in viewer page
        const params = new URLSearchParams();
        if (sessionId) params.set('session', sessionId);
        window.open(`/documents/${doc.documentId}?${params.toString()}`, '_blank');
    } else {
        // Show inline preview (template) for non-completed docs
        setSelectedDoc({
            id: doc.id,
            name: doc.name,
            content: getDocContent(doc.id),
            isTemplate: true,  // Flag to show "Preview" label
        });
    }
};
```

Update the onClick in the JSX:

```typescript
<div
    key={idx}
    onClick={() => handleDocClick(doc)}
    // ... rest of props
>
```

### 6. Update Modal Title for Template Preview

Show "Preview" label when viewing template vs actual document:

```typescript
{selectedDoc && (
    <div className="fixed inset-0 z-50 ...">
        <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            {selectedDoc.isTemplate ? 'Preview: ' : ''}{selectedDoc.name}
            {selectedDoc.isTemplate && (
                <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full ml-2">
                    Template
                </span>
            )}
        </h3>
        // ... rest of modal
    </div>
)}
```

### 7. Pass sessionId from Parent Component

In `chat-interface.tsx`, pass the session ID to DocumentChecklist:

```typescript
// Find where DocumentChecklist is rendered (around line 602)
<DocumentChecklist
    messages={messages}
    data={acquisitionData}
    sessionId={sessionId}  // ADD THIS
/>
```

Note: The parent component needs access to `sessionId`. Check if it's available in the component or needs to be added via context.

### 8. Add Visual Indicator for Viewable Documents

Add an icon to show that completed documents can be opened:

```typescript
{doc.status === 'completed' && doc.documentId && (
    <ExternalLink className="w-4 h-4 text-green-600 shrink-0" />
)}
{doc.status !== 'completed' && (
    <Eye className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
)}
```

Import `ExternalLink` from lucide-react.

### 9. Validate TypeScript Compilation

Run TypeScript check to ensure no type errors:

```bash
cd client && npx tsc --noEmit
```

## Testing Strategy

### Manual Testing Flow:

1. **Start fresh session** - Verify all documents show "pending" status
2. **Begin intake** - Provide some data, verify relevant docs show "in-progress"
3. **Generate document** - Ask agent to "Generate a SOW for IT services"
4. **Verify status change** - SOW should now show "completed" with green checkmark
5. **Click completed doc** - Should open `/documents/{id}` in new tab
6. **Click in-progress doc** - Should show template preview modal with "Template" badge
7. **Navigate away and back** - Status should persist (from localStorage)

### Edge Cases:

- Session without any package data (new user)
- Session with partial package data
- Document generated but sessionStorage cleared
- Multiple documents of same type

## Acceptance Criteria

1. Documents show "completed" status ONLY when `document_id` exists in package checklist
2. Clicking completed documents opens document viewer page in new tab
3. Clicking non-completed documents shows template preview with "Template" badge
4. Progress bar and completion count reflect actual generated documents
5. Status persists across page refreshes (via localStorage)
6. TypeScript compiles without errors

## Validation Commands

Execute these commands to validate the implementation:

- `cd client && npx tsc --noEmit` - TypeScript compilation check
- `cd client && npm run build` - Full build validation
- Manual browser testing with the flow described above

## Notes

### Relationship to Existing Spec

This plan complements `.claude/specs/fix-document-viewer-bugs.md` which fixes:
- sessionStorage key mismatch
- Same-tab navigation in document-card.tsx
- Document persistence in simple-chat-interface.tsx

This plan focuses specifically on the `document-checklist.tsx` component used in the advanced chat interface.

### Document Type Mapping

The checklist uses different IDs than the document-store:
| Checklist ID | document-store Type |
|--------------|---------------------|
| `sow` | `sow` |
| `igce` | `igce` |
| `market-research` | `market_research` |
| `plan` | `acquisition_plan` |
| `funding` | `funding_doc` |
| `urgency` | `justification` |

### Progress Bar Calculation

After this fix, `overallProgress` should be calculated based on actual completed documents:
```typescript
const completedCount = documents.filter(d => d.status === 'completed').length;
const overallProgress = Math.round((completedCount / documents.length) * 100);
```

This ensures the progress bar reflects actual document generation, not just intake field completion.
