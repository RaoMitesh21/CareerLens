import React, { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, AlertCircle, CheckCircle, Lock } from 'lucide-react';
import { getPasswordStrength } from '../../utils/validation';

/* ═══════════════════════════════════════════════════════════════════
   AuthComponents — Premium Light-Theme Design System
   Bright glassmorphic inputs, cyan glowing focus states, 3D button effects
   ═══════════════════════════════════════════════════════════════════ */

/**
 * PasswordInput — Light glassmorphic password field
 * Features: eye toggle, animated strength bar, glowing focus
 */
export const PasswordInput = ({
  label,
  value,
  onChange,
  onBlur,
  error,
  placeholder = 'Enter password',
  showStrength = true,
  disabled = false,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const strength = showStrength && value ? getPasswordStrength(value) : null;

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}

      <div className="relative">
        <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={18} />
        <input
          type={showPassword ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={`auth-input pl-11 pr-11 ${error ? 'error' : ''}`}
        />

        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-cyan-500 transition-colors cursor-pointer"
        >
          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>

      {/* Animated Strength Indicator */}
      {showStrength && value && strength && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="space-y-2 pt-1"
        >
          <div className="h-1.5 rounded-full overflow-hidden bg-slate-200">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${strength.percent}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              style={{ backgroundColor: strength.color }}
              className="h-full rounded-full"
            />
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500">
              Strength: <span style={{ color: strength.color }} className="font-semibold">
                {strength.level}
              </span>
            </span>
            <span className="text-slate-400 font-medium">{strength.percent}%</span>
          </div>

          {/* Requirements Checklist */}
          <div className="space-y-1 text-xs">
            {[
              { key: 'length', label: 'At least 8 characters' },
              { key: 'uppercase', label: 'Uppercase letter' },
              { key: 'lowercase', label: 'Lowercase letter' },
              { key: 'number', label: 'Number (0-9)' },
              { key: 'special', label: 'Special character (@$!%*?&)' },
            ].map(({ key, label }) => (
              <motion.div
                key={key}
                className={`flex items-center gap-2 ${
                  strength.requirements[key] ? 'text-emerald-500 font-medium' : 'text-slate-500'
                }`}
                animate={{ opacity: 1, x: 0 }}
                initial={{ opacity: 0, x: -5 }}
                transition={{ duration: 0.2 }}
              >
                {strength.requirements[key] ? (
                  <CheckCircle size={14} className="text-emerald-500" />
                ) : (
                  <span className="w-3.5 h-3.5 rounded-full border border-slate-300 flex items-center justify-center text-[8px]">○</span>
                )}
                {label}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 text-red-500 text-xs mt-1 font-medium"
        >
          <AlertCircle size={14} />
          {error}
        </motion.div>
      )}
    </div>
  );
};

/**
 * OTPInput — Glowing 6-digit light boxes
 * Features: auto-focus, backspace navigation, glow on focus
 */
export const OTPInput = ({ value, onChange, error, disabled = false }) => {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const inputRefs = useRef([]);
  const otp = value.split('');

  const applyDigitsFromIndex = (startIndex, digits) => {
    const newOTP = [...otp];
    const sanitized = digits.replace(/\D/g, '').slice(0, 6 - startIndex);

    if (!sanitized) return;

    sanitized.split('').forEach((d, offset) => {
      newOTP[startIndex + offset] = d;
    });

    onChange(newOTP.join(''));

    const nextIndex = Math.min(startIndex + sanitized.length, 5);
    setFocusedIndex(nextIndex);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleChange = (index, digit) => {
    if (!digit) {
      const newOTP = [...otp];
      newOTP[index] = '';
      onChange(newOTP.join(''));
      return;
    }

    const normalized = digit.replace(/\D/g, '');
    if (!normalized) return;

    // Support autofill/paste-like multi-digit input in a single field.
    if (normalized.length > 1) {
      applyDigitsFromIndex(index, normalized);
      return;
    }

    const newOTP = [...otp];
    newOTP[index] = normalized;
    onChange(newOTP.join(''));

    // Auto-focus next box
    if (index < 5) {
      setFocusedIndex(index + 1);
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (index, e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text') || '';
    applyDigitsFromIndex(index, pasted);
  };

  const handleInputRef = (index, el) => {
    inputRefs.current[index] = el;
    if (focusedIndex === index && el) {
      el.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      e.preventDefault();
      const newOTP = [...otp];
      newOTP[index] = '';
      onChange(newOTP.join(''));

      if (index > 0) {
        setFocusedIndex(index - 1);
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      setFocusedIndex(index - 1);
    } else if (e.key === 'ArrowRight' && index < 5) {
      setFocusedIndex(index + 1);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-3 justify-center">
        {[0, 1, 2, 3, 4, 5].map((index) => (
          <motion.input
            key={index}
            ref={(el) => handleInputRef(index, el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={otp[index] || ''}
            onChange={(e) => handleChange(index, e.target.value)}
            onPaste={(e) => handlePaste(index, e)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onFocus={() => setFocusedIndex(index)}
            disabled={disabled}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05, duration: 0.3 }}
            className={`auth-otp-box ${error ? 'border-red-500 bg-red-50' : ''}`}
          />
        ))}
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-center gap-2 text-red-500 text-sm font-medium"
        >
          <AlertCircle size={16} />
          {error}
        </motion.div>
      )}
    </div>
  );
};

/**
 * FormInput — Light glassmorphic input with icon
 * Features: icon glow on focus, animated error display
 */
export const FormInput = ({
  label,
  value,
  onChange,
  onBlur,
  error,
  type = 'text',
  placeholder,
  icon: Icon,
  disabled = false,
  required = false,
}) => {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          {label} {required && <span className="text-cyan-600">*</span>}
        </label>
      )}

      <div className="relative">
        {Icon && (
          <Icon
            className={`absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none transition-colors duration-300 ${
              isFocused ? 'text-cyan-500' : 'text-slate-400'
            }`}
            size={18}
          />
        )}

        <input
          type={type}
          value={value}
          onChange={onChange}
          onBlur={(e) => {
            setIsFocused(false);
            onBlur?.(e);
          }}
          onFocus={() => setIsFocused(true)}
          placeholder={placeholder || label}
          disabled={disabled}
          className={`auth-input ${Icon ? 'pl-11' : ''} ${error ? 'error' : ''}`}
        />
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 text-red-500 text-xs mt-1 font-medium"
        >
          <AlertCircle size={14} />
          {error}
        </motion.div>
      )}
    </div>
  );
};

/**
 * SubmitButton — Gradient button with shimmer sweep + depth
 * Features: loading spinner, disabled state, 3D press effect
 */
export const SubmitButton = ({
  children,
  loading = false,
  disabled = false,
  onClick,
  variant = 'primary',
  className = '',
}) => {
  const variants = {
    primary: {
      background: 'linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%)',
      boxShadow: '0 10px 25px rgba(0, 194, 203, 0.3), 0 4px 10px rgba(15, 23, 42, 0.1)',
      color: 'white',
      border: 'none',
    },
    secondary: {
      background: 'linear-gradient(135deg, #10B981 0%, #14B8A6 100%)',
      boxShadow: '0 10px 25px rgba(16, 185, 129, 0.3), 0 4px 10px rgba(15, 23, 42, 0.1)',
      color: 'white',
      border: 'none',
    },
    outline: {
      background: 'rgba(255, 255, 255, 0.9)',
      boxShadow: '0 2px 5px rgba(15, 23, 42, 0.05)',
      border: '1px solid rgba(203, 213, 225, 1)',
      color: '#0f172a',
    },
  };

  const style = variants[variant] || variants.primary;

  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={loading || disabled}
      whileHover={!disabled ? { scale: 1.01, y: -2 } : {}}
      whileTap={!disabled ? { scale: 0.98, y: 1 } : {}}
      className={`auth-btn-shimmer w-full py-3.5 px-6 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer ${className}`}
      style={{
        ...style,
      }}
    >
      {loading ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 0.8, ease: 'linear' }}
          className={`w-5 h-5 border-2 rounded-full ${variant === 'outline' ? 'border-slate-300 border-t-cyan-500' : 'border-white/30 border-t-white'}`}
        />
      ) : (
        children
      )}
    </motion.button>
  );
};

/**
 * Toast Notification Components — Bright frosted glass toasts
 */
export const ErrorMessage = ({ message, onClose }) => {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -20, x: 100 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, y: -20, x: 100 }}
          className="fixed top-4 right-4 px-5 py-3.5 rounded-xl flex items-center gap-3 z-50"
          style={{
            background: 'rgba(254, 242, 242, 0.9)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(252, 165, 165, 1)',
            color: '#b91c1c',
            boxShadow: '0 10px 30px rgba(239, 68, 68, 0.15)',
          }}
        >
          <AlertCircle size={20} className="text-red-500" />
          <span className="text-sm font-semibold">{message}</span>
          <button
            onClick={onClose}
            className="ml-3 hover:opacity-70 transition-opacity text-red-500 cursor-pointer"
          >
            ✕
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export const SuccessMessage = ({ message, onClose }) => {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -20, x: 100 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, y: -20, x: 100 }}
          className="fixed top-4 right-4 px-5 py-3.5 rounded-xl flex items-center gap-3 z-50"
          style={{
            background: 'rgba(240, 253, 244, 0.9)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(134, 239, 172, 1)',
            color: '#15803d',
            boxShadow: '0 10px 30px rgba(34, 197, 94, 0.15)',
          }}
        >
          <CheckCircle size={20} className="text-emerald-500" />
          <span className="text-sm font-semibold">{message}</span>
          {onClose && (
            <button
              onClick={onClose}
              className="ml-3 hover:opacity-70 transition-opacity text-emerald-600 cursor-pointer"
            >
              ✕
            </button>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};
