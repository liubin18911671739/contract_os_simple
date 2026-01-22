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

function App() {
  return (
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
  );
}

export default App;
