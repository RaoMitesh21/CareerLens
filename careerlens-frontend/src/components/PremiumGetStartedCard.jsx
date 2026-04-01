import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { X, Sparkles, ArrowRight } from 'lucide-react';

const taglines = [
  'Discover Your Hidden Skills Gap',
  'AI-Powered Career Clarity Awaits',
  'Unlock Your True Market Value',
  'Turn Weaknesses Into Strengths',
  'Get recruited, not rejected',
  'Beat the ATS algorithm',
  'See what employers see in you',
  'Level up your career game',
  'Data-driven job readiness',
  'Your career clarity starts here',
  'Power up your job search',
  'Decode the hiring code',
  'Be unstoppable in your field',
  'Career matching perfected',
  'Skip the guesswork, nail the job',
  'Your competitive advantage awaits',
  'Transform your career trajectory',
  'Get noticed, get hired',
  'Master your skill stack',
];

export default function PremiumGetStartedCard({ 
  delaySeconds = 5, 
  navigateTo = '/signup',
  variant = 'default'
}) {
  const [isVisible, setIsVisible] = useState(false);
  const [tagline, setTagline] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Set random tagline
    setTagline(taglines[Math.floor(Math.random() * taglines.length)]);

    // Show card after delay
    const timer = setTimeout(() => {
      setIsVisible(true);
      console.log('🎯 Premium card should show now');
    }, delaySeconds * 1000);

    return () => clearTimeout(timer);
  }, [delaySeconds]);

  const handleClose = () => {
    setIsVisible(false);
  };

  const handleGetStarted = () => {
    setIsVisible(false);
    navigate(navigateTo);
  };

  // Minimal variant (bottom-right corner)
  if (variant === 'minimal') {
    return (
      <AnimatePresence>
        {isVisible && (
          <motion.div
            className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[9999] w-[90vw] max-w-xs"
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg sm:rounded-xl shadow-2xl border border-cyan-200 p-3 sm:p-4">
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 sm:w-5 h-4 sm:h-5 text-cyan-600" />
                  <span className="text-xs sm:text-sm font-bold text-gray-900">Premium Card</span>
                </div>
                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600 p-0.5"
                >
                  <X className="w-4 sm:w-5 h-4 sm:h-5" />
                </button>
              </div>
              <p className="text-xs sm:text-sm text-gray-700 mb-3 font-medium line-clamp-2">"{tagline}"</p>
              <button
                onClick={handleGetStarted}
                className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-2 rounded-lg text-xs sm:text-sm font-semibold hover:from-cyan-700 hover:to-blue-700 transition-all"
              >
                Get Started
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  // Default variant (full modal)
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 z-[9999] flex items-end sm:items-center justify-center p-4 sm:p-0"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Card */}
          <motion.div
            className="relative bg-white rounded-2xl shadow-2xl border border-cyan-100 w-full sm:max-w-sm overflow-hidden"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 px-6 py-8 relative overflow-hidden">
              {/* Decorative blobs */}
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-white/10 rounded-full blur-2xl" />
              <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-white/5 rounded-full blur-2xl" />

              <div className="relative z-10 flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-white animate-pulse" />
                  <span className="text-xs font-bold text-white/90 uppercase tracking-widest">Premium</span>
                </div>
                <button
                  onClick={handleClose}
                  className="text-white/70 hover:text-white transition-colors p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <h2 className="text-3xl font-bold text-white leading-tight">
                Ready to Transform Your Career?
              </h2>
            </div>

            {/* Body */}
            <div className="p-6">
              {/* Tagline */}
              <motion.p
                className="text-lg font-semibold text-gray-800 mb-6 leading-snug"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
              >
                "{tagline}"
              </motion.p>

              {/* Benefits */}
              <motion.div
                className="space-y-3 mb-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.25 }}
              >
                {['AI-powered analysis', 'Personalized roadmap', '2 minutes to start'].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm text-gray-700">
                    <div className="w-2 h-2 bg-cyan-600 rounded-full flex-shrink-0" />
                    {item}
                  </div>
                ))}
              </motion.div>

              {/* CTA */}
              <motion.button
                onClick={handleGetStarted}
                className="w-full bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 hover:shadow-lg transition-all"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Get Started Now
                <ArrowRight className="w-5 h-5" />
              </motion.button>

              <p className="text-center text-xs text-gray-500 mt-4">
                No credit card required • Takes 2 minutes
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
