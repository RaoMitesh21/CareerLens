import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, ChevronLeft, LogIn, Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { FormInput, PasswordInput, SubmitButton, ErrorMessage, SuccessMessage } from '../../components/auth/AuthComponents';
import Auth3DBackground from '../../components/auth/Auth3DBackground';
import Logo from '../../components/Logo';

const LoginScreen = () => {
  const navigate = useNavigate();
  const { login, error, successMessage, clearError, isLoading } = useAuth();

  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const [rememberMe, setRememberMe] = useState(false);

  const validateForm = () => {
    const errors = {};
    if (!loginId.trim()) {
      errors.loginId = 'Username or email is required';
    }
    if (!password) {
      errors.password = 'Password is required';
    }
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    setFormErrors({});
    const result = await login(loginId, password);
    if (result.success) {
      sessionStorage.setItem('otpFlowType', 'login');
      setTimeout(() => {
        navigate('/verify-otp?type=login');
      }, 500);
    }
  };

  return (
    <Auth3DBackground>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-md"
      >
        {/* Back Button */}
        <motion.button
          onClick={() => navigate('/')}
          className="mb-6 flex items-center gap-2 text-slate-500 hover:text-cyan-600 transition-colors font-medium cursor-pointer"
          whileHover={{ x: -4 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ChevronLeft size={18} />
          Back
        </motion.button>

        {/* Logo Presentation */}
        <motion.div
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.15, duration: 0.6, type: 'spring', stiffness: 100 }}
          className="flex justify-center mb-8"
        >
          <div 
            className="bg-white rounded-full p-6 flex items-center justify-center"
            style={{
              boxShadow: '0 10px 30px rgba(0, 194, 203, 0.15), 0 4px 10px rgba(15, 23, 42, 0.05)',
              border: '1px solid rgba(0, 194, 203, 0.1)'
            }}
          >
            <Logo size="md" />
          </div>
        </motion.div>

        {/* Glass Card (Light) */}
        <motion.div
          initial={{ opacity: 0, y: 30, rotateX: 10 }}
          animate={{ opacity: 1, y: 0, rotateX: 0 }}
          transition={{ delay: 0.25, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="auth-glass-card p-8 space-y-6"
        >
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
          >
            {/* Icon Badge */}
            <motion.div
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
              className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-white"
              style={{
                border: '1px solid rgba(0,194,203,0.3)',
                boxShadow: '0 8px 20px rgba(0,194,203,0.15)',
              }}
            >
              <LogIn className="text-cyan-500" size={22} />
            </motion.div>

            <h1
              className="text-2xl font-bold mb-1"
              style={{
                background: 'linear-gradient(135deg, #0f172a, #334155)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Welcome back
            </h1>
            <p className="text-slate-500 font-medium text-sm">Sign in to your CareerLens account</p>
          </motion.div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Login ID */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <FormInput
                label="Username or Email"
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                error={formErrors.loginId}
                placeholder="john_doe or john@example.com"
                icon={Mail}
                required
              />
            </motion.div>

            {/* Password */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
            >
              <PasswordInput
                label="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={formErrors.password}
                showStrength={false}
              />
            </motion.div>

            {/* Remember Me & Forgot Password */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="flex items-center justify-between"
            >
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="sr-only"
                  />
                  <div
                    className={`w-4 h-4 rounded border transition-all duration-200 flex items-center justify-center ${
                      rememberMe
                        ? 'bg-cyan-500 border-cyan-500'
                        : 'border-slate-300 bg-white group-hover:border-cyan-400'
                    }`}
                  >
                    {rememberMe && (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="text-white text-[10px] font-bold"
                      >
                        ✓
                      </motion.span>
                    )}
                  </div>
                </div>
                <span className="text-sm font-medium text-slate-600 group-hover:text-slate-800 transition-colors">
                  Remember me
                </span>
              </label>

              <button
                type="button"
                onClick={() => navigate('/forgot-password')}
                className="text-sm text-cyan-600 hover:text-cyan-500 font-bold transition-colors cursor-pointer"
              >
                Forgot password?
              </button>
            </motion.div>

            {/* Submit Button */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.55 }}
              className="pt-1"
            >
              <SubmitButton loading={isLoading} onClick={handleSubmit}>
                Sign In <ArrowRight size={18} />
              </SubmitButton>
            </motion.div>

            {/* Security Info */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="rounded-xl p-3.5 bg-cyan-50/80"
              style={{
                border: '1px solid rgba(0, 194, 203, 0.2)',
              }}
            >
              <p className="text-xs font-medium text-slate-600 flex items-start gap-2.5 leading-relaxed">
                <Shield size={16} className="text-cyan-500 flex-shrink-0 mt-0.5" />
                You'll be asked to verify your identity with a code sent to your email for extra security.
              </p>
            </motion.div>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full" style={{ height: '1px', background: 'linear-gradient(90deg, transparent, rgba(15,23,42,0.1), transparent)' }} />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-transparent text-slate-400">or</span>
            </div>
          </div>

          {/* Sign Up Link */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.65 }}
            className="text-center"
          >
            <p className="text-slate-500 font-medium text-sm">
              Don't have an account?{' '}
              <button
                onClick={() => navigate('/signup')}
                className="text-cyan-600 font-bold hover:text-cyan-500 transition-colors cursor-pointer"
              >
                Sign up
              </button>
            </p>
          </motion.div>
        </motion.div>

        {/* Security footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-center font-medium text-xs text-slate-500 mt-6"
        >
          🔐 Secure login with industry-grade encryption
        </motion.p>
      </motion.div>

      {/* Notifications */}
      <ErrorMessage message={error} onClose={clearError} />
      <SuccessMessage message={successMessage} />
    </Auth3DBackground>
  );
};

export default LoginScreen;
