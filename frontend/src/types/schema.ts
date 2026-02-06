// Matches TaskBase from backend/app/models/schemas.py
export interface Task {
    title: string;
    description: string | null;
    assignee_name: string | null; // Raw extracted name
    assignee_id: number | null;   // Resolved Vikunja User ID
    priority: number;             // 1-5
    due_date: string | null;      // ISO Date "YYYY-MM-DD"
}

// Matches AnalysisResponse
export interface AnalysisResponse {
    tasks: Task[];
    token_count: number;
    processing_time: number;
}

// Matches Vikunja Sync Response
export interface SyncDetail {
    title: string;
    status: 'success' | 'error';
    error?: string;
}

export interface SyncResponse {
    total: number;
    success: number;
    failed: number;
    details: SyncDetail[];
}

export interface VoiceState {
    title: string | null;
    description: string | null;
    dueDate: string | null;
    assignee: string | null;
    status: 'draft' | 'ready'; // Based on typical voice agent flows
    priority?: number;
    _reply_text?: string; // Metadata for UI text display
}

export interface VoiceTurnResponse {
    updated_state: VoiceState;
    reply_audio: string; // Base64 encoded audio
    should_end_session?: boolean;
}
