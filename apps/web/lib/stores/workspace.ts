import { create } from 'zustand';

export interface FileEntry {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileEntry[];
}

interface WorkspaceStore {
  workspaceRoot: string;
  fileTree: FileEntry[];
  selectedFile: string | null;
  setWorkspace: (root: string) => void;
  setFileTree: (tree: FileEntry[]) => void;
  setSelectedFile: (path: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  workspaceRoot: '',
  fileTree: [],
  selectedFile: null,

  setWorkspace: (root: string) => {
    set({ workspaceRoot: root });
  },

  setFileTree: (tree: FileEntry[]) => {
    set({ fileTree: tree });
  },

  setSelectedFile: (path: string | null) => {
    set({ selectedFile: path });
  },
}));
