import { create } from 'zustand';
import type { Task, SyncResponse } from '../types/schema';
import { batchApi } from '../api/batch';

interface BatchState {
    status: 'idle' | 'uploading' | 'analyzing' | 'reviewing' | 'syncing' | 'completed' | 'error';
    tasks: Task[];
    syncResult: SyncResponse | null;
    error: string | null;

    // Actions
    uploadFiles: (files: File[]) => Promise<void>;
    updateTask: (index: number, updates: Partial<Task>) => void;
    removeTask: (index: number) => void;
    syncToVikunja: () => Promise<void>;
    reset: () => void;
}

export const useBatchStore = create<BatchState>((set, get) => ({
    status: 'idle',
    tasks: [],
    syncResult: null,
    error: null,

    uploadFiles: async (files: File[]) => {
        set({ status: 'uploading', error: null });
        try {
            const response = await batchApi.uploadFiles(files);
            set({
                tasks: response.tasks,
                status: 'reviewing'
            });
        } catch (err: any) {
            set({
                status: 'error',
                error: err.message || 'Failed to upload files'
            });
        }
    },

    updateTask: (index, updates) => {
        set((state) => {
            const newTasks = [...state.tasks];
            newTasks[index] = { ...newTasks[index], ...updates };
            return { tasks: newTasks };
        });
    },

    removeTask: (index) => {
        set((state) => ({
            tasks: state.tasks.filter((_, i) => i !== index),
        }));
    },

    syncToVikunja: async () => {
        const { tasks } = get();
        if (tasks.length === 0) return;

        set({ status: 'syncing', error: null });
        try {
            const result = await batchApi.syncTasks(tasks);
            set({
                status: 'completed',
                syncResult: result
            });
        } catch (err: any) {
            set({
                status: 'error',
                error: err.message || 'Failed to sync tasks'
            });
        }
    },

    reset: () => {
        set({
            status: 'idle',
            tasks: [],
            syncResult: null,
            error: null,
        });
    },
}));
