/* ═══════════════════════════════════════════════════════════════════
   Navbar — Responsive floating glass nav with smooth scroll animation
   ═══════════════════════════════════════════════════════════════════ */

import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Logo from './Logo';

export default function Navbar() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('hero');
  const isLandingPage = location.pathname === '/';

  // Track which section is in view using Intersection Observer
  useEffect(() => {
    if (!isLandingPage) return;

    const sections = ['hero', 'features', 'benefits', 'contact'];
    const observers = [];

    const observerOptions = {
      root: null,
      rootMargin: '-50% 0px -50% 0px',
      threshold: 0,
    };

    sections.forEach((sectionId) => {
      const element = document.getElementById(sectionId);
      if (element) {
        const observer = new IntersectionObserver((entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setActiveSection(sectionId);
            }
          });
        }, observerOptions);
        observer.observe(element);
        observers.push(observer);
      }
    });

    return () => {
      observers.forEach((obs) => obs.disconnect());
    };
  }, [isLandingPage]);

  // Handle smooth scroll to section
  const scrollToSection = (sectionId) => {
    setMobileMenuOpen(false);
    if (isLandingPage) {
      // Delay scroll slightly so mobile menu closing animation completes
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 350);
    }
  };

  // For landing page, use scroll links; for other pages, use router links
  const navLinks = [
    { to: isLandingPage ? null : '/', section: isLandingPage ? 'hero' : null, label: 'Home' },
    { to: null, section: 'features', label: 'Features' },
    { to: null, section: 'benefits', label: 'Benefits' },
    { to: null, section: 'contact', label: 'Contact' },
  ];

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(16px) saturate(180%)',
        WebkitBackdropFilter: 'blur(16px) saturate(180%)',
        borderBottom: '1px solid rgba(0,0,0,0.04)',
        boxShadow: '0 1px 8px rgba(0,0,0,0.03)',
      }}
    >
      <nav className="section-container flex items-center justify-between py-3 sm:py-4">
        {/* Logo */}
        <Link to="/" className="flex items-center no-underline">
          <Logo size="lg" />
        </Link>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex rounded-full px-1.5 py-1.5 items-center gap-1"
          style={{
            background: 'rgba(255, 255, 255, 0.65)',
            backdropFilter: 'blur(20px) saturate(160%)',
            WebkitBackdropFilter: 'blur(20px) saturate(160%)',
            border: '1px solid rgba(255, 255, 255, 0.5)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {navLinks.map((link, idx) => {
            const isActive = isLandingPage && activeSection === link.section;
            
            return (
              <motion.div key={idx} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                {link.section && isLandingPage ? (
                  // Section scroll link for landing page
                  <button
                    onClick={() => scrollToSection(link.section)}
                    className={`
                      relative px-4 py-1.5 rounded-full text-sm font-medium no-underline transition-all duration-200 border-none bg-transparent cursor-pointer
                      ${isActive ? 'text-cyan-700' : 'text-ink-secondary hover:text-ink'}
                    `}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="nav-active-pill"
                        className="absolute inset-0 rounded-full"
                        style={{ background: 'rgba(0, 194, 203, 0.12)', boxShadow: '0 0 12px rgba(0,194,203,0.1)' }}
                        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10">{link.label}</span>
                  </button>
                ) : (
                  // Router link for other pages
                  <Link
                    to={link.to || '/'}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`
                      relative px-4 py-1.5 rounded-full text-sm font-medium no-underline transition-colors duration-200
                      ${location.pathname === link.to ? 'text-white' : 'text-ink-secondary hover:text-ink'}
                    `}
                    style={location.pathname === link.to ? { background: '#232B32' } : {}}
                  >
                    {location.pathname === link.to && (
                      <motion.div
                        layoutId="nav-pill"
                        className="absolute inset-0 rounded-full"
                        style={{ background: '#232B32' }}
                        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10">{link.label}</span>
                  </Link>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Desktop CTA */}
        <div className="hidden md:block">
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link to="/signup" className="btn-primary !py-2 !px-5 !text-sm">
              Get Started
            </Link>
          </motion.div>
        </div>

        {/* Mobile Menu Button */}
        <motion.button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg hover:bg-white/5 transition-colors border-none bg-transparent cursor-pointer"
          aria-label="Toggle menu"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-ink">
            {mobileMenuOpen ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </motion.button>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden border-t border-slate-100"
            style={{ background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(20px) saturate(180%)', WebkitBackdropFilter: 'blur(20px) saturate(180%)', boxShadow: '0 8px 32px rgba(0,0,0,0.08)' }}
          >
            <div className="section-container py-4 flex flex-col gap-2">
              {navLinks.map((link, idx) => {
                const isActive = isLandingPage && activeSection === link.section;
                
                return (
                  <motion.div 
                    key={idx}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: idx * 0.05 }}
                  >
                    {link.section && isLandingPage ? (
                      <button
                        onClick={() => scrollToSection(link.section)}
                        className={`
                          w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium no-underline transition-all border-none bg-transparent cursor-pointer
                          ${isActive ? 'text-cyan-700 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}
                        `}
                        style={isActive ? { background: 'rgba(0, 194, 203, 0.1)', color: '#0891b2' } : {}}
                      >
                        {link.label}
                      </button>
                    ) : (
                      <Link
                        to={link.to || '/'}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`
                          block px-4 py-2.5 rounded-lg text-sm font-medium no-underline transition-colors
                          ${location.pathname === link.to
                            ? 'text-cyan-700 font-semibold'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                          }
                        `}
                        style={location.pathname === link.to ? { background: 'rgba(0, 194, 203, 0.1)' } : {}}
                      >
                        {link.label}
                      </Link>
                    )}
                  </motion.div>
                );
              })}
              <motion.div 
                className="pt-2 border-t border-slate-100"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                <Link to="/signup" className="btn-primary w-full text-center !py-2.5 block">
                  Get Started
                </Link>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
