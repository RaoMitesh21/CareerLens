import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Auth Pages
import RoleSelectionScreen from './pages/auth/RoleSelectionScreen';
import RegisterScreen from './pages/auth/RegisterScreen';
import OTPVerificationScreen from './pages/auth/OTPVerificationScreen';
import LoginScreen from './pages/auth/LoginScreen';
import ForgotPasswordScreen from './pages/auth/ForgotPasswordScreen';
import ResetPasswordScreen from './pages/auth/ResetPasswordScreen';

// Dashboard Pages
import StudentDashboard from './pages/dashboard/StudentDashboard';
import RecruiterDashboard from './pages/dashboard/RecruiterDashboard';

// Legacy Pages
import Navbar from './components/Navbar';
import SeoManager from './components/SeoManager';
import LandingPage from './pages/LandingPage';
import ResultsPage from './pages/ResultsPage';
import DemoPage from './pages/DemoPage';
import RecruiterPage from './pages/RecruiterPage';

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { isAuthenticated, userRole, isInitializing } = useAuth();

  // Show loading while initializing auth from localStorage
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-100 mb-4">
            <div className="animate-spin">
              <div className="h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
            </div>
          </div>
          <p className="text-gray-700 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }

  if (requiredRole && userRole !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <>
      <SeoManager />
      <Routes>
      {/* ═══════════════════════════════════════════════════════════════
          PUBLIC PAGES (Always accessible)
          ═══════════════════════════════════════════════════════════════ */}
      
      {/* Landing Page — Entry point */}
      <Route path="/" element={<><Navbar /><LandingPage /></>} />

      {/* ═══════════════════════════════════════════════════════════════
          AUTHENTICATION ROUTES (Public, redirect if authenticated)
          ═══════════════════════════════════════════════════════════════ */}
      
      {/* Sign Up — Role selection + registration */}
        <Route path="/signup" element={<RoleSelectionScreen />} />
        <Route path="/register" element={<RegisterScreen />} />
      
      {/* Sign In */}
        <Route path="/signin" element={<LoginScreen />} />
        <Route path="/login" element={<LoginScreen />} />
      
      {/* Password Recovery */}
        <Route path="/forgot-password" element={<ForgotPasswordScreen />} />
      <Route path="/reset-password" element={<ResetPasswordScreen />} />
      
      {/* OTP Verification (unguarded, flow-dependent) */}
      <Route path="/verify-otp" element={<OTPVerificationScreen />} />

      {/* ═══════════════════════════════════════════════════════════════
          STUDENT ROUTES (Protected, student role required)
          ═══════════════════════════════════════════════════════════════ */}
      
      {/* Student Resume Analyzer */}
      <Route
        path="/student/analyzer"
        element={
          <ProtectedRoute requiredRole="student">
            <StudentDashboard />
          </ProtectedRoute>
        }
      />
      
      {/* Public Demo Route — NO LOGIN REQUIRED */}
      <Route
        path="/demo"
        element={<><Navbar /><DemoPage /></>}
      />

      {/* Analysis Results */}
      {/* Protected authenticated results */}
      <Route
        path="/results"
        element={
          <ProtectedRoute requiredRole="student">
            <><Navbar /><ResultsPage /></>
          </ProtectedRoute>
        }
      />
      <Route
        path="/results/:mode"
        element={
          <ProtectedRoute requiredRole="student">
            <><Navbar /><ResultsPage /></>
          </ProtectedRoute>
        }
      />
      
      {/* Student Dashboard (new - alternative view) */}
      <Route
        path="/student/dashboard"
        element={
          <ProtectedRoute requiredRole="student">
            <StudentDashboard />
          </ProtectedRoute>
        }
      />

      {/* ═══════════════════════════════════════════════════════════════
          RECRUITER ROUTES (Protected, recruiter role required)
          ═══════════════════════════════════════════════════════════════ */}
      
      {/* Recruiter Job Posting & Analysis */}
      <Route
        path="/recruiter/jobs"
        element={
          <ProtectedRoute requiredRole="recruiter">
            <><Navbar /><RecruiterPage /></>
          </ProtectedRoute>
        }
      />

      {/* Recruiter Compare Analyzer */}
      <Route
        path="/recruiter/compare"
        element={
          <ProtectedRoute requiredRole="recruiter">
            <><Navbar /><RecruiterPage /></>
          </ProtectedRoute>
        }
      />
      
      {/* Recruiter Dashboard */}
      <Route
        path="/recruiter/dashboard"
        element={
          <ProtectedRoute requiredRole="recruiter">
            <RecruiterDashboard />
          </ProtectedRoute>
        }
      />

      {/* ═══════════════════════════════════════════════════════════════
          FALLBACK
          ═══════════════════════════════════════════════════════════════ */}
      
      {/* Catch all — redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
