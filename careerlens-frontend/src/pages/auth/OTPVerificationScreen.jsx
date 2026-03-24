import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, ChevronLeft, ShieldCheck, Clock, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { OTPInput, SubmitButton, ErrorMessage, SuccessMessage } from '../../components/auth/AuthComponents';
import Auth3DBackground from '../../components/auth/Auth3DBackground';

const OTPVerificationScreen = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryType = searchParams.get('type');
  const { verifyOTP, verifyLoginOTP, resendOTP, error, successMessage, clearError, isLoading } = useAuth();

  const [otp, setOtp] = useState('');
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [localError, setLocalError] = useState('');

  const type = useMemo(() => {
    const validTypes = new Set(['login', 'registration', 'reset']);
    const storedType = sessionStorage.getItem('otpFlowType');

    if (queryType && validTypes.has(queryType)) {
      sessionStorage.setItem('otpFlowType', queryType);
      return queryType;
    }

    if (storedType && validTypes.has(storedType)) {
      return storedType;
    }

    sessionStorage.setItem('otpFlowType', 'login');
    return 'login';
  }, [queryType]);

  useEffect(() => {
    const requestedType = queryType || '';
    if (requestedType !== type) {
      navigate(`/verify-otp?type=${type}`, { replace: true });
    }
  }, [navigate, queryType, type]);

  useEffect(() => {
    let timer;
    if (countdown > 0 && !canResend) {
      timer = setInterval(() => setCountdown((prev) => prev - 1), 1000);
    } else if (countdown === 0) {
      setCanResend(true);
    }
    return () => clearInterval(timer);
  }, [countdown, canResend]);

  const handleVerify = async (e) => {
    e?.preventDefault();
    if (otp.length !== 6) return;
    setLocalError('');

    // Get email from localStorage based on flow type
    let email = '';
    if (type === 'registration') {
      const pendingData = localStorage.getItem('pendingRegistration');
      email = pendingData ? JSON.parse(pendingData).email : '';
    } else if (type === 'login') {
      const pendingData = localStorage.getItem('pendingLogin');
      email = pendingData ? JSON.parse(pendingData).email : '';
    } else if (type === 'reset') {
      const pendingData = localStorage.getItem('pendingReset');
      email = pendingData ? JSON.parse(pendingData).email : '';
    }

    if (!email) {
      setLocalError('Email not found. Please try again.');
      return;
    }

    const stepMap = { registration: 'register', reset: 'reset' };
    const result = type === 'login'
      ? await verifyLoginOTP(email, otp)
      : await verifyOTP(email, otp, stepMap[type]);

    if (result.success) {
      sessionStorage.removeItem('otpFlowType');
      setTimeout(() => {
        if (type === 'reset') {
          sessionStorage.setItem('verifiedResetOTP', otp);
          sessionStorage.setItem('verifiedResetEmail', email);
          navigate('/reset-password');
        } else if (type === 'login') {
          const role = result.user?.role;
          if (role === 'recruiter') {
            navigate('/recruiter/dashboard');
          } else {
            navigate('/student/dashboard');
          }
        } else {
          navigate('/signin');
        }
      }, 800);
    }
  };

  const handleResend = async () => {
    if (!canResend) return;
    setLocalError('');

    setIsResending(true);
    // Get email from localStorage
    let email = '';
    if (type === 'registration') {
      const pendingData = localStorage.getItem('pendingRegistration');
      email = pendingData ? JSON.parse(pendingData).email : '';
    } else if (type === 'login') {
      const pendingData = localStorage.getItem('pendingLogin');
      email = pendingData ? JSON.parse(pendingData).email : '';
    } else if (type === 'reset') {
      const pendingData = localStorage.getItem('pendingReset');
      email = pendingData ? JSON.parse(pendingData).email : '';
    }

    if (!email) {
      setLocalError('Email not found. Cannot resend OTP.');
      setIsResending(false);
      return;
    }

    const stepMap = { registration: 'register', login: 'login', reset: 'reset' };
    const result = await resendOTP(email, stepMap[type]);
    setIsResending(false);

    if (result.success) {
      setCountdown(60);
      setCanResend(false);
      setOtp('');
    }
  };

  // Header content based on verification type
  const getContent = () => {
    switch (type) {
      case 'registration':
        return {
          title: 'Verify your email',
          desc: "We've sent a 6-digit code to your email to verify your new account.",
          iconColor: 'text-emerald-500',
          gradient: 'linear-gradient(135deg, #10B981, #14B8A6)',
          borderColor: 'rgba(16, 185, 129, 0.3)',
          shadowColor: 'rgba(16, 185, 129, 0.15)',
        };
      case 'reset':
        return {
          title: 'Enter reset code',
          desc: "Enter the 6-digit code we sent to your email to reset your password.",
          iconColor: 'text-orange-500',
          gradient: 'linear-gradient(135deg, #F97316, #EF4444)',
          borderColor: 'rgba(249, 115, 22, 0.3)',
          shadowColor: 'rgba(249, 115, 22, 0.15)',
        };
      case 'login':
      default:
        return {
          title: 'Two-Step Verification',
          desc: "Enter the security code associated with your account to sign in.",
          iconColor: 'text-cyan-500',
          gradient: 'linear-gradient(135deg, #00C2CB, #0ea5e9)',
          borderColor: 'rgba(0, 194, 203, 0.3)',
          shadowColor: 'rgba(0, 194, 203, 0.15)',
        };
    }
  };

  const content = getContent();

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
          onClick={() => navigate(-1)}
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
            {/* Animated Shield Icon */}
            <motion.div
              animate={{ rotateY: [0, 10, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5 bg-white"
              style={{
                border: `1px solid ${content.borderColor}`,
                boxShadow: `0 8px 25px ${content.shadowColor}`,
              }}
            >
              <ShieldCheck className={content.iconColor} size={32} />
            </motion.div>

            <h1 className="text-2xl font-bold mb-2 text-slate-800">
              {content.title}
            </h1>
            <p className="text-slate-500 font-medium text-sm px-2">
              {content.desc}
            </p>
          </motion.div>

          {/* Form */}
          <form onSubmit={handleVerify} className="space-y-8">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className="pt-2"
            >
              <OTPInput
                value={otp}
                onChange={(val) => {
                  setOtp(val);
                  if (val.length === 6) clearError();
                }}
                disabled={isLoading}
              />
            </motion.div>

            {/* Timer and Resend */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.45 }}
              className="flex flex-col items-center gap-2"
            >
              {!canResend ? (
                <div className="flex items-center gap-1.5 text-sm font-medium text-slate-500">
                  <Clock size={14} className="text-cyan-600" />
                  Code expires in <span className="font-bold text-slate-800">{countdown}s</span>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={isResending}
                  className="flex items-center gap-1.5 text-sm font-bold text-cyan-600 hover:text-cyan-500 transition-colors cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw size={14} className={isResending ? 'animate-spin' : ''} />
                  Resend Code
                </button>
              )}
            </motion.div>

            {/* Submit */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <SubmitButton
                onClick={handleVerify}
                loading={isLoading}
                disabled={otp.length !== 6 || isLoading}
                variant={type === 'registration' ? 'secondary' : 'primary'}
              >
                Verify & Continue <ArrowRight size={18} />
              </SubmitButton>
            </motion.div>

            {/* Info Box */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.55 }}
              className="rounded-xl p-4 bg-slate-50/80"
              style={{ border: '1px solid rgba(203, 213, 225, 0.6)' }}
            >
              <p className="text-xs font-medium text-slate-500 leading-relaxed text-center">
                Can't find the email? Check your <span className="text-slate-700 font-bold">spam</span> or <span className="text-slate-700 font-bold">junk</span> folder. If you still don't see it, request a new code.
              </p>
            </motion.div>
          </form>
        </motion.div>
      </motion.div>

      {/* Notifications */}
      <ErrorMessage message={error} onClose={clearError} />
      <ErrorMessage message={localError} onClose={() => setLocalError('')} />
      <SuccessMessage message={successMessage} />
    </Auth3DBackground>
  );
};

export default OTPVerificationScreen;
