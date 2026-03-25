/* ═══════════════════════════════════════════════════════════════════
   LiveAnalysisPanel — Hero Right-Side Resume Analysis Simulation
   Phased AI workflow: INIT → RESUME → 10s ANALYZE → REVEAL
   Runs ONCE per session, then shows final state.
   ═══════════════════════════════════════════════════════════════════ */

import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const SESSION_KEY = 'cl_hero_anim_done';

/* ── Analysis labels (cycle during 10s blur) ────────────────── */
const ANALYSIS_STEPS = [
  'Uploading resume…',
  'Initializing AI engine…',
  'Extracting skills…',
  'Analyzing projects…',
  'Evaluating core competencies…',
  'Matching with target role…',
  'Calculating match score…',
  'Generating insights…',
  'Preparing report…',
  'Finalizing results…',
];

/* ── Timing (ms) ────────────────────────────────────────────── */
const T = {
  RESUME: 500,
  BLUR_ON: 1200,
  BLUR_OFF: 11200,
  SCORE: 11800,
  BARS: 12600,
  PROJECTS: 13400,
  STATS: 14000,
  SUGGESTIONS: 14600,
  DONE: 16000,
};
const STEP_INTERVAL = 1000;

/* ── Score Ring ──────────────────────────────────────────────── */
function ScoreRing({ score = 87, size = 180, animate = false }) {
  const [responsive, setResponsive] = useState(false);
  const displaySize = typeof window !== 'undefined' && window.innerWidth < 640 ? Math.min(size, 150) : size;
  const stroke = 12;
  const r = (displaySize - stroke) / 2;
  const C = 2 * Math.PI * r;
  const offset = C - (Math.min(100, Math.max(0, score)) / 100) * C;

  return (
    <div className="relative flex items-center justify-center mx-auto" style={{ width: displaySize, height: displaySize }}>
      <div className="absolute inset-0 rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%)', filter: 'blur(16px)', transform: 'scale(1.3)' }} />
      <svg width={size} height={size} className="-rotate-90 relative z-10">
        <defs>
          <linearGradient id="sr-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="55%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
          <filter id="sr-glow"><feGaussianBlur stdDeviation="2.5" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="url(#sr-grad)" strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={C} filter="url(#sr-glow)"
          initial={{ strokeDashoffset: animate ? C : offset }}
          animate={{ strokeDashoffset: offset }}
          transition={animate ? { duration: 1.8, ease: [0.22, 1, 0.36, 1] } : { duration: 0 }}
        />
      </svg>
      <div className="absolute text-center z-10">
        <motion.p
          className="text-4xl font-extrabold text-slate-900"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={animate ? { opacity: 0, scale: 0.85 } : {}}
          animate={{ opacity: 1, scale: 1 }}
          transition={animate ? { duration: 0.5, ease: [0.22, 1, 0.36, 1] } : { duration: 0 }}
        >{score}%</motion.p>
        <p className="text-[0.6rem] uppercase tracking-[0.16em] text-slate-500 mt-0.5">Match Score</p>
      </div>
    </div>
  );
}

/* ── Shimmer skeleton ───────────────────────────────────────── */
function Shimmer({ w = '100%', h = 8, delay = 0 }) {
  return (
    <div className="rounded-full overflow-hidden" style={{ width: w, height: h, background: 'rgba(148,163,184,0.06)' }}>
      <motion.div className="h-full w-full rounded-full"
        style={{ background: 'linear-gradient(90deg, transparent 25%, rgba(148,163,184,0.15) 50%, transparent 75%)', backgroundSize: '200% 100%' }}
        animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
        transition={{ duration: 1.5, repeat: Infinity, delay, ease: 'linear' }}
      />
    </div>
  );
}

/* ── Fade-in wrapper for sequential reveal ──────────────────── */
function Reveal({ visible, delay = 0, children, className = '' }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: visible ? 1 : 0, y: visible ? 0 : 12 }}
      transition={{ duration: 0.5, delay: visible ? delay : 0, ease: [0.4, 0, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
}

/* ── MAIN ────────────────────────────────────────────────────── */
export default function LiveAnalysisPanel() {
  const alreadyPlayed = useRef(
    typeof window !== 'undefined' && sessionStorage.getItem(SESSION_KEY) === '1'
  );
  const [phase, setPhase] = useState(alreadyPlayed.current ? 99 : 0);
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    if (alreadyPlayed.current) return;
    const ids = [];
    const t = (ms, fn) => ids.push(setTimeout(fn, ms));

    t(T.RESUME, () => setPhase(1));
    t(T.BLUR_ON, () => setPhase(2));
    ANALYSIS_STEPS.forEach((_, i) => t(T.BLUR_ON + i * STEP_INTERVAL, () => setStepIdx(i)));
    t(T.BLUR_OFF, () => setPhase(3));
    t(T.SCORE, () => setPhase(4));
    t(T.BARS, () => setPhase(5));
    t(T.PROJECTS, () => setPhase(6));
    t(T.STATS, () => setPhase(7));
    t(T.SUGGESTIONS, () => setPhase(8));
    t(T.DONE, () => { setPhase(99); sessionStorage.setItem(SESSION_KEY, '1'); });

    return () => ids.forEach(clearTimeout);
  }, []);

  const anim = !alreadyPlayed.current;
  const isBlurred = phase >= 0 && phase <= 2;
  const show = (minPhase) => !anim || phase >= minPhase;

  const skills = useMemo(() => [
    { cat: 'Core Skills', items: 'Python, ML, Data Analysis', pct: 85, bar: 'from-emerald-400 to-emerald-600' },
    { cat: 'Secondary', items: 'React, JS, Streamlit', pct: 65, bar: 'from-blue-400 to-blue-600' },
    { cat: 'Missing', items: 'Deep Learning, MLOps', pct: 30, bar: 'from-orange-400 to-red-500' },
  ], []);

  const projects = useMemo(() => [
    { name: 'CareerLens', tag: 'Most relevance', icon: '✅', c: '#067150' },
    { name: 'ThunderCast', tag: 'High relevance', icon: '✅', c: '#3b9579' },
    { name: 'Talksy', tag: 'Low relevance', icon: '⚠️', c: '#d97706' },
  ], []);

  const stats = useMemo(() => [
    { l: 'CGPA', v: '8.83', bg: 'rgba(6,182,212,0.1)', c: '#0891b2' },
    { l: 'Rank', v: '1st', bg: 'rgba(16,185,129,0.1)', c: '#059669' },
    { l: 'Status', v: 'Top Performer', bg: 'rgba(139,92,246,0.1)', c: '#7c3aed' },
  ], []);

  const suggestions = ['Learn MLOps', 'Add Deep Learning projects', 'Improve deployment skills'];

  /* ── Glass styles ──────────────────────────────────────────── */
  const panelStyle = {
    background: 'rgba(255,255,255,0.62)',
    backdropFilter: 'blur(28px) saturate(165%)',
    WebkitBackdropFilter: 'blur(28px) saturate(165%)',
    borderColor: 'rgba(255,255,255,0.55)',
    boxShadow: '0 28px 70px rgba(15,23,42,0.1), 0 10px 28px rgba(14,165,233,0.06), inset 0 1px 0 rgba(255,255,255,0.9), inset 0 0 20px rgba(255,255,255,0.2)',
  };

  const innerCard = {
    background: 'rgba(255,255,255,0.68)',
    borderColor: 'rgba(255,255,255,0.55)',
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.8), 0 2px 8px rgba(0,0,0,0.02)',
  };

  return (
    <div className="relative w-full flex items-start justify-center lg:pt-4">
      {/* BG blobs */}
      <div className="absolute inset-0 pointer-events-none">
        <motion.div className="absolute rounded-full blur-3xl"
          style={{ width: 260, height: 260, top: 15, right: 35, background: 'rgba(6,182,212,0.18)' }}
          animate={{ opacity: [0.4, 0.75, 0.4], scale: [0.96, 1.06, 0.96] }}
          transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }} />
        <motion.div className="absolute rounded-full blur-3xl"
          style={{ width: 280, height: 280, bottom: 15, left: 25, background: 'rgba(99,102,241,0.14)' }}
          animate={{ opacity: [0.3, 0.65, 0.3], scale: [1.04, 0.94, 1.04] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }} />
      </div>

      {/* ── PANEL ───────────────────────────────────────── */}
      <motion.div
        initial={anim ? { opacity: 0, y: 28, scale: 0.95 } : {}}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={anim ? { duration: 0.8, ease: [0.22, 1, 0.36, 1] } : { duration: 0 }}
        whileHover={{ y: -4, transition: { duration: 0.3 } }}
        className="relative w-full max-w-[500px] rounded-[24px] border p-5 overflow-hidden"
        style={panelStyle}
      >

        {/* ═══ CONTENT — sections fade in one-by-one after blur ═══ */}

        {/* 1. Resume Card */}
        <Reveal visible={show(1)} className="rounded-xl border p-3.5" >
          <div style={innerCard} className="rounded-xl border p-3.5 -m-3.5">
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-[0.6rem] uppercase tracking-widest text-slate-400">Resume</p>
                <p className="text-sm font-bold text-slate-900 truncate">Rao Mitesh</p>
                <p className="text-[0.7rem] text-slate-500">Data Scientist • Ahmedabad</p>
              </div>
              <div className="flex flex-wrap gap-1 justify-end max-w-[150px] shrink-0">
                {['Python', 'ML', 'SQL'].map(s => (
                  <span key={s} className="px-2 py-0.5 text-[9px] font-bold rounded-full border border-cyan-200 bg-cyan-50 text-cyan-700">{s}</span>
                ))}
              </div>
            </div>
          </div>
        </Reveal>

        {/* 2. Score Ring */}
        <Reveal visible={show(4)} className="mt-4">
          <ScoreRing score={87} animate={anim && show(4)} />
        </Reveal>

        {/* 3. Skill Bars */}
        <Reveal visible={show(5)} className="mt-3.5 space-y-2">
          {skills.map((s, i) => (
            <div key={s.cat}>
              <div className="flex justify-between text-[0.6rem] mb-0.5">
                <span className="font-bold text-slate-500 uppercase tracking-wider">{s.cat}</span>
                <span className="font-bold text-slate-800">{show(5) ? `${s.pct}%` : ''}</span>
              </div>
              <div className="h-[6px] rounded-full overflow-hidden" style={{ background: 'rgba(148,163,184,0.1)' }}>
                <motion.div
                  initial={anim ? { width: 0 } : { width: `${s.pct}%` }}
                  animate={{ width: show(5) ? `${s.pct}%` : '0%' }}
                  transition={anim ? { delay: i * 0.15, duration: 0.7, ease: [0.4, 0, 0.2, 1] } : { duration: 0 }}
                  className={`h-full rounded-full bg-gradient-to-r ${s.bar}`}
                />
              </div>
              <p className="text-[0.58rem] text-slate-400 mt-0.5">{s.items}</p>
            </div>
          ))}
        </Reveal>

        {/* 4. Projects */}
        <Reveal visible={show(6)} className="mt-3 rounded-lg border p-2.5">
          <div style={innerCard} className="rounded-lg border p-2.5 -m-2.5">
            <p className="text-[0.55rem] uppercase tracking-[0.14em] text-slate-400 font-bold mb-1.5">Projects</p>
            {projects.map(p => (
              <div key={p.name} className="flex items-center justify-between text-[0.72rem] py-0.5">
                <span className="text-slate-700 font-medium">{p.name}</span>
                <span className="flex items-center gap-1 text-[0.6rem] font-bold shrink-0" style={{ color: p.c }}>
                  {p.icon} {p.tag}
                </span>
              </div>
            ))}
          </div>
        </Reveal>

        {/* 5. Stat Pills */}
        <Reveal visible={show(7)} className="mt-2.5 flex gap-1.5 flex-wrap">
          {stats.map(s => (
            <div key={s.l}
              className="px-2 py-[3px] rounded-md text-[0.55rem] font-bold flex items-center gap-1"
              style={{ background: s.bg, color: s.c }}>
              <span className="opacity-70">{s.l}</span> {s.v}
            </div>
          ))}
        </Reveal>

        {/* 6. Suggestions */}
        <Reveal visible={show(8)} className="mt-3 rounded-lg border p-2.5">
          <div style={innerCard} className="rounded-lg border p-2.5 -m-2.5">
            <p className="text-[0.55rem] uppercase tracking-[0.14em] text-slate-400 font-bold mb-1.5">Suggestions</p>
            {suggestions.map(s => (
              <p key={s} className="text-[0.72rem] text-slate-600 flex items-center gap-1.5 py-0.5">
                <span className="w-1 h-1 rounded-full bg-violet-500 shrink-0" />
                {s}
              </p>
            ))}
          </div>
        </Reveal>


        {/* ═══ HEAVY BLUR OVERLAY (phases 0-2, ~10 seconds) ═══ */}
        <AnimatePresence>
          {anim && isBlurred && (
            <motion.div
              className="absolute inset-0 z-20 flex flex-col items-center justify-center rounded-[24px]"
              style={{
                background: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
              }}
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
            >
              <div className="flex flex-col items-center gap-4 px-6 w-full max-w-[320px]">
                {/* Spinner */}
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
                  className="w-10 h-10 rounded-full border-[2.5px] border-slate-200 border-t-cyan-500"
                />

                {/* Cycling text */}
                <AnimatePresence mode="wait">
                  <motion.p
                    key={phase === 0 ? 'init' : stepIdx}
                    className="text-sm font-semibold text-slate-600 text-center"
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.25 }}
                  >
                    {phase === 0 ? 'Initializing AI engine…' : ANALYSIS_STEPS[stepIdx]}
                  </motion.p>
                </AnimatePresence>

                {/* Progress bar */}
                <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: 'rgba(148,163,184,0.12)' }}>
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: 'linear-gradient(90deg, #06b6d4, #8b5cf6)' }}
                    initial={{ width: '0%' }}
                    animate={{ width: phase >= 2 ? '100%' : '5%' }}
                    transition={phase >= 2 ? { duration: 10, ease: 'linear' } : { duration: 0.5 }}
                  />
                </div>

                {/* Shimmer placeholders */}
                <div className="w-full space-y-2">
                  <Shimmer h={7} delay={0} />
                  <Shimmer w="85%" h={7} delay={0.15} />
                  <Shimmer w="70%" h={7} delay={0.3} />
                  <Shimmer w="55%" h={7} delay={0.45} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </motion.div>
    </div>
  );
}
