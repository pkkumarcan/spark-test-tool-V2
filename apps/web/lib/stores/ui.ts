import { create } from 'zustand';

type SidebarTab = 'explorer' | 'sessions' | 'tasks';

interface UIStore {
  sidebarTab: SidebarTab;
  terminalOpen: boolean;
  toggleTerminal: () => void;
  setSidebarTab: (tab: SidebarTab) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarTab: 'explorer',
  terminalOpen: true,

  toggleTerminal: () => {
    set((state) => ({ terminalOpen: !state.terminalOpen }));
  },

  setSidebarTab: (tab: SidebarTab) => {
    set({ sidebarTab: tab });
  },
}));
