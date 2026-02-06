import { BatchProcessingView } from './components/BatchProcessingView';
import { VoiceAgentView } from './views/VoiceAgentView';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/batch" replace />} />
        <Route path="/batch" element={<BatchProcessingView />} />
        <Route path="/voice" element={<VoiceAgentView />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
