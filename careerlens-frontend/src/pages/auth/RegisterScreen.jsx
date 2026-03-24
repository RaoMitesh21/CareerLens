import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, User, ArrowRight, ChevronLeft, UserPlus } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { FormInput, PasswordInput, SubmitButton, ErrorMessage, SuccessMessage } from '../../components/auth/AuthComponents';
import { validateRegisterForm, validateName, validateEmail, validateUsername, validatePassword } from '../../utils/validation';
import Auth3DBackground from '../../components/auth/Auth3DBackground';
import Logo from '../../components/Logo';

const RegisterScreen = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { register, error, successMessage, clearError, isLoading } = useAuth();
  const role = searchParams.get('role') || 'student';

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    login_id: '',
    password: '',
    confirmPassword: '',
  });

  const [validationErrors, setValidationErrors] = useState({});

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Immediately clear errors from validationErrors when user starts typing
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleBlur = (field) => {
    let fieldError = '';

    // Validate individual fields
    if (field === 'name') {
      const validation = validateName(formData.name);
      fieldError = validation.error || '';
    } else if (field === 'email') {
      const validation = validateEmail(formData.email);
      fieldError = validation.error || '';
    } else if (field === 'login_id') {
      const validation = validateUsername(formData.login_id);
      fieldError = validation.error || '';
    } else if (field === 'password') {
      const validation = validatePassword(formData.password);
      fieldError = validation.valid ? '' : (validation.errors[0] || 'Invalid password');
    } else if (field === 'confirmPassword') {
      // Only check if passwords match (not full validation because password might not be fully typed yet)
      if (formData.password && formData.confirmPassword !== formData.password) {
        fieldError = 'Passwords do not match';
      }
    }

    // Update errors - delete key if no error, set if error exists
    setValidationErrors((prev) => {
      const newErrors = { ...prev };
      if (fieldError) {
        newErrors[field] = fieldError;
      } else {
        delete newErrors[field];
      }
      return newErrors;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validation = validateRegisterForm({ ...formData, role });
    if (!validation.valid) {
      setValidationErrors(validation.errors);
      return;
    }
    setValidationErrors({});
    const result = await register(formData.name, formData.email, formData.login_id, formData.password, role);
    if (result.success) {
      sessionStorage.setItem('otpFlowType', 'registration');
      setTimeout(() => {
        navigate('/verify-otp?type=registration');
      }, 500);
    }
  };

  return (
    <Auth3DBackground>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-md py-8"
      >
        {/* Back Button */}
        <motion.button
          onClick={() => navigate('/signup')}
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
            transition={{ delay: 0.3 }}
          >
            {/* Icon Badge */}
            <motion.div
              animate={{ y: [0, -4, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-white"
              style={{
                border: '1px solid rgba(0,194,203,0.3)',
                boxShadow: '0 8px 20px rgba(0,194,203,0.15)',
              }}
            >
              <UserPlus className="text-cyan-500" size={22} />
            </motion.div>

            <h1
              className="text-2xl font-bold mb-1"
              style={{
                background: 'linear-gradient(135deg, #0f172a, #3b82f6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Create Account
            </h1>
            <p className="text-slate-500 font-medium text-sm">
              Join as a{' '}
              <span className="font-bold text-cyan-600">
                {role === 'student' ? 'Student' : 'Recruiter'}
              </span>
            </p>
          </motion.div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
              <FormInput
                label="Full Name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                onBlur={() => handleBlur('name')}
                error={validationErrors.name}
                placeholder="John Doe"
                icon={User}
                required
              />
            </motion.div>

            {/* Email */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
              <FormInput
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                onBlur={() => handleBlur('email')}
                error={validationErrors.email}
                placeholder="you@example.com"
                icon={Mail}
                required
              />
            </motion.div>

            {/* Username */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
              <FormInput
                label="Username"
                value={formData.login_id}
                onChange={(e) => handleChange('login_id', e.target.value)}
                onBlur={() => handleBlur('login_id')}
                error={validationErrors.login_id}
                placeholder="john_doe"
                required
              />
              <p className="text-[11px] font-medium text-slate-400 mt-1.5 ml-1">3-20 characters, letters, numbers, - and _</p>
            </motion.div>

            {/* Password */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
              <PasswordInput
                label="Password"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                onBlur={() => handleBlur('password')}
                error={validationErrors.password}
                showStrength={true}
              />
            </motion.div>

            {/* Confirm Password */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }}>
              <PasswordInput
                label="Confirm Password"
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                onBlur={() => handleBlur('confirmPassword')}
                error={validationErrors.confirmPassword}
                showStrength={false}
              />
            </motion.div>

            {/* Submit */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="pt-2"
            >
              <SubmitButton
                onClick={handleSubmit}
                loading={isLoading}
                disabled={isLoading || Object.keys(validationErrors).length > 0}
              >
                Create Account <ArrowRight size={18} />
              </SubmitButton>
            </motion.div>

            {/* Terms */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.65 }}
              className="text-xs font-medium text-center text-slate-500"
            >
              By signing up, you agree to our{' '}
              <a href="#" className="text-cyan-600 hover:text-cyan-500 font-bold transition-colors">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="text-cyan-600 hover:text-cyan-500 font-bold transition-colors">
                Privacy Policy
              </a>
            </motion.p>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full" style={{ height: '1px', background: 'linear-gradient(90deg, transparent, rgba(15,23,42,0.1), transparent)' }} />
            </div>
          </div>

          {/* Sign In Link */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-center"
          >
            <p className="text-slate-500 font-medium text-sm">
              Already have an account?{' '}
              <button
                onClick={() => navigate('/signin')}
                className="text-cyan-600 font-bold hover:text-cyan-500 transition-colors cursor-pointer"
              >
                Sign in
              </button>
            </p>
          </motion.div>
        </motion.div>

        {/* Progress Dots */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.75 }}
          className="mt-8 flex justify-center gap-2"
        >
          <motion.div
            className="w-2.5 h-2.5 rounded-full"
            style={{ background: '#00C2CB', boxShadow: '0 0 10px rgba(0,194,203,0.5)' }}
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-300" />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-300" />
        </motion.div>
      </motion.div>

      {/* Notifications */}
      <ErrorMessage message={error} onClose={clearError} />
      <SuccessMessage message={successMessage} />
    </Auth3DBackground>
  );
};

export default RegisterScreen;
