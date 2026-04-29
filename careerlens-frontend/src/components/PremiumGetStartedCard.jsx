import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { X, Sparkles, User, Briefcase, ChevronRight, BarChart3, Target, Compass } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function PremiumGetStartedCard({ 
  delaySeconds = 5, 
  navigateTo = '/signup',
  variant = 'default'
}) {
  const CARD_Z_INDEX = 2147483000;
  const [isVisible, setIsVisible] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setIsMounted(true);

    const params = new URLSearchParams(window.location.search);
    if (params.get('showCard') === '1') {
      setIsVisible(true);
      return;
    }

    // Check if user previously closed it
    const hasClosed = typeof sessionStorage !== 'undefined' && 
                      sessionStorage.getItem('careerlens_premium_card_closed') === 'true';

    // Always show after delay, UI unless they already closed it
    if (!hasClosed) {
      const timer = window.setTimeout(() => {
        setIsVisible(true);
      }, delaySeconds * 1000);
  
      return () => window.clearTimeout(timer);
    }
  }, [delaySeconds]);

  const handleClose = () => {
    setIsVisible(false);
    // Remember they closed it so it doesn't annoy them constantly
    try { sessionStorage.setItem('careerlens_premium_card_closed', 'true'); } catch(e){}
  };

  const handleGetStarted = (role) => {
    setIsVisible(false);
    navigate(`${navigateTo}?role=${role}`);
  };

  useEffect(() => {
    if (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('careerlens_premium_card_closed') === 'true') {
       const params = new URLSearchParams(window.location.search);
       if (params.get('showCard') !== '1') {
         setIsVisible(false);
       }
    }
  }, []);

  if (!isMounted) return null;

  return createPortal(
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center p-3 sm:p-4 z-50 overflow-y-auto"
          style={{ zIndex: CARD_Z_INDEX }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          role="dialog"
          aria-modal="true"
        >
          {/* Performance Optimized Backdrop - Small blur, mostly darkening */}
          <motion.div 
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-[4px] min-h-[100vh]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose} 
          />

          {/* Premium Card — original structure, refined */}
          <motion.div
            className="relative w-full max-w-[95vw] sm:max-w-[540px] max-h-[92vh] overflow-y-auto scrollbar-hide rounded-[24px] sm:rounded-3xl bg-white cursor-default shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] border border-slate-100 my-auto"
            initial={{ scale: 0.95, y: 30, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.95, y: 20, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 250 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Warm accent strip */}
            <div className="h-1 w-full bg-gradient-to-r from-[#00C2CB] via-[#10B981] to-[#0EA5E9] rounded-t-[24px] sm:rounded-t-3xl" />

            {/* Header Section */}
            <div className="relative p-5 sm:p-8 pb-4 sm:pb-6 bg-slate-50 border-b border-slate-100">
              <div className="flex items-start justify-between mb-3 sm:mb-4">
                <div className="flex items-center gap-2 px-3 sm:px-4 py-1.5 bg-white rounded-full border border-slate-200 shadow-sm">
                  <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-cyan-600" />
                  <span className="text-[10px] sm:text-[11px] font-bold uppercase tracking-widest text-slate-800">CareerLens</span>
                </div>
                <button onClick={handleClose} className="p-1.5 sm:p-2 sm:-mr-1 -mr-1 rounded-full hover:bg-slate-200/60 transition-all duration-300 text-slate-400 hover:text-slate-700">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <motion.h2 
                className="text-2xl sm:text-[32px] font-extrabold text-slate-900 leading-[1.2] sm:leading-[1.15] tracking-tight mt-2 sm:mt-3"
                style={{ fontFamily: 'var(--font-display)' }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                Upload your resume. {' '}
                <span className="text-[#00C2CB]">See what's missing.</span>
              </motion.h2>
              <motion.p 
                className="mt-2 sm:mt-3 text-[14px] sm:text-[15px] leading-relaxed text-slate-600 font-medium max-w-sm"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                Paste a job description, upload your CV — we show you exactly which skills to learn next.
              </motion.p>
            </div>

            {/* Content & Capabilities */}
            <div className="p-5 sm:p-8 pb-4 sm:pb-6 bg-white">
              <div className="space-y-4 sm:space-y-4 mb-5 sm:mb-8">
                {[
                  { icon: Target, color: 'text-cyan-600', bg: 'bg-cyan-50/80', border: 'border-cyan-100', text: 'Compare your skills against 13,896 in our database' },
                  { icon: Compass, color: 'text-teal-600', bg: 'bg-teal-50/80', border: 'border-teal-100', text: 'Get a step-by-step learning plan for your gaps' },
                  { icon: BarChart3, color: 'text-blue-600', bg: 'bg-blue-50/80', border: 'border-blue-100', text: 'Recruiters: batch rank and screen candidates' }
                ].map((item, i) => (
                  <motion.div 
                    key={i} 
                    className="flex items-center gap-3 sm:gap-4 group cursor-default"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 + i * 0.1 }}
                  >
                    <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex flex-shrink-0 items-center justify-center border shadow-sm sm:group-hover:scale-105 transition-transform duration-300 ${item.bg} ${item.border}`}>
                      <item.icon className={`w-4 h-4 sm:w-[18px] sm:h-[18px] ${item.color}`} />
                    </div>
                    <span className="text-[13px] sm:text-[14.5px] text-slate-700 font-medium sm:group-hover:text-slate-900 transition-colors">{item.text}</span>
                  </motion.div>
                ))}
              </div>

              {/* Dual Action Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                <motion.button
                  onClick={() => handleGetStarted('student')}
                  className="group flex flex-row items-center justify-start sm:justify-center gap-3 sm:gap-4 py-3 sm:py-3.5 px-4 rounded-xl sm:rounded-[18px] bg-white border-2 border-slate-100 hover:border-cyan-400 hover:bg-cyan-50/30 hover:shadow-[0_4px_20px_rgba(0,194,203,0.12)] transition-all duration-300"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                >
                  <div className="p-2 rounded-full bg-slate-50 group-hover:bg-cyan-100 transition-colors duration-300">
                    <User className="w-4 h-4 sm:w-[18px] sm:h-[18px] text-slate-500 group-hover:text-cyan-600 transition-colors" />
                  </div>
                  <span className="text-[14px] sm:text-[15px] font-bold text-slate-800">I'm a Student</span>
                </motion.button>

                <motion.button
                  onClick={() => handleGetStarted('recruiter')}
                  className="group flex flex-row items-center justify-start sm:justify-center gap-3 sm:gap-4 py-3 sm:py-3.5 px-4 rounded-xl sm:rounded-[18px] bg-white border-2 border-slate-100 hover:border-blue-400 hover:bg-blue-50/30 hover:shadow-[0_4px_20px_rgba(59,130,246,0.12)] transition-all duration-300"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                >
                  <div className="p-2 rounded-full bg-slate-50 group-hover:bg-blue-100 transition-colors duration-300">
                    <Briefcase className="w-4 h-4 sm:w-[18px] sm:h-[18px] text-slate-500 group-hover:text-blue-600 transition-colors" />
                  </div>
                  <span className="text-[14px] sm:text-[15px] font-bold text-slate-800">I'm a Recruiter</span>
                </motion.button>
              </div>

              <motion.p 
                className="text-center text-[10px] sm:text-[11px] text-slate-400 mt-4 sm:mt-5 font-medium"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
              >
                Used by 2,400+ students across 45 colleges · Takes 30 seconds
              </motion.p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}

