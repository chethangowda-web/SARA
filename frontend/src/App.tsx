import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyEmail from './pages/VerifyEmail';

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
import AdminStaffManagement from './pages/admin/AdminStaffManagement';

import GrievanceDetailsPage from './pages/GrievanceDetailsPage';

import { IntelligenceDashboard } from './pages/sangam/IntelligenceDashboard';
import { NeedClustersPage } from './pages/sangam/NeedClustersPage';
import { InvestmentProjectsPage } from './pages/sangam/InvestmentProjectsPage';
import { GapsPage } from './pages/sangam/GapsPage';
import { PrioritiesPage } from './pages/sangam/PrioritiesPage';

// Root-level redirect to user workspace based on role
function HomeRedirect() {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role === 'CITIZEN') return <Navigate to="/citizen" replace />;
  if (user.role === 'OFFICER') return <Navigate to="/officer" replace />;
  if (user.role === 'SUPERVISOR') return <Navigate to="/supervisor" replace />;
  if (user.role === 'ADMIN') return <Navigate to="/admin" replace />;

  return <Navigate to="/login" replace />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login & Register & Verification */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />

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
            path="/admin/staff"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminStaffManagement />
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
            path="/admin/intelligence"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
                <IntelligenceDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/intelligence/needs"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
                <NeedClustersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/intelligence/projects"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
                <InvestmentProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/intelligence/gaps"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
                <GapsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/intelligence/priorities"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
                <PrioritiesPage />
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
