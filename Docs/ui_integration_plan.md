# UI Integration Plan & Gap Analysis

**Date:** 2026-02-05
**Objective:** Port Stitch-generated HTML designs to React/Shadcn components.

## 1. Gap Analysis

### Missing Shadcn Components
We need to ensure the following components are installed via `npx shadcn-ui@latest add [component]`:
- [ ] `avatar` (User profiles, Assignees)
- [ ] `badge` (Priorities, Status)
- [ ] `button` (Actions)
- [ ] `card` (Task Form container)
- [ ] `checkbox` (Table selection)
- [ ] `input` (Form fields)
- [ ] `table` (Task Review Grid)
- [ ] `separator` (Visual dividers)
- [ ] `scroll-area` (Chat history, Task list)
- [ ] `textarea` (Description field)
- [ ] `select` (Dropdowns for Assignee/Project)

### Icon Mapping (Material Symbols -> Lucide React)
The design uses Google Material Symbols. We will use `lucide-react` equivalents:

| Material Symbol | Lucide Icon | Context |
| :--- | :--- | :--- |
| `cloud_upload` | `Upload` | Batch Upload Tab |
| `mic` | `Mic` | Voice Agent Tab/Button |
| `settings` | `Settings` | Settings Tab |
| `auto_fix` / `auto_awesome` | `Wand2` / `Sparkles` | Logo / AI Features |
| `home` | `Home` | Breadcrumb |
| `notifications` | `Bell` | Header |
| `help` | `HelpCircle` | Header |
| `delete` | `Trash2` | Table Action |
| `assignment_turned_in` | `ClipboardCheck` | Section Header |
| `sync_alt` | `RefreshCw` | Sync Button |
| `graphic_eq` | `AudioWaveform` | Live Mode Indicator |
| `send` | `Send` | Chat Input |
| `check_circle` | `CheckCircle` | Create Task Button |
| `calendar_today` | `Calendar` | Due Date |
| `expand_more` | `ChevronDown` | Dropdowns |
| `info` | `Info` | AI Tips |

## 2. Component Architecture

### Layout Wrapper (`DashboardLayout.tsx`)
- **Sidebar**: Persistent navigation.
- **Header**: User profile and global actions.
- **Main**: Rendered children (Batch vs Voice).

### Page 1: Batch Dashboard (`/dashboard`)
- **UploadZone**: heavily styled dropzone.
- **TaskReviewTable**: `Shadcn Table` with custom columns.
    - Columns: Checkbox, Title, Description (truncated), Assignee, Priority (Badge), DueDate, Actions.
- **SyncBar**: Floating/Fixed bottom bar.

### Page 2: Voice Agent (`/voice-agent`)
- **SplitScreen**: Flexbox `flex-1` split.
- **LeftPanel (Chat)**:
    - `MessageBubble`: Differentiate User (Green/Primary) vs AI (Gray).
    - `VoiceControls`: Large Mic button.
- **RightPanel (LiveForm)**:
    - **Drafting State**: "Drafting..." pulse indicator.
    - **Form**: Input fields for Task details.

## 3. Reference Code (Raw HTML)

### Dashboard (`dashboard.html`)
```html
<!-- [PASTE CONTENT OF dashboard.html HERE IF NEEDED, BUT REFERENCING FILE IS BETTER] -->
<!-- See c:\Ai\meeting_to_vikunja\dashboard.html -->
```

### Voice Agent (`voice.html`)
```html
<!-- [PASTE CONTENT OF voice.html HERE IF NEEDED] -->
<!-- See c:\Ai\meeting_to_vikunja\voice.html -->
```
