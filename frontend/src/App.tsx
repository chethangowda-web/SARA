import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth, getDashboardRoute } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Signup from './pages/Signup';

import CitizenDashboard from './pages/CitizenDashboard';
import CitizenGrievancesPage from './pages/citizen/CitizenGrievancesPage';
import CitizenSubmitPage from './pages/citizen/CitizenSubmitPage';

import OfficerDashboard from './pages/OfficerDashboard';
import OfficerAssignedCasesPage from './pages/officer/OfficerAssignedCasesPage';

import SupervisorDashboard from './pages/SupervisorDashboard';
import SupervisorDepartmentCasesPage from './pages/supervisor/SupervisorDepartmentCasesPage';
import SupervisorOfficerWorkloadPage from './pages/supervisor/SupervisorOfficerWorkloadPage';
import SupervisorEscalationMonitorPage from './pages/supervisor/SupervisorEscalationMonitorPage';

import AdminDashboard from './pages/AdminDashboard';
import AdminDepartmentsPage from './pages/admin/AdminDepartmentsPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminAnomaliesPage from './pages/admin/AdminAnomaliesPage';

import GrievanceDetailsPage from './pages/GrievanceDetailsPage';

// Root-level redirect to user workspace based on role
function HomeRedirect() {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-300 animate-fadeIn">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
          <p className="text-sm font-medium tracking-wider">Verifying session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const route = getDashboardRoute(user.role);
  return <Navigate to={route} replace />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login & Signup */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Root Redirect */}
          <Route path="/" element={<HomeRedirect />} />

          {/* Shared Grievance Details Route */}
          <Route
            path="/grievances/:id"
            element={
              <ProtectedRoute allowedRoles={['CITIZEN', 'OFFICER', 'SUPERVISOR', 'ADMIN']}>
                <GrievanceDetailsPage />
              </ProtectedRoute>
            }
          />

          {/* Protected CITIZEN Workspaces */}
          <Route
            path="/citizen"
            element={
              <ProtectedRoute allowedRoles={['CITIZEN']}>
                <CitizenDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/citizen/grievances"
            element={
              <ProtectedRoute allowedRoles={['CITIZEN']}>
                <CitizenGrievancesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/citizen/submit"
            element={
              <ProtectedRoute allowedRoles={['CITIZEN']}>
                <CitizenSubmitPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/citizen/*"
            element={
              <ProtectedRoute allowedRoles={['CITIZEN']}>
                <Navigate to="/citizen" replace />
              </ProtectedRoute>
            }
          />

          {/* Protected OFFICER Workspaces */}
          <Route
            path="/officer"
            element={
              <ProtectedRoute allowedRoles={['OFFICER']}>
                <OfficerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/officer/assigned"
            element={
              <ProtectedRoute allowedRoles={['OFFICER']}>
                <OfficerAssignedCasesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/officer/cases"
            element={
              <ProtectedRoute allowedRoles={['OFFICER']}>
                <OfficerAssignedCasesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/officer/*"
            element={
              <ProtectedRoute allowedRoles={['OFFICER']}>
                <Navigate to="/officer" replace />
              </ProtectedRoute>
            }
          />

          {/* Protected SUPERVISOR Workspaces */}
          <Route
            path="/supervisor"
            element={
              <ProtectedRoute allowedRoles={['SUPERVISOR']}>
                <SupervisorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/cases"
            element={
              <ProtectedRoute allowedRoles={['SUPERVISOR']}>
                <SupervisorDepartmentCasesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/officers"
            element={
              <ProtectedRoute allowedRoles={['SUPERVISOR']}>
                <SupervisorOfficerWorkloadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/escalations"
            element={
              <ProtectedRoute allowedRoles={['SUPERVISOR']}>
                <SupervisorEscalationMonitorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/*"
            element={
              <ProtectedRoute allowedRoles={['SUPERVISOR']}>
                <Navigate to="/supervisor" replace />
              </ProtectedRoute>
            }
          />

          {/* Protected ADMIN Workspaces */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/departments"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminDepartmentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/analytics"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminAnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/anomalies"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminAnomaliesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <Navigate to="/admin" replace />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
