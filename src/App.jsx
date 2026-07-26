import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './contexts/ToastContext';

// Layouts
import AuthLayout from './layouts/AuthLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Pages
import Login from './pages/Login';
import CreateAccount from './pages/CreateAccount';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import FacultySearch from './pages/FacultySearch';
import TimetableView from './pages/TimetableView';
import UploadedFiles from './pages/UploadedFiles';
import Downloads from './pages/Downloads';
import Settings from './pages/Settings';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { currentUser, loading } = useAuth();
  
  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  if (!currentUser) return <Navigate to="/login" replace />;
  
  return children;
};

const App = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              {/* Auth Routes */}
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<CreateAccount />} />
              </Route>

              {/* Dashboard Routes */}
              <Route path="/" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
                <Route index element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
                <Route path="upload" element={<ErrorBoundary><Upload /></ErrorBoundary>} />
                <Route path="faculty" element={<ErrorBoundary><FacultySearch /></ErrorBoundary>} />
                <Route path="faculty/:id" element={<ErrorBoundary><TimetableView /></ErrorBoundary>} />
                <Route path="files" element={<ErrorBoundary><UploadedFiles /></ErrorBoundary>} />
                <Route path="downloads" element={<ErrorBoundary><Downloads /></ErrorBoundary>} />
                <Route path="settings" element={<ErrorBoundary><Settings /></ErrorBoundary>} />
              </Route>

              {/* Catch all */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
