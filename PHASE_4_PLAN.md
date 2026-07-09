# Phase 4: Workspace Selection Modal + File CRUD

## T1: Phase 4: Workspace modal + file CRUD in explorer

### T1.1: Add DELETE endpoint to backend ide.py
- **Status**: open
- **Description**: Add `DELETE /api/ide/file` route to `apps/gateway/routes/ide.py`. Use `os.remove()` for files, `shutil.rmtree()` for directories. Include `_is_safe_path()` validation and a confirmation param to prevent accidental deletes of large dirs. Add `DeleteFileRequest(BaseModel)` with `path: str` and `confirm: bool = False`.
- **Files**: `apps/gateway/routes/ide.py`
- **Depends on**: none

### T1.2: Fix FileEntry field name mismatch
- **Status**: open
- **Description**: Backend returns `type: "directory" | "file"` but `FileTree.tsx` checks `entry.isDir` and `workspace.ts` store uses `isDirectory`. Unify to a single convention. Best approach: normalize at the API response level — add `isDir: bool` to the backend response alongside `type`, OR update all frontend code to use `type`. Recommend: add `isDir` alias in backend `list_files()` response so FileTree.tsx works without changes, and update workspace store `FileEntry` to match.
- **Files**: `apps/gateway/routes/ide.py`, `apps/web/lib/stores/workspace.ts`, `apps/web/components/FileTree.tsx`
- **Depends on**: T1.1

### T1.3: Create WorkspaceModal component
- **Status**: open
- **Description**: Create `components/WorkspaceModal.tsx`. Inline modal pattern (matching `preview/page.tsx` style): `fixed inset-0 bg-black/80 flex items-center justify-center z-50`. Content: `bg-[#1a1a22] border border-[#2a2a36] rounded-xl` card with:
  - Header: "Select Workspace"
  - Input field: `bg-[#0a0a12] border border-[#2a2a36] rounded-lg` for workspace path
  - "Set Workspace" button (accent `#00e5ff` bg or border)
  - On submit: POST `/api/ide/workspace` → GET `/api/ide/files` → store in WorkspaceStore + localStorage → close
  - Click-outside-to-close, Escape key to close
  - Show current workspace path if already set
- **Files**: `apps/web/components/WorkspaceModal.tsx` (new)
- **Depends on**: T1.2

### T1.4: Add file CRUD + context menu to FileTree.tsx
- **Status**: open
- **Description**: Enhance `components/FileTree.tsx`:
  1. **Right-click context menu**: Custom div positioned at mouse coords (`fixed` + `top/left`), matching dark theme. Items: "New File", "New Folder", "Delete".
  2. **New File/Folder**: On click, show inline input (replace the clicked entry's name area with an input). On Enter: POST `/api/ide/file` with `path` + `content: ""` (files) or create dir via a new param. Refresh tree after.
  3. **Delete**: Confirmation dialog (small inline modal or browser `confirm()`), then DELETE `/api/ide/file`. Refresh tree after.
  4. **Active file indicator**: Read `useSessionStore` events, find `tool_call` events with `write_file`/`edit_file` tool names, extract target paths, show pulsing dot (`animate-pulse` + green dot) next to files currently being modified.
  5. **Wire to WorkspaceStore**: Use `useWorkspaceStore.fileTree` and `setFileTree` instead of local state. Add `refreshTree()` helper that fetches and updates both local display and store.
- **Files**: `apps/web/components/FileTree.tsx`
- **Depends on**: T1.1, T1.2, T1.3

### T1.5: Wire workspace modal + sidebar header into ide/page.tsx
- **Status**: open
- **Description**: Modify `app/ide/page.tsx`:
  1. Add workspace name/path display in the left sidebar header area (above tabs). Make it clickable → opens `WorkspaceModal`.
  2. On mount: check `localStorage` for saved workspace root. If present, set in store and fetch tree. If absent, show `WorkspaceModal` (first load).
  3. Import and render `WorkspaceModal` with open/close state.
- **Files**: `apps/web/app/ide/page.tsx`
- **Depends on**: T1.3, T1.4

### T1.6: Run npm run build to verify
- **Status**: open
- **Description**: Run `npm run build` in `apps/web` directory. Fix any TypeScript or build errors. Ensure zero errors.
- **Files**: none
- **Depends on**: T1.1–T1.5

---

## Execution Order

```
T1.1 (backend DELETE) ──→ T1.2 (field fix) ──→ T1.3 (modal) ──→ T1.4 (filetree CRUD) ──→ T1.5 (page wiring) ──→ T1.6 (build verify)
```

T1.1 and T1.2 can run in parallel since T1.2 only touches frontend files. But T1.2 depends on T1.1 for the DELETE endpoint to exist.

## Key Decisions

1. **FileEntry field**: Add `isDir` to backend response (non-breaking, minimal frontend changes)
2. **Context menu**: Custom positioned div (no library — matches existing pattern of no shared UI primitives)
3. **Delete confirmation**: Use browser `confirm()` to keep it simple (no custom dialog component needed)
4. **Active indicator**: Derive from session store events, show pulsing green dot
5. **Workspace persistence**: `localStorage` key `spark_workspace_root`
