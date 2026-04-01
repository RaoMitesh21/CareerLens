import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { X, Sparkles, ArrowRight } from 'lucide-react';

// App-related taglines pool - different for each trigger
const taglinePool = [
  'Discover Your Hidden Skills Gap',
  'AI-Powered Career Clarity Awaits',
  'Unlock Your True Market Value',
  'Turn Weaknesses Into Strengths',
  'Get recruited, not rejected',
  'Beat the ATS algorithm',
  'See what employers see in you',
  'Level up your career game',
  'Data-driven job readiness',
  'From overlooked to overqualified',
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

// Get random tagline from pool
const getRandomTagline = () => {
  return taglinePool[Math.floor(Math.random() * taglinePool.length)];
};

export default function PremiumGetStartedCard({ 
  delaySeconds = 5, 
  onClose = null,
  navigateTo = '/signup',
  variant = 'default' // 'default' or 'minimal'
}) {
  const [isVisible, setIsVisible] = useState(false);
  const [tagline, setTagline] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Generate random tagline once when component mounts
    const newTagline = getRandomTagline();
    setTagline(newTagline);

    // Timer to show card after delay
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delaySeconds * 1000);

    return () => clearTimeout(timer);
  }, [delaySeconds]);

  const handleClose = () => {
    setIsVisible(false);
    if (onClose) onClose();
  };

  const handleGetStarted = () => {
    setIsVisible(false);
    navigate(navigateTo);
  };

  // Card Animation Variants
  const cardVariants = {
    hidden: {
      opacity: 0,
      scale: 0.85,
      y: 20,
    },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30,
      },
    },
    exit: {
      opacity: 0,
      scale: 0.8,
      y: -20,
      transition: {
        duration: 0.3,
      },
    },
  };

  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
  };

  if (variant === 'minimal') {
    // Minimal variant - corner notification (fully responsive)
    return (
      <AnimatePresence>
        {isVisible && (
          <motion.div
            className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 max-w-[90vw] sm:max-w-xs"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            <div className="bg-white rounded-lg sm:rounded-xl shadow-2xl border border-indigo-100 p-3 sm:p-4 w-full">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Sparkles className="w-4 sm:w-5 h-4 sm:h-5 text-cyan-600 flex-shrink-0" />
                  <span className="text-xs sm:text-sm font-semibold text-gray-900">Premium</span>
                </div>
                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
                >
                  <X className="w-4 sm:w-5 h-4 sm:h-5" />
                </button>
              </div>
              <p className="text-xs sm:text-sm text-gray-700 mb-4 font-medium line-clamp-3">{tagline}</p>
              <button
                onClick={handleGetStarted}
                className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-2 px-3 rounded-lg text-xs sm:text-sm font-semibold hover:from-cyan-700 hover:to-blue-700 transition-all active:scale-95"
              >
                Get Started
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  // Full variant - centered modal-style card (fully responsive)
  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={handleClose}
          />

          {/* Premium Card */}
          <motion.div
            className="fixed inset-0 flex items-center justify-center z-50 p-4 sm:p-6"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={handleClose}
          >
            <motion.div
              className="bg-white rounded-xl sm:rounded-2xl shadow-2xl border border-cyan-100 w-full max-w-sm overflow-hidden"
              variants={cardVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header with Gradient */}
              <div className="bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 px-4 sm:px-6 pt-6 pb-6 sm:pb-8 relative overflow-hidden">
                {/* Decorative circles */}
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-white/10 rounded-full blur-xl" />
                <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-400/10 rounded-full blur-xl" />

                <div className="relative z-10 flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 sm:w-6 h-5 sm:h-6 text-white animate-pulse flex-shrink-0" />
                    <span className="text-[10px] sm:text-xs font-bold text-white/90 uppercase tracking-widest">Premium</span>
                  </div>
                  <button
                    onClick={handleClose}
                    className="text-white/70 hover:text-white transition-colors hover:bg-white/10 rounded-lg p-1 flex-shrink-0"
                  >
                    <X className="w-5 sm:w-6 h-5 sm:h-6" />
                  </button>
                </div>

                <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2 leading-tight">
                  Ready to Transform Your Career?
                </h2>
              </div>

              {/* Content Area */}
              <div className="p-4 sm:p-6">
                {/* Random Tagline */}
                <motion.p
                  className="text-base sm:text-lg font-semibold text-gray-800 mb-4 sm:mb-6 leading-snug"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  "{tagline}"
                </motion.p>

                {/* Benefits List */}
                <motion.ul
                  className="space-y-2 sm:space-y-3 mb-4 sm:mb-6"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                >
                  {[
                    'AI-powered skill gap analysis',
                    'Personalized career roadmap',
                    'Just 2 minutes to get started',
                  ].map((benefit, i) => (
                    <li key={i} className="flex items-center gap-3 text-xs sm:text-sm text-gray-700">
                      <div className="w-1.5 h-1.5 bg-cyan-600 rounded-full flex-shrink-0" />
                      <span>{benefit}</span>
                    </li>
                  ))}
                </motion.ul>

                {/* CTA Button */}
                <motion.button
                  onClick={handleGetStarted}
                  className="w-full bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 text-white py-2.5 sm:py-3 rounded-lg sm:rounded-xl font-semibold flex items-center justify-center gap-2 text-sm sm:text-base hover:shadow-lg hover:from-cyan-700 hover:via-blue-700 hover:to-purple-700 transition-all active:scale-95"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Get Started Now
                  <ArrowRight className="w-4 sm:w-5 h-4 sm:h-5" />
                </motion.button>

                {/* Footer Text */}
                <p className="text-center text-[10px] sm:text-xs text-gray-500 mt-3 sm:mt-4">
                  No credit card required • Takes 2 minutes
                </p>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
