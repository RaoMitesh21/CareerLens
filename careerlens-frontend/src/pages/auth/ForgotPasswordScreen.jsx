import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, ChevronLeft, HelpCircle, Info } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { FormInput, SubmitButton, ErrorMessage, SuccessMessage } from '../../components/auth/AuthComponents';
import Auth3DBackground from '../../components/auth/Auth3DBackground';

const ForgotPasswordScreen = () => {
  const navigate = useNavigate();
  const { requestPasswordReset, error, successMessage, clearError, isLoading } = useAuth();

  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [fieldError, setFieldError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!emailOrUsername.trim()) {
      setFieldError('Email or username is required');
      return;
    }
    setFieldError('');
    const result = await requestPasswordReset(emailOrUsername);
    if (result.success) {
      sessionStorage.setItem('otpFlowType', 'reset');
      setTimeout(() => {
        navigate('/verify-otp?type=reset');
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
          onClick={() => navigate('/login')}
          className="mb-6 flex items-center gap-2 text-slate-500 hover:text-cyan-600 transition-colors font-medium cursor-pointer"
          whileHover={{ x: -4 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ChevronLeft size={18} />
          Back to login
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
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5 bg-white"
              style={{
                border: '1px solid rgba(249,115,22,0.3)',
                boxShadow: '0 8px 25px rgba(249,115,22,0.15)',
              }}
            >
              <HelpCircle className="text-orange-500" size={28} />
            </motion.div>

            <h1
              className="text-2xl font-bold mb-2 text-slate-800"
            >
              Reset Password
            </h1>
            <p className="text-slate-500 font-medium text-sm px-2">
              Enter your email or username and we'll send you a code to reset your password.
            </p>
          </motion.div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <FormInput
                label="Email or Username"
                value={emailOrUsername}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                error={fieldError}
                placeholder="john@example.com or john_doe"
                icon={Mail}
                required
              />
            </motion.div>

            {/* Submit */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
              className="pt-2"
            >
              <SubmitButton loading={isLoading} onClick={handleSubmit}>
                Send Reset Code <ArrowRight size={18} />
              </SubmitButton>
            </motion.div>

            {/* Tips */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="rounded-xl p-4 space-y-2 bg-blue-50/80"
              style={{
                border: '1px solid rgba(59, 130, 246, 0.2)',
              }}
            >
              <p className="text-xs font-bold text-blue-600 flex items-center gap-2">
                <Info size={14} />
                Tips
              </p>
              <ul className="text-xs font-medium text-slate-600 space-y-1.5 ml-5">
                <li>• Check your spam folder if you don't see the code</li>
                <li>• The code will expire in 15 minutes</li>
                <li>• You can request a new code if needed</li>
              </ul>
            </motion.div>
          </form>

          {/* Contact Support */}
          <div className="text-center pt-2">
            <p className="text-sm font-medium text-slate-500">
              Having trouble?{' '}
              <a href="mailto:support@careerlens.com" className="text-cyan-600 hover:text-cyan-500 font-bold transition-colors">
                Contact support
              </a>
            </p>
          </div>
        </motion.div>
      </motion.div>

      {/* Notifications */}
      <ErrorMessage message={error} onClose={clearError} />
      <SuccessMessage message={successMessage} />
    </Auth3DBackground>
  );
};

export default ForgotPasswordScreen;
