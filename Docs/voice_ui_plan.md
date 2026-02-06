# Voice Agent UI Implementation Plan

## Goal
Replace the developer UI for the Voice Agent with a polished, split-screen interface using Shadcn components and the Stitch design.

## Proposed Changes

### 1. Store Updates (if needed)
*   Verify `useVoiceStore` matches the UI requirements (Messages, Task Draft, Recording State).

### 2. New Components (`src/components/voice/`)
*   **`ChatInterface.tsx`**: 
    - Render `messages` from store.
    - Style user messages (green/right) and AI messages (gray/left).
    - Use `ScrollArea` for the list.
*   **`VoiceControls.tsx`**:
    - "Live" vs "Standard" toggle (visual only initially).
    - Centered Mic button (Floating Action Button style).
*   **`TaskDraftCard.tsx`**:
    - Live form binding to `currentTask` in store.
    - Fields: Title, Description (Textarea), Assignee, Due Date, Priority.
    - "Drafting..." indicator when `isProcessing` is true.

### 3. Layout Integration (`src/views/VoiceAgentView.tsx`)
*   Split screen layout: Chat (Left) | Draft (Right).
*   Responsive checking (stack on mobile).

## Verification Plan
### Manual Verification
1.  Navigate to `/voice`.
2.  **Visual Check**: Confirm split screen layout.
3.  **Interaction**: 
    - Click Mic -> Check if recording state updates.
    - Speak/Mock text -> Check if bubbles appear correctly.
    - Draft Updates -> Check if the Right Panel form updates in real-time.
