import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import KBAdmin from './pages/KBAdmin';
import NewTaskUpload from './pages/NewTaskUpload';
import Processing from './pages/Processing';
import Results from './pages/Results';
import Review from './pages/Review';
import Evaluation from './pages/Evaluation';
import Settings from './pages/Settings';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LogViewer } from './components/LogViewer';
import { useNavigationLog } from './hooks/useLifecycleLog';

function App() {
  // Log application-level navigation events
  useNavigationLog();

  return (
    <ErrorBoundary>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/kb" element={<KBAdmin />} />
          <Route path="/new-task" element={<NewTaskUpload />} />
          <Route path="/processing/:taskId" element={<Processing />} />
          <Route path="/results/:taskId" element={<Results />} />
          <Route path="/review/:taskId" element={<Review />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
      {/* Log viewer - only visible in development */}
      {import.meta.env.DEV && <LogViewer />}
    </ErrorBoundary>
  );
}

export default App;
