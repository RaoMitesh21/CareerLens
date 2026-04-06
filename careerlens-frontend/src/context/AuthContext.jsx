import React, { createContext, useContext, useState, useEffect } from 'react';

// Create Auth Context
const AuthContext = createContext();

function resolveAuthApiBaseUrl() {
  const envUrl = (import.meta.env.VITE_API_URL || '').trim();

  if (typeof window === 'undefined') {
    return envUrl || 'http://127.0.0.1:8012';
  }

  const hostname = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;

  const isCapacitor = (hostname === 'localhost' && port === '') || protocol === 'capacitor:';
  const isReactDevServer = (hostname === 'localhost' || hostname === '127.0.0.1') && port !== '';

  if (isCapacitor) {
    return envUrl || 'https://careerlens-api-imy1.onrender.com';
  }

  if (isReactDevServer) {
    return '/api';
  }

  if (envUrl) {
    return envUrl;
  }

  if (hostname.includes('careerlens.in') || hostname.includes('vercel.app')) {
    return 'https://careerlens-api-imy1.onrender.com';
  }

  return 'http://127.0.0.1:8012';
}

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const API_BASE_URL = resolveAuthApiBaseUrl();

  // Initialize from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(userData);
        setUserRole(userData.role);
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Failed to restore auth state:', err);
        clearAuth();
      }
    }
    
    // Always mark initialization as complete, even if no auth data found
    setIsInitializing(false);
  }, []);

  // API call helper with auth
  const apiCall = async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add JWT token for authenticated requests
    if (token && !endpoint.includes('/auth/')) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  };

  // Register user
  const register = async (name, email, login_id, password, role) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          name,
          email,
          login_id,
          password,
          role,
        }),
      });

      // Store pending registration info for OTP verification
      localStorage.setItem(
        'pendingRegistration',
        JSON.stringify({
          email,
          role,
          user_id: response.user_id,
        })
      );

      setSuccessMessage('Registration successful. Check your email for OTP.');

      return {
        success: true,
        message: response.message,
        userId: response.user_id,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Verify OTP (for registration or password reset)
  const verifyOTP = async (email, otp, currentStep = 'register') => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/auth/verify-otp', {
        method: 'POST',
        body: JSON.stringify({
          email,
          otp,
        }),
      });

      // Clear pending registration after successful verification
      if (currentStep === 'register') {
        localStorage.removeItem('pendingRegistration');
      }

      setSuccessMessage('OTP verified successfully.');

      return {
        success: true,
        message: response.message,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Resend OTP (for registration or password reset)
  const resendOTP = async (email, currentStep = 'register') => {
    try {
      setIsLoading(true);
      setError(null);

      let endpoint = '/auth/resend-otp-registration';
      if (currentStep === 'reset') {
        endpoint = '/auth/resend-otp-reset';
      } else if (currentStep === 'login') {
        endpoint = '/auth/resend-otp-login';
      }

      const response = await apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify({ email }),
      });

      setSuccessMessage('OTP resent to your email.');

      return {
        success: true,
        message: response.message,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Login user (generates 2FA OTP)
  const login = async (login_id, password) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          login_id,
          password,
        }),
      });

      // Store login info temporarily for 2FA verification
      localStorage.setItem(
        'pendingLogin',
        JSON.stringify({
          email: response.email,
          user_id: response.user_id,
        })
      );

      setSuccessMessage('Check your email for login verification code.');

      return {
        success: true,
        message: response.message,
        email: response.email,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Verify login OTP (2FA) - returns JWT token
  const verifyLoginOTP = async (email, otp) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/auth/verify-login-otp', {
        method: 'POST',
        body: JSON.stringify({
          email,
          otp,
        }),
      });

      // Store token and user data
      const accessToken = response.access_token;
      const userData = response.user;

      localStorage.setItem('authToken', accessToken);
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.removeItem('pendingLogin');

      // Update auth state
      setToken(accessToken);
      setUser(userData);
      setUserRole(userData.role);
      setIsAuthenticated(true);

      setSuccessMessage('Login successful!');

      return {
        success: true,
        message: 'Login successful',
        token: accessToken,
        user: userData,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Request password reset
  const requestPasswordReset = async (email_or_username) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({
          email_or_username,
        }),
      });

      // Store reset info for verification
      localStorage.setItem(
        'pendingReset',
        JSON.stringify({
          email: response.email,
        })
      );

      setSuccessMessage('Password reset code sent to your email.');

      return {
        success: true,
        message: response.message,
        email: response.email,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Reset password with OTP
  const resetPassword = async (email, otp, newPassword) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({
          email,
          otp,
          new_password: newPassword,
        }),
      });

      localStorage.removeItem('pendingReset');

      setSuccessMessage('Password reset successfully. Please login with your new password.');

      return {
        success: true,
        message: response.message,
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Logout
  const logout = async () => {
    try {
      setIsLoading(true);
      
      // Optional: Call logout endpoint for cleanup
      try {
        await apiCall('/auth/logout', {
          method: 'POST',
        });
      } catch (err) {
        // Logout endpoint failure shouldn't prevent local logout
        console.error('Logout API call failed:', err);
      }

      clearAuth();
      setSuccessMessage('Logged out successfully.');
      
      return {
        success: true,
        message: 'Logged out successfully',
      };
    } catch (err) {
      setError(err.message);
      return {
        success: false,
        error: err.message,
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Clear auth state
  const clearAuth = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('pendingRegistration');
    localStorage.removeItem('pendingLogin');
    localStorage.removeItem('pendingReset');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setUserRole(null);
  };

  // Clear error message
  const clearError = () => {
    setError(null);
  };

  // Clear success message
  const clearSuccessMessage = () => {
    setSuccessMessage(null);
  };

  const value = {
    // State
    user,
    token,
    isAuthenticated,
    userRole,
    isLoading,
    error,
    successMessage,
    isInitializing,

    // Methods
    register,
    verifyOTP,
    resendOTP,
    login,
    verifyLoginOTP,
    requestPasswordReset,
    resetPassword,
    logout,
    clearError,
    clearSuccessMessage,

    // API helper
    apiCall,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthContext;
