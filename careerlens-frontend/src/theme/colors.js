/**
 * CareerLens Theme Configuration
 * Glassmorphism + Neumorphism Hybrid Design System
 */

export const theme = {
  // Primary Colors - Sky Blue Theme
  colors: {
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9', // Main cyan
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c3d66',
    },
    secondary: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e', // Main green
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#145231',
    },
    neutral: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },

  // Glassmorphism Shadows
  shadows: {
    glass: {
      sm: '0 4px 16px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      md: '0 8px 32px rgba(0, 100, 200, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      lg: '0 20px 68px rgba(0, 100, 200, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      xl: '0 25px 80px rgba(0, 100, 200, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
    },
    glow: {
      cyan: '0 0 30px rgba(6, 182, 212, 0.3)',
      blue: '0 0 30px rgba(59, 130, 246, 0.3)',
      green: '0 0 30px rgba(34, 197, 94, 0.3)',
    },
  },

  // Gradient Effects
  gradients: {
    primary: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
    primaryHover: 'linear-gradient(135deg, #0284c7 0%, #0891b2 100%)',
    secondary: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
    background: 'linear-gradient(135deg, #f0f9ff 0%, #ecf0f1 50%, #e0f2fe 100%)',
    card: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(240, 249, 255, 0.8) 100%)',
    darkCard: 'linear-gradient(135deg, rgba(30, 30, 36, 0.95) 0%, rgba(17, 24, 39, 0.9) 100%)',
  },

  // Backdrop Blur Effects
  blur: {
    sm: 'blur(4px)',
    md: 'blur(8px)',
    lg: 'blur(12px)',
    xl: 'blur(16px)',
  },

  // Border Radius
  radius: {
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    full: '9999px',
  },

  // Spacing
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },

  // Typography
  typography: {
    h1: {
      fontSize: '2.5rem',
      fontWeight: '700',
      lineHeight: '1.2',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: '700',
      lineHeight: '1.3',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: '600',
      lineHeight: '1.4',
    },
    p: {
      fontSize: '1rem',
      fontWeight: '400',
      lineHeight: '1.6',
    },
    small: {
      fontSize: '0.875rem',
      fontWeight: '400',
      lineHeight: '1.5',
    },
  },

  // Animations
  animations: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
      slower: '700ms',
    },
    timingFunction: {
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    },
  },
};

// Utility function for glassmorphism card
export const getGlassCardClasses = (variant = 'light') => {
  const base = 'rounded-2xl backdrop-blur-md border transition-all duration-300';
  
  if (variant === 'light') {
    return `${base} bg-white/80 border-white/20 hover:bg-white/90 hover:border-white/30`;
  }
  
  if (variant === 'dark') {
    return `${base} bg-gray-800/80 border-gray-700/50 hover:bg-gray-800/90 hover:border-gray-600/70`;
  }
  
  return base;
};

// Utility function for gradient text
export const getGradientTextClasses = () => {
  return 'bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-500 bg-clip-text text-transparent';
};

export default theme;
