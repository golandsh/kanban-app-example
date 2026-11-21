# Frontend Overview

A Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS v4 frontend for the single-board Kanban workspace ("Kanban Studio"). Currently a client-only MVP using in-memory initial data.

## Tech Stack

- **Framework**: Next.js `16.1.6` (App Router, `src/app/`)
- **UI**: React `19.2.3`, Tailwind CSS v4 (`@tailwindcss/postcss`), `clsx`
- **Drag and Drop**: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- **Testing**: Vitest + React Testing Library + `jsdom` (unit/component), Playwright (E2E)
- **Linting**: ESLint 9 (`eslint-config-next`)

## Directory Structure

- `src/app/layout.tsx`: Root layout loading `Space_Grotesk` (`--font-display`) and `Manrope` (`--font-body`) Google Fonts and setting page metadata.
- `src/app/globals.css`: Tailwind v4 import and CSS custom properties for the color scheme (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, `--surface`, `--surface-strong`, `--stroke`, `--shadow`).
- `src/app/page.tsx`: Entry page rendering `<KanbanBoard />`.
- `src/lib/kanban.ts`: Core types (`Card`, `Column`, `BoardData`), `initialData` (5 fixed columns: Backlog, Discovery, In Progress, Review, Done; 8 sample cards), `moveCard` (intra-column reorder and cross-column move), and `createId`.
- `src/components/KanbanBoard.tsx`: Client component (`"use client"`) holding `board` state (`useState(initialData)`), `DndContext` with `PointerSensor` (6px activation distance) and `closestCorners`, `DragOverlay`, and handlers for `handleDragStart`, `handleDragEnd`, `handleRenameColumn`, `handleAddCard`, `handleDeleteCard`.
- `src/components/KanbanColumn.tsx`: Droppable column (`useDroppable`) with `SortableContext` (`verticalListSortingStrategy`), inline `<input>` for renaming the column title, empty-state drop zone, and `<NewCardForm />`.
- `src/components/KanbanCard.tsx`: Sortable card (`useSortable`) displaying `card.title`, `card.details`, and a `Remove` button. Note: card editing is not yet implemented in the initial MVP.
- `src/components/KanbanCardPreview.tsx`: Lightweight card preview rendered inside `<DragOverlay>` while dragging.
- `src/components/NewCardForm.tsx`: Collapsible form (`Add a card` button -> title input + details textarea + `Add card` / `Cancel`).
- `src/test/setup.ts`, `src/test/vitest.d.ts`: Vitest + `@testing-library/jest-dom` setup.
- `src/lib/kanban.test.ts`: Unit tests for `moveCard` and `createId`.
- `src/components/KanbanBoard.test.tsx`: Component/integration tests for rendering, column renaming, adding/removing cards.
- `tests/kanban.spec.ts`: Playwright E2E tests (runs against `npm run dev` on `127.0.0.1:3000`).

## Scripts (`package.json`)

- `npm run dev` / `npm run build` / `npm run start` / `npm run lint`
- `npm run test:unit` (Vitest)
- `npm run test:e2e` (Playwright)
- `npm run test:all` (both)

## Notes for Upcoming Integration

- `next.config.ts` currently has no `output: "export"` configured; static export will be needed so FastAPI can serve the built site at `/`.
- `KanbanBoard` currently initializes from `initialData` in memory with no API calls, auth gate, card editing, or AI chat sidebar yet.
