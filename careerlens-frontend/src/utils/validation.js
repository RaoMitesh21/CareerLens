/**
 * Validation Utilities for CareerLens Auth
 * Email, Password, Username, OTP validation
 */

// Email validation regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const validateEmail = (email) => {
  if (!email) {
    return { valid: false, error: 'Email is required' };
  }
  if (!EMAIL_REGEX.test(email)) {
    return { valid: false, error: 'Invalid email format' };
  }
  return { valid: true };
};

// Password validation with detailed requirements
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

export const validatePassword = (password) => {
  // Handle undefined or null password
  if (!password) {
    return {
      valid: false,
      errors: ['Password is required'],
      requirements: {
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false,
      },
    };
  }

  const errors = [];
  const requirements = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[@$!%*?&]/.test(password),
  };

  if (password.length < 8) errors.push('At least 8 characters');
  if (!requirements.uppercase) errors.push('One uppercase letter (A-Z)');
  if (!requirements.lowercase) errors.push('One lowercase letter (a-z)');
  if (!requirements.number) errors.push('One number (0-9)');
  if (!requirements.special) errors.push('One special character (@$!%*?&)');

  return {
    valid: Object.values(requirements).every(Boolean),
    errors,
    requirements,
  };
};

// Password strength indicator
export const getPasswordStrength = (password) => {
  const requirements = {
    length: password && password.length >= 8,
    uppercase: password && /[A-Z]/.test(password),
    lowercase: password && /[a-z]/.test(password),
    number: password && /\d/.test(password),
    special: password && /[@$!%*?&]/.test(password),
  };

  if (!password) {
    return { 
      level: 'weak', 
      percent: 0, 
      color: '#ef4444',
      requirements,
    };
  }

  let strength = 0;

  // Check each requirement
  if (requirements.length) strength += 20;
  if (password.length >= 12) strength += 10;
  if (requirements.lowercase) strength += 20;
  if (requirements.uppercase) strength += 20;
  if (requirements.number) strength += 15;
  if (requirements.special) strength += 15;

  let level = 'weak';
  let color = '#ef4444'; // red

  if (strength >= 80) {
    level = 'strong';
    color = '#22c55e'; // green
  } else if (strength >= 60) {
    level = 'good';
    color = '#eab308'; // yellow
  } else if (strength >= 40) {
    level = 'fair';
    color = '#f97316'; // orange
  }

  return {
    level,
    percent: Math.min(strength, 100),
    color,
    requirements,
  };
};

// Username validation
export const validateUsername = (username) => {
  if (!username) {
    return { valid: false, error: 'Username is required' };
  }
  if (username.length < 3) {
    return { valid: false, error: 'Username must be at least 3 characters' };
  }
  if (username.length > 20) {
    return { valid: false, error: 'Username must be at most 20 characters' };
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    return {
      valid: false,
      error: 'Username can only contain letters, numbers, underscores, and hyphens',
    };
  }
  return { valid: true };
};

// Name validation
export const validateName = (name) => {
  if (!name) {
    return { valid: false, error: 'Name is required' };
  }
  if (name.length < 2) {
    return { valid: false, error: 'Name must be at least 2 characters' };
  }
  if (name.length > 100) {
    return { valid: false, error: 'Name must be at most 100 characters' };
  }
  if (!/^[a-zA-Z\s'-]+$/.test(name)) {
    return {
      valid: false,
      error: 'Name can only contain letters, spaces, apostrophes, and hyphens',
    };
  }
  return { valid: true };
};

// OTP validation
export const validateOTP = (otp) => {
  if (!otp) {
    return { valid: false, error: 'OTP is required' };
  }
  if (otp.length !== 6) {
    return { valid: false, error: 'OTP must be exactly 6 digits' };
  }
  if (!/^\d{6}$/.test(otp)) {
    return { valid: false, error: 'OTP must contain only numbers' };
  }
  return { valid: true };
};

// Confirm password validation
export const validatePasswordMatch = (password, confirmPassword) => {
  if (password !== confirmPassword) {
    return { valid: false, error: 'Passwords do not match' };
  }
  return { valid: true };
};

// Combined validation for register form
export const validateRegisterForm = (formData) => {
  const errors = {};

  // Validate name
  const nameValidation = validateName(formData.name);
  if (!nameValidation.valid) {
    errors.name = nameValidation.error;
  }

  // Validate email
  const emailValidation = validateEmail(formData.email);
  if (!emailValidation.valid) {
    errors.email = emailValidation.error;
  }

  // Validate username
  const usernameValidation = validateUsername(formData.login_id);
  if (!usernameValidation.valid) {
    errors.login_id = usernameValidation.error;
  }

  // Validate password
  const passwordValidation = validatePassword(formData.password);
  if (!passwordValidation.valid) {
    errors.password = 'Password does not meet requirements';
  }

  // Validate password match
  const matchValidation = validatePasswordMatch(
    formData.password,
    formData.confirmPassword
  );
  if (!matchValidation.valid) {
    errors.confirmPassword = matchValidation.error;
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  };
};

// Debounce function for validation
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export default {
  validateEmail,
  validatePassword,
  getPasswordStrength,
  validateUsername,
  validateName,
  validateOTP,
  validatePasswordMatch,
  validateRegisterForm,
  debounce,
};
