import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, ChevronLeft, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { PasswordInput, SubmitButton, ErrorMessage, SuccessMessage } from '../../components/auth/AuthComponents';
import { validatePassword } from '../../utils/validation';
import Auth3DBackground from '../../components/auth/Auth3DBackground';

const ResetPasswordScreen = () => {
  const navigate = useNavigate();
  const { resetPassword, error, successMessage, clearError, isLoading } = useAuth();

  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });

  const [validationErrors, setValidationErrors] = useState({});
  const [isSuccess, setIsSuccess] = useState(false);
  const [resetContext, setResetContext] = useState({ email: '', otp: '' });

  useEffect(() => {
    const pendingResetData = localStorage.getItem('pendingReset');
    const verifiedResetEmail = sessionStorage.getItem('verifiedResetEmail') || '';
    const verifiedResetOTP = sessionStorage.getItem('verifiedResetOTP') || '';

    let pendingEmail = '';
    if (pendingResetData) {
      try {
        pendingEmail = JSON.parse(pendingResetData)?.email || '';
      } catch {
        pendingEmail = '';
      }
    }

    const resolvedEmail = verifiedResetEmail || pendingEmail;

    if (!resolvedEmail || !verifiedResetOTP) {
      navigate('/forgot-password', { replace: true });
      return;
    }

    setResetContext({ email: resolvedEmail, otp: verifiedResetOTP });
  }, [navigate]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (validationErrors[field]) {
      setValidationErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate password
    const validation = validatePassword(formData.password);
    if (!validation.valid) {
      setValidationErrors({ password: validation.errors[0] || 'Password does not meet requirements' });
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setValidationErrors({ confirmPassword: 'Passwords do not match' });
      return;
    }

    setValidationErrors({});

    const result = await resetPassword(resetContext.email, resetContext.otp, formData.password);

    if (result.success) {
      sessionStorage.removeItem('verifiedResetOTP');
      sessionStorage.removeItem('verifiedResetEmail');
      setIsSuccess(true);
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 3000); // Wait longer so they can read the success message
    }
  };

  // Success State View
  if (isSuccess) {
    return (
      <Auth3DBackground>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, type: 'spring' }}
          className="w-full max-w-md text-center"
        >
          <div className="auth-glass-card p-10 space-y-6 flex flex-col items-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', damping: 12 }}
              className="w-20 h-20 rounded-full flex items-center justify-center bg-white"
              style={{
                border: '2px solid rgba(16, 185, 129, 0.5)',
                boxShadow: '0 0 40px rgba(16, 185, 129, 0.2)',
              }}
            >
              <ShieldCheck className="text-emerald-500" size={40} />
            </motion.div>

            <h1 className="text-2xl font-bold text-slate-800">Password Reset Complete</h1>
            <p className="text-slate-500 font-medium">
              Your password has been successfully updated. You will be redirected to the login page shortly.
            </p>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="pt-4 w-full"
            >
              <SubmitButton onClick={() => navigate('/login')} variant="secondary">
                Return to Login
              </SubmitButton>
            </motion.div>
          </div>
        </motion.div>
      </Auth3DBackground>
    );
  }

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
          onClick={() => navigate('/login')}
          className="mb-6 flex items-center gap-2 text-slate-500 hover:text-cyan-600 transition-colors font-medium cursor-pointer"
          whileHover={{ x: -4 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ChevronLeft size={18} />
          Cancel
        </motion.button>

        {/* Glass Card (Light) */}
        <motion.div
          initial={{ opacity: 0, y: 30, rotateX: 10 }}
          animate={{ opacity: 1, y: 0, rotateX: 0 }}
          transition={{ delay: 0.2, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="auth-glass-card p-8 space-y-6"
        >
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-center"
          >
            {/* Icon */}
            <motion.div
              animate={{ rotate: [0, 10, 0, -10, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5 bg-white"
              style={{
                border: '1px solid rgba(16, 185, 129, 0.3)',
                boxShadow: '0 8px 25px rgba(16, 185, 129, 0.15)',
              }}
            >
              <LockKeyhole className="text-emerald-500" size={28} />
            </motion.div>

            <h1 className="text-2xl font-bold mb-2 text-slate-800">
              Create New Password
            </h1>
            <p className="text-slate-500 font-medium text-sm px-2">
              Your new password must be unique from those previously used.
            </p>
          </motion.div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <PasswordInput
                label="New Password"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                error={validationErrors.password}
                showStrength={true}
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
            >
              <PasswordInput
                label="Confirm New Password"
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                error={validationErrors.confirmPassword}
                showStrength={false}
              />
            </motion.div>

            {/* Submit */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="pt-2"
            >
              <SubmitButton
                onClick={handleSubmit}
                loading={isLoading}
                disabled={isLoading}
                variant="secondary"
              >
                Reset Password <ArrowRight size={18} />
              </SubmitButton>
            </motion.div>
          </form>
        </motion.div>
      </motion.div>

      {/* Notifications */}
      <ErrorMessage message={error} onClose={clearError} />
      <SuccessMessage message={successMessage} />
    </Auth3DBackground>
  );
};

export default ResetPasswordScreen;
