/* ── Landing Page with state for contact form ─────────────────── */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import LiveAnalysisPanel from '../components/LiveAnalysisPanel';
import FeatureCard from '../components/FeatureCard';
import Logo from '../components/Logo';

/* ── Rotating taglines ────────────────────────────────────────────── */
const taglines = [
  'Know Your Skill Gap\nBefore Recruiters Do.',
  'See what recruiters see\nbefore they say no.',
  'Spot the gap.\nFix the gap. Get the job.',
  "Don't let your skill gap\nbe a surprise.",
  'Audit your skills\nbefore they audit you.',
  'Debug your resume\nbefore deployment.',
  'Patch your skill gaps.\nUpgrade your career.',
  'The code review\nfor your career path.',
  'Optimize your stack\nbefore the interview.',
  'Turn your blind spots\ninto selling points.',
  "Be the candidate\nthey can't ignore.",
  'Close the gap between\nyou and your dream job.',
  'Reveal. Refine.\nRecruited.',
  'Outsmart\nthe screening process.',
  'Data-driven\ncareer clarity.',
  "View your profile\nthrough a recruiter's lens.",
  'Bring your hidden\nweaknesses into focus.',
  'The clarity you need\nto get hired.',
];

const TAGLINE_DURATION = 4000; // ms

/* ── Animated counter ─────────────────────────────────────────────── */
function AnimatedNum({ value, suffix = '' }) {
  const num = parseInt(value.replace(/[^0-9]/g, ''), 10);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const dur = 1800;
    function tick(now) {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(eased * num));
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }, [num]);

  return <>{display.toLocaleString()}{suffix}</>;
}

/* ── Feature data ─────────────────────────────────────────────────── */
const features = [
  {
    step: '01',
    title: 'Precision Match Engine',
    description:
      'ESCO-powered 3-tier scoring classifies skills as Core, Secondary, and Bonus — then calculates calibrated match scores with confidence weighting.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
      </svg>
    ),
    gradient: 'from-cyan-500/10 to-blue-500/10',
    accent: '#00C2CB',
  },
  {
    step: '02',
    title: 'Skill Gap Intelligence',
    description:
      "See exactly which skills you have and which you're missing — ranked by priority with confidence scores based on keyword frequency and context.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
    gradient: 'from-violet-500/10 to-fuchsia-500/10',
    accent: '#8B5CF6',
  },
  {
    step: '03',
    title: 'Smart Roadmap System',
    description:
      'Get a personalised learning roadmap — beginner to advanced — with phased skill targets, durations, and concrete actions to close your gaps.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 20V10" /><path d="M12 20V4" /><path d="M6 20v-6" />
      </svg>
    ),
    gradient: 'from-emerald-500/10 to-teal-500/10',
    accent: '#10B981',
  },
];

/* ── Stats ────────────────────────────────────────────────────────── */
const stats = [
  { value: '3007', suffix: '', label: 'Occupations', icon: '◆' },
  { value: '13896', suffix: '', label: 'Skills Tracked', icon: '◈' },
  { value: '123000', suffix: '+', label: 'Skill Relations', icon: '⊕' },
];

export default function LandingPage() {
  const [tagIdx, setTagIdx] = useState(0);
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', role: '', message: '' });
  const [formLoading, setFormLoading] = useState(false);
  const [formStatus, setFormStatus] = useState(null); // 'success' or 'error'
  const [formMessage, setFormMessage] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      setTagIdx((prev) => (prev + 1) % taglines.length);
    }, TAGLINE_DURATION);
    return () => clearInterval(timer);
  }, []);

  const [line1, line2] = taglines[tagIdx].split('\n');

  return (
    <div className="min-h-screen">
      {/* ── Background ───────────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        {/* Cyan blob — top right */}
        <div className="absolute rounded-full blur-3xl opacity-25"
          style={{ width: 'clamp(300px, 80vw, 800px)', height: 'clamp(300px, 80vw, 800px)', top: '-15%', right: '-10%',
            background: 'radial-gradient(circle, rgba(0,194,203,0.25) 0%, rgba(14,165,233,0.08) 40%, transparent 70%)' }} />
        {/* Violet blob — left */}
        <div className="absolute rounded-full blur-3xl opacity-15"
          style={{ width: 'clamp(200px, 60vw, 600px)', height: 'clamp(200px, 60vw, 600px)', top: '35%', left: '-12%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, rgba(59,130,246,0.05) 50%, transparent 70%)' }} />
        {/* Warm blob — bottom right */}
        <div className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 'clamp(150px, 50vw, 400px)', height: 'clamp(150px, 50vw, 400px)', bottom: '5%', right: '10%',
            background: 'radial-gradient(circle, rgba(249,115,22,0.10) 0%, transparent 70%)' }} />
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.02]"
          style={{ backgroundImage: 'linear-gradient(#232B32 1px, transparent 1px), linear-gradient(90deg, #232B32 1px, transparent 1px)',
            backgroundSize: '60px 60px' }} />
      </div>

      {/* ── Hero Section ─────────────────────────────────────────── */}
      <section id="hero" className="relative pt-32 pb-16 lg:pt-40 lg:pb-24" style={{ zIndex: 1 }}>
        <div className="section-container">
          <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-start">

            {/* Left — Copy */}
            <div className="flex flex-col gap-6">
              {/* Badge */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5 }}
              >
                <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide uppercase border" style={{
                  background: 'linear-gradient(135deg, rgba(0,194,203,0.08) 0%, rgba(139,92,246,0.06) 100%)',
                  borderColor: 'rgba(0,194,203,0.18)',
                  color: '#00C2CB',
                }}>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
                  </span>
                  AI-Powered Skill Analysis
                </span>
              </motion.div>

              {/* Headline — rotating taglines */}
              <div className="relative" style={{ minHeight: 'clamp(4rem, 12vw, 9.5rem)' }}>
                {/* Radial glow behind headline */}
                <div className="absolute -inset-10 rounded-full blur-3xl opacity-30 pointer-events-none" style={{ background: 'radial-gradient(ellipse at center, rgba(0,194,203,0.2) 0%, rgba(139,92,246,0.08) 50%, transparent 70%)' }} />
                <AnimatePresence mode="wait">
                  <motion.h1
                    key={tagIdx}
                    className="absolute top-0 left-0 w-full leading-[1.12] tracking-tight"
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontWeight: 800,
                      fontSize: 'clamp(1.85rem, 3.8vw, 3.2rem)',
                    }}
                    initial={{ y: 30, opacity: 0, filter: 'blur(6px)' }}
                    animate={{ y: 0, opacity: 1, filter: 'blur(0px)' }}
                    exit={{ y: -25, opacity: 0, filter: 'blur(6px)' }}
                    transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <span className="text-ink">{line1}</span>
                    <br />
                    <span style={{
                      background: 'linear-gradient(135deg, #00C2CB 0%, #3B82F6 50%, #8B5CF6 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}>{line2}</span>
                  </motion.h1>
                </AnimatePresence>

                {/* Progress bar under headline */}
                <div className="absolute bottom-0 left-0 w-64 h-[3px] rounded-full overflow-hidden" style={{ background: 'rgba(0,194,203,0.12)' }}>
                  <motion.div
                    key={tagIdx}
                    className="h-full rounded-full"
                    style={{ background: 'linear-gradient(90deg, #00C2CB, #8B5CF6)' }}
                    initial={{ width: '0%' }}
                    animate={{ width: '100%' }}
                    transition={{ duration: TAGLINE_DURATION / 1000, ease: 'linear' }}
                  />
                </div>
              </div>

              {/* Subtitle */}
              <motion.p
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
                className="text-ink-secondary text-lg max-w-md leading-relaxed"
              >
                Upload your resume. Pick a role. Get an instant, data-driven
                breakdown of what you have, what you're missing, and how to
                close the gap.
              </motion.p>

              {/* CTAs */}
              <motion.div
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.45, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
                className="flex flex-col md:flex-row items-start md:items-center gap-3 pt-2"
              >
                <Link to="/signup" className="btn-primary group">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:-translate-y-0.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Get Started
                </Link>
                <Link to="/signin" className="btn-secondary group">
                  <span className="flex items-center gap-2">
                    Sign In
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:translate-x-0.5">
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </span>
                </Link>
                <Link to="/demo" className="btn-secondary group" style={{ background: 'rgba(0, 194, 203, 0.06)', borderColor: 'rgba(0, 194, 203, 0.2)', color: '#00a8b0' }}>
                  <span>✦</span>
                  See Demo
                </Link>
              </motion.div>

              {/* Stats */}
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.6 }}
                className="flex items-center gap-6 pt-4"
              >
                {stats.map((stat, i) => (
                  <motion.div
                    key={i}
                    className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl"
                    style={{ background: 'rgba(255,255,255,0.5)', border: '1px solid rgba(35,43,50,0.06)' }}
                    whileHover={{ scale: 1.04, y: -2 }}
                    transition={{ type: 'spring', stiffness: 400 }}
                  >
                    <span className="text-lg">{stat.icon}</span>
                    <div className="flex flex-col">
                      <span className="text-lg text-ink leading-tight"
                        style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>
                        <AnimatedNum value={stat.value} suffix={stat.suffix} />
                      </span>
                      <span className="text-[0.65rem] text-ink-muted uppercase tracking-wider leading-tight">
                        {stat.label}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </div>

            {/* Right — Floating Nodes */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5, duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
              className="hidden lg:block relative"
              style={{
                filter: 'drop-shadow(0 20px 40px rgba(0,194,203,0.12))',
              }}
            >
              <LiveAnalysisPanel />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Trusted By / Tech Strip ──────────────────────────────── */}
      <section className="relative py-10" style={{ zIndex: 1 }}>
        <div className="section-container">
          <motion.div
            className="flex flex-col items-center gap-4"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-muted">
              Powered by the European Skills Framework
            </span>
            <div className="flex items-center gap-8 text-ink-muted/40">
              {['ESCO', 'FastAPI', 'React', 'MySQL', 'Python'].map((t, i) => (
                <span key={i} className="text-sm font-bold tracking-wider uppercase" style={{ fontFamily: 'var(--font-display)' }}>{t}</span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Features Section ─────────────────────────────────────── */}
      <section id="features" className="relative py-24" style={{ zIndex: 1 }}>
        <div className="section-container">
          {/* Section Header */}
          <motion.div
            className="text-center mb-16"
            initial={{ y: 30, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-widest mb-4" style={{
              background: 'rgba(0,194,203,0.06)',
              color: '#00C2CB',
              border: '1px solid rgba(0,194,203,0.12)',
            }}>
              ✦ How It Works
            </span>
            <h2 className="text-ink mt-3 tracking-tight"
              style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.75rem, 3vw, 2.5rem)' }}>
              Three engines.{' '}
              <span style={{
                background: 'linear-gradient(135deg, #00C2CB, #8B5CF6)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>One clear picture.</span>
            </h2>
            <p className="text-ink-secondary mt-3 max-w-lg mx-auto">
              Upload once. Our pipeline matches, analyzes, and plans your path — in seconds.
            </p>
          </motion.div>

          {/* Feature Cards — enhanced with step numbers + accent colors */}
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={i}
                className="glass-card p-8 flex flex-col gap-4 relative overflow-hidden group"
                initial={{ y: 40, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                whileHover={{ y: -8, scale: 1.02 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: i * 0.15, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              >
                {/* Step number — large faded background */}
                <span className="absolute top-4 right-5 text-6xl font-black opacity-[0.04] select-none"
                  style={{ fontFamily: 'var(--font-display)', color: feature.accent }}>
                  {feature.step}
                </span>

                {/* Top accent line */}
                <div className="absolute top-0 left-0 right-0 h-[3px] rounded-t-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style={{ background: `linear-gradient(90deg, ${feature.accent}, transparent)` }} />

                {/* Icon with gradient ring */}
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center relative"
                  style={{ background: `${feature.accent}10`, color: feature.accent }}>
                  <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-400" style={{ boxShadow: `inset 0 0 12px ${feature.accent}20, 0 0 20px ${feature.accent}10` }} />
                  {feature.icon}
                </div>

                {/* Step label */}
                <span className="text-[0.65rem] font-bold uppercase tracking-[0.15em]" style={{ color: feature.accent }}>
                  Step {feature.step}
                </span>

                {/* Title */}
                <h3 className="text-lg text-ink tracking-tight"
                  style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}>
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-sm text-ink-secondary leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Helps Students Section ────────────────────────── */}
      <section id="benefits" className="relative py-24" style={{ zIndex: 1 }}>
        <div className="section-container">
          {/* Section Header */}
          <motion.div
            className="text-center mb-16"
            initial={{ y: 30, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-widest mb-4" style={{
              background: 'rgba(16, 185, 129, 0.06)',
              color: '#10B981',
              border: '1px solid rgba(16, 185, 129, 0.12)',
            }}>
              ✦ For Students
            </span>
            <h2 className="text-ink mt-3 tracking-tight"
              style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.75rem, 3vw, 2.5rem)' }}>
              Accelerate Your Career{' '}
              <span style={{
                background: 'linear-gradient(135deg, #10B981, #06B6D4)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>Growth.</span>
            </h2>
            <p className="text-ink-secondary mt-3 max-w-lg mx-auto">
              Understand your strengths, identify skill gaps, and follow a personalized roadmap to land your dream role.
            </p>
          </motion.div>

          {/* Student Benefits Grid */}
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: '✦',
                title: 'Match Your Target Role',
                description: 'See exactly how your skills align with the precise requirements of your target position. Understand your readiness level instantly.'
              },
              {
                icon: '◈',
                title: 'Identify Critical Gaps',
                description: 'Discover which skills employers demand that you\'re currently missing. Prioritize your learning based on job market demand.'
              },
              {
                icon: '↗',
                title: 'Follow Your Growth Path',
                description: 'Get a structured, phased roadmap with concrete milestones. Progress from foundational skills to advanced expertise.'
              },
              {
                icon: '◷',
                title: 'Save Time & Money',
                description: 'Focus your learning efforts strategically. Avoid expensive courses that don\'t match your actual needs.'
              },
              {
                icon: '⊙',
                title: 'Gain Confidence',
                description: 'Enter interviews knowing exactly where you stand. Speak confidently about your strengths and planned improvements.'
              },
              {
                icon: '▲',
                title: 'Accelerate Success',
                description: 'With a data-driven plan, you\'re 3x more likely to land interviews and receive competitive offers.'
              }
            ].map((benefit, i) => (
              <motion.div
                key={i}
                className="glass-card p-6 flex flex-col gap-3 group hover:border-emerald-500/30"
                initial={{ y: 40, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                whileHover={{ y: -6, scale: 1.015 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: i * 0.1, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              >
                {/* Icon with gradient background */}
                <div className="w-11 h-11 rounded-xl flex items-center justify-center text-xl" style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(6,182,212,0.08) 100%)' }}>
                  {benefit.icon}
                </div>
                
                {/* Title */}
                <h3 className="text-base text-ink tracking-tight font-semibold"
                  style={{ fontFamily: 'var(--font-display)' }}>
                  {benefit.title}
                </h3>

                {/* Description */}
                <p className="text-sm text-ink-secondary leading-relaxed">
                  {benefit.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Helps Recruiters Section ──────────────────────── */}
      <section className="relative py-24 border-t border-surface-alt" style={{ zIndex: 1 }}>
        <div className="section-container">
          {/* Section Header */}
          <motion.div
            className="text-center mb-16"
            initial={{ y: 30, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-widest mb-4" style={{
              background: 'rgba(249, 115, 22, 0.06)',
              color: '#F97316',
              border: '1px solid rgba(249, 115, 22, 0.12)',
            }}>
              ✦ For Recruiters
            </span>
            <h2 className="text-ink mt-3 tracking-tight"
              style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.75rem, 3vw, 2.5rem)' }}>
              Streamline Hiring &{' '}
              <span style={{
                background: 'linear-gradient(135deg, #F97316, #DC2626)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>Find Better Talent.</span>
            </h2>
            <p className="text-ink-secondary mt-3 max-w-lg mx-auto">
              Evaluate candidates faster with objective skill matching. Reduce screening time by 70% and focus on top prospects.
            </p>
          </motion.div>

          {/* Recruiter Benefits Grid */}
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: '⚡',
                title: 'Batch Skill Analysis',
                description: 'Upload multiple resumes at once and get instant skill matching reports for all candidates. Evaluate dozens in minutes.'
              },
              {
                icon: '≡',
                title: 'Objective Scoring',
                description: 'Eliminate bias with data-driven skill assessments. See which candidates truly match your requirements.'
              },
              {
                icon: '◉',
                title: 'Deep Skill Insights',
                description: 'Understand not just what skills candidates claim to have, but their proficiency level across 13,896 tracked competencies.'
              },
              {
                icon: '◫',
                title: 'Better Candidate Match',
                description: 'Find candidates who not only have the required skills but also match your career progression and development needs.'
              },
              {
                icon: '📈',
                title: 'Reduce Hiring Time',
                description: 'Cut screening time dramatically. Focus your human evaluation on qualified candidates, not gatekeeping applications.'
              },
              {
                icon: '✓',
                title: 'Improve Retention',
                description: 'Hire talent that\'s genuinely prepared for the role. Workers matched on skills show 40% higher retention rates.'
              }
            ].map((benefit, i) => (
              <motion.div
                key={i}
                className="glass-card p-6 flex flex-col gap-3 group hover:border-orange-500/30"
                initial={{ y: 40, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                whileHover={{ y: -6, scale: 1.015 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: i * 0.1, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              >
                {/* Icon with gradient background */}
                <div className="w-11 h-11 rounded-xl flex items-center justify-center text-xl" style={{ background: 'linear-gradient(135deg, rgba(249,115,22,0.08) 0%, rgba(220,38,38,0.06) 100%)' }}>
                  {benefit.icon}
                </div>
                
                {/* Title */}
                <h3 className="text-base text-ink tracking-tight font-semibold"
                  style={{ fontFamily: 'var(--font-display)' }}>
                  {benefit.title}
                </h3>

                {/* Description */}
                <p className="text-sm text-ink-secondary leading-relaxed">
                  {benefit.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Contact Us Section — Two Column Layout ────────────────── */}
      <section id="contact" className="relative py-24 border-t border-surface-alt" style={{ zIndex: 1 }}>
        <div className="section-container">
          <motion.div
            className="grid lg:grid-cols-2 gap-16 items-start"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            {/* Left Column — Questions & Info */}
            <motion.div
              className="flex flex-col gap-8"
              initial={{ x: -40, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              {/* Header */}
              <div>
                <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-widest mb-4" style={{
                  background: 'rgba(139, 92, 246, 0.06)',
                  color: '#8B5CF6',
                  border: '1px solid rgba(139, 92, 246, 0.12)',
                }}>
                  ✦ Let's Connect
                </span>
                <h2 className="text-ink mt-3 tracking-tight"
                  style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.75rem, 3vw, 2.5rem)' }}>
                  Have a Question?{' '}
                  <span style={{
                    background: 'linear-gradient(135deg, #8B5CF6, #00C2CB)',
                    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                  }}>We're Here to Help.</span>
                </h2>
                <p className="text-ink-secondary mt-4 text-lg leading-relaxed max-w-md">
                  Whether you're a student exploring career paths or a recruiter looking to streamline hiring, we're ready to support your journey.
                </p>
              </div>

              {/* FAQ Style Questions */}
              <div className="flex flex-col gap-4">
                {[
                  {
                    icon: '▭',
                    q: 'How does the skill analysis work?',
                    a: 'Our AI analyzes your resume against 13,896 skills using ESCO framework to provide precise, data-driven insights.'
                  },
                  {
                    icon: '◬',
                    q: 'Can I get a personalized roadmap?',
                    a: 'Yes! Our roadmap system creates phased learning paths tailored to your target role and current skills.'
                  },
                  {
                    icon: '◯',
                    q: 'Is it suitable for recruiters too?',
                    a: 'Absolutely. Batch analyze candidates, get objective skill matching, and make hiring 70% faster.'
                  },
                  {
                    icon: '◆',
                    q: 'How secure is my data?',
                    a: 'We employ enterprise-grade encryption and never share your data. Your privacy is our priority.'
                  }
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    className="glass-card p-5 rounded-xl hover:border-violet-500/30 transition-all group"
                    initial={{ y: 20, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true, margin: '-50px' }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <div className="flex gap-3">
                      <span className="text-2xl flex-shrink-0">{item.icon}</span>
                      <div className="flex flex-col gap-1">
                        <h4 className="text-sm font-semibold text-ink">{item.q}</h4>
                        <p className="text-xs text-ink-secondary leading-relaxed">{item.a}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Contact Info Minimal */}
              <div className="flex flex-col gap-3 pt-4 border-t border-surface-alt">
                <p className="text-sm text-ink-secondary">
                  <span className="inline-block font-semibold text-ink">Direct:</span> raomitesh12@gmail.com
                </p>
                <p className="text-sm text-ink-secondary">
                  <span className="inline-block font-semibold text-ink">Response:</span> Within 24 hours
                </p>
              </div>
            </motion.div>

            {/* Right Column — Contact Form */}
            {/* Right Column — Contact Form */}
            <motion.div
              className="p-8 md:p-10 rounded-2xl"
              initial={{ x: 40, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              style={{
                background: 'rgba(255, 255, 255, 0.88)',
                backdropFilter: 'blur(30px) saturate(160%)',
                WebkitBackdropFilter: 'blur(30px) saturate(160%)',
                border: '1px solid rgba(255, 255, 255, 0.7)',
                boxShadow: '0 24px 48px rgba(15, 23, 42, 0.06), 0 8px 20px rgba(0, 194, 203, 0.08), inset 0 1px 0 rgba(255,255,255,0.95)'
              }}
            >
              <form 
                onSubmit={async (e) => {
                  e.preventDefault();
                  setFormLoading(true);
                  setFormStatus(null);
                  setFormMessage('');

                  try {
                    const payload = {
                      name: formData.name,
                      email: formData.email,
                      subject: formData.subject,
                      role: formData.role,
                      message: formData.message
                    };

                    const response = await fetch('http://localhost:8000/api/contact/submit', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload)
                    });

                    if (!response.ok) {
                      const error = await response.json();
                      setFormStatus('error');
                      setFormMessage(error.detail || 'Failed to send message. Please try again.');
                      setFormLoading(false);
                      return;
                    }

                    const data = await response.json();
                    setFormStatus('success');
                    setFormMessage(data.message || 'Thank you! We\'ll get back to you within 24 hours.');
                    setFormData({ name: '', email: '', subject: '', role: '', message: '' });
                    setFormLoading(false);
                  } catch (err) {
                    console.error('Form submission error:', err);
                    setFormStatus('error');
                    setFormMessage('Connection error. Please check your internet and try again.');
                    setFormLoading(false);
                  }
                }}
                className="flex flex-col gap-6"
              >
                {/* Form Title */}
                <div className="pb-4 border-b border-slate-200">
                  <h3 className="text-2xl text-slate-800 font-bold" style={{ fontFamily: 'var(--font-display)' }}>
                    Send Us a Message
                  </h3>
                  <p className="text-sm text-slate-500 mt-1 font-medium">
                    We'll get back to you within 24 hours
                  </p>
                </div>

                {/* Name Input */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700">Full Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="John Doe"
                    required
                    disabled={formLoading}
                    className="input-3d placeholder:text-slate-400 disabled:opacity-50"
                  />
                </div>

                {/* Email Input */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700">Email Address *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="john@example.com"
                    required
                    disabled={formLoading}
                    className="input-3d placeholder:text-slate-400 disabled:opacity-50"
                  />
                </div>

                {/* Subject Input */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700">Subject *</label>
                  <input
                    type="text"
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    placeholder="What is this about?"
                    required
                    disabled={formLoading}
                    className="input-3d placeholder:text-slate-400 disabled:opacity-50"
                  />
                </div>

                {/* Role Select */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700">You are a *</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    required
                    disabled={formLoading}
                    className="input-3d cursor-pointer appearance-none disabled:opacity-50"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                      backgroundPosition: `right 0.5rem center`,
                      backgroundRepeat: `no-repeat`,
                      backgroundSize: `1.5em 1.5em`,
                      paddingRight: `2.5rem`
                    }}
                  >
                    <option value="">Select your role</option>
                    <option value="Student">Student / Career Seeker</option>
                    <option value="Recruiter">Recruiter / HR Professional</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                {/* Message Textarea */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700">Your Message *</label>
                  <textarea
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    placeholder="Tell us how we can help you..."
                    rows="5"
                    required
                    disabled={formLoading}
                    className="input-3d resize-none placeholder:text-slate-400 disabled:opacity-50"
                    style={{ fontFamily: 'var(--font-body)' }}
                  />
                </div>

                {/* Submit Button */}
                <motion.button
                  type="submit"
                  disabled={formLoading}
                  whileHover={!formLoading ? { scale: 1.01, y: -3 } : {}}
                  whileTap={!formLoading ? { scale: 0.98 } : {}}
                  className="mt-2 w-full py-4 rounded-xl font-bold text-white transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
                  style={{
                    background: 'linear-gradient(180deg, #00d4dd 0%, #00aeb6 100%)',
                    boxShadow: 'var(--shadow-btn-3d)',
                    textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                  }}
                >
                  <span className="flex items-center justify-center gap-2">
                    {formLoading ? (
                      <>
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                          className="w-5 h-5"
                        >
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                          </svg>
                        </motion.div>
                        Sending...
                      </>
                    ) : (
                      <>
                        Send Message
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="22" y1="2" x2="11" y2="13" />
                          <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                      </>
                    )}
                  </span>
                </motion.button>

                {/* Status Messages */}
                {formStatus === 'success' && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-sm font-medium"
                  >
                    ✓ {formMessage}
                  </motion.div>
                )}
                {formStatus === 'error' && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm font-medium"
                  >
                    ✕ {formMessage}
                  </motion.div>
                )}
                
                {/* Privacy Note */}
                <p className="text-xs text-slate-400 text-center pt-2 font-medium">
                  Your information is secure and will never be shared.
                </p>
              </form>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ── Bottom CTA ───────────────────────────────────────────── */}
      <section className="relative py-24" style={{ zIndex: 1 }}>
        <div className="section-container">
          <motion.div
            className="relative overflow-hidden rounded-2xl p-12 md:p-16 text-center flex flex-col items-center gap-6"
            style={{
              background: 'linear-gradient(135deg, #1a2027 0%, #232B32 50%, #1a2027 100%)',
              boxShadow: '0 30px 60px -12px rgba(0,0,0,0.2)',
            }}
            initial={{ y: 40, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            {/* Decorative blobs inside CTA */}
            <div className="absolute rounded-full blur-3xl opacity-25"
              style={{ width: 350, height: 350, top: '-20%', right: '-5%', background: 'radial-gradient(circle, #00C2CB 0%, transparent 70%)' }} />
            <div className="absolute rounded-full blur-3xl opacity-15"
              style={{ width: 250, height: 250, bottom: '-15%', left: '10%', background: 'radial-gradient(circle, #8B5CF6 0%, transparent 70%)' }} />

            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-white/40">
              Ready to start?
            </span>
            <h2 className="text-white tracking-tight relative"
              style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.5rem, 3vw, 2.25rem)' }}>
              Your next career move starts with{' '}
              <span style={{ color: '#00C2CB' }}>clarity.</span>
            </h2>
            <p className="text-white/60 max-w-md">
              It takes 30 seconds. No sign-up required. Just upload your resume
              and select a target role.
            </p>
            <div className="flex flex-col md:flex-row items-center gap-4 mt-2">
              <Link to="/signup"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl text-base font-semibold text-[#232B32] transition-all hover:-translate-y-1 no-underline w-full md:w-auto justify-center"
                style={{ background: '#00C2CB', boxShadow: '0 6px 24px rgba(0,194,203,0.4), 0 0 40px rgba(0,194,203,0.15)' }}>
                Get Started Free
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </Link>
              <Link to="/demo"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl text-base font-semibold text-white/80 border border-white/15 hover:border-white/30 hover:text-white transition-all no-underline w-full md:w-auto justify-center">
                Try Demo First
              </Link>
              <Link to="/signin"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl text-base font-semibold text-white/80 border border-white/15 hover:border-white/30 hover:text-white transition-all no-underline w-full md:w-auto justify-center">
                Already have account?
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Enhanced Footer ──────────────────────────────────────── */}
      <footer className="relative" style={{ zIndex: 1 }}>
        {/* Gradient top border */}
        <div className="h-px w-full" style={{ background: 'linear-gradient(90deg, transparent, rgba(0,194,203,0.3), rgba(139,92,246,0.2), transparent)' }} />
        {/* Footer Content */}
        <div className="section-container py-16">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            {/* Brand Column */}
            <div className="flex flex-col gap-4">
              <Logo size="md" />
              <p className="text-sm text-ink-secondary leading-relaxed">
                AI-powered skill analysis empowering students and recruiters with data-driven clarity.
              </p>
              <div className="flex items-center gap-3 pt-2">
                {[
                  { icon: '𝕏', href: '#' },
                  { icon: '🔗', href: '#' },
                  { icon: '💼', href: '#' },
                  { icon: '📘', href: '#' }
                ].map((social, i) => (
                  <a
                    key={i}
                    href={social.href}
                    className="w-10 h-10 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors text-ink-secondary hover:text-ink"
                  >
                    {social.icon}
                  </a>
                ))}
              </div>
            </div>

            {/* Product Links */}
            <div className="flex flex-col gap-4">
              <h4 className="text-sm font-semibold text-ink">Product</h4>
              <nav className="flex flex-col gap-2.5">
                {['Features', 'Pricing', 'Security', 'Roadmap'].map((link) => (
                  <a
                    key={link}
                    href="#"
                    className="text-sm text-ink-secondary hover:text-ink transition-colors no-underline"
                  >
                    {link}
                  </a>
                ))}
              </nav>
            </div>

            {/* Resources Links */}
            <div className="flex flex-col gap-4">
              <h4 className="text-sm font-semibold text-ink">Resources</h4>
              <nav className="flex flex-col gap-2.5">
                {['Documentation', 'Blog', 'API Docs', 'Careers'].map((link) => (
                  <a
                    key={link}
                    href="#"
                    className="text-sm text-ink-secondary hover:text-ink transition-colors no-underline"
                  >
                    {link}
                  </a>
                ))}
              </nav>
            </div>

            {/* Legal Links */}
            <div className="flex flex-col gap-4">
              <h4 className="text-sm font-semibold text-ink">Company</h4>
              <nav className="flex flex-col gap-2.5">
                {['About', 'Contact', 'Privacy', 'Terms'].map((link) => (
                  <a
                    key={link}
                    href="#"
                    className="text-sm text-ink-secondary hover:text-ink transition-colors no-underline"
                  >
                    {link}
                  </a>
                ))}
              </nav>
            </div>
          </div>

          {/* Newsletter Signup */}
          <motion.div
            className="py-8 px-6 rounded-xl mb-12"
            style={{ background: 'linear-gradient(135deg, rgba(0,194,203,0.08) 0%, rgba(139,92,246,0.08) 100%)', border: '1px solid rgba(0,194,203,0.1)' }}
            initial={{ y: 20, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className="text-lg font-semibold text-ink mb-2">Stay updated</h3>
                <p className="text-sm text-ink-secondary">
                  Get insights on industry trends and career development tips delivered to your inbox.
                </p>
              </div>
              <form className="flex gap-2">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-ink placeholder:text-ink-muted focus:outline-none focus:border-cyan-500/50 transition-colors text-sm"
                />
                <button
                  type="submit"
                  className="px-6 py-2.5 rounded-lg text-white font-semibold transition-all hover:scale-105 no-underline whitespace-nowrap"
                  style={{
                    background: 'linear-gradient(135deg, #00C2CB, #8B5CF6)',
                    boxShadow: '0 2px 12px rgba(0,194,203,0.25)'
                  }}
                >
                  Subscribe
                </button>
              </form>
            </div>
          </motion.div>

          {/* Bottom Footer Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-surface-alt text-sm text-ink-secondary">
            <span>© 2026 CareerLens. All rights reserved.</span>
            <span>ESCO-powered skill intelligence for global careers</span>
          </div>
        </div>
      </footer>

      {/* Noise overlay */}
      <div className="noise-overlay" />
    </div>
  );
}
