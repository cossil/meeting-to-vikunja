import client from './client';
import type { AnalysisResponse, Task, SyncResponse } from '../types/schema';

export const batchApi = {
    uploadFiles: async (files: File[], instructions?: string): Promise<AnalysisResponse> => {
        const formData = new FormData();
        if (files.length > 0) {
            formData.append('file', files[0]);
        }
        if (instructions) {
            formData.append('instructions', instructions);
        }

        const response = await client.post<AnalysisResponse>('/analyze', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    syncTasks: async (tasks: Task[]): Promise<SyncResponse> => {
        const response = await client.post<SyncResponse>('/sync', { tasks });
        return response.data;
    },
};
