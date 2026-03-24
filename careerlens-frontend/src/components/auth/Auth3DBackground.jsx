/* ═══════════════════════════════════════════════════════════════════
   Auth3DBackground — Immersive LIGHT animated background
   Used across all auth pages for a consistent premium feel
   ═══════════════════════════════════════════════════════════════════ */

import { motion } from 'framer-motion';
import { useMemo } from 'react';

/* ── Generate random particles ─────────────────────────────────── */
function generateParticles(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 3 + 1,
    duration: Math.random() * 20 + 20, // slightly slower for relaxed feel
    delay: Math.random() * 5,
    opacity: Math.random() * 0.4 + 0.1, // softer opacity
  }));
}

export default function Auth3DBackground({ children }) {
  const particles = useMemo(() => generateParticles(30), []);

  return (
    <div className="auth-bg-root">
      {/* ── Soft Light Base ─────────────────────────────────────── */}
      <div
        className="fixed inset-0"
        style={{
          background:
            'linear-gradient(135deg, #f8fafc 0%, #f0f9ff 25%, #e0f2fe 50%, #f1f5f9 75%, #f8fafc 100%)',
        }}
      />

      {/* ── Animated gradient blobs ───────────────────────────── */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Cyan blob — top right */}
        <motion.div
          className="absolute rounded-full"
          style={{
            width: 700,
            height: 700,
            top: '-20%',
            right: '-15%',
            background:
              'radial-gradient(circle, rgba(0,194,203,0.15) 0%, rgba(0,194,203,0.05) 40%, transparent 70%)',
            filter: 'blur(80px)',
          }}
          animate={{
            x: [0, 40, -30, 0],
            y: [0, -30, 40, 0],
            scale: [1, 1.05, 0.95, 1],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* Soft Violet/Blue blob — bottom left */}
        <motion.div
          className="absolute rounded-full"
          style={{
            width: 600,
            height: 600,
            bottom: '-15%',
            left: '-10%',
            background:
              'radial-gradient(circle, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.05) 40%, transparent 70%)',
            filter: 'blur(70px)',
          }}
          animate={{
            x: [0, -35, 25, 0],
            y: [0, 35, -20, 0],
            scale: [1, 0.95, 1.05, 1],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 4,
          }}
        />

        {/* Brand Accent blob — center */}
        <motion.div
          className="absolute rounded-full"
          style={{
            width: 400,
            height: 400,
            top: '40%',
            left: '30%',
            background:
              'radial-gradient(circle, rgba(14,165,233,0.1) 0%, transparent 60%)',
            filter: 'blur(60px)',
          }}
          animate={{
            x: [0, 50, -40, 0],
            y: [0, -40, 30, 0],
          }}
          transition={{
            duration: 22,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 8,
          }}
        />
      </div>

      {/* ── Floating particle field ────────────────────────────── */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {particles.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full"
            style={{
              width: p.size,
              height: p.size,
              left: `${p.x}%`,
              top: `${p.y}%`,
              background: p.id % 3 === 0
                ? 'rgba(0, 194, 203, 0.7)'
                : p.id % 3 === 1
                ? 'rgba(14, 165, 233, 0.6)'
                : 'rgba(148, 163, 184, 0.5)',
            }}
            animate={{
              y: [0, -40 - Math.random() * 50, 0],
              x: [0, (Math.random() - 0.5) * 40, 0],
              opacity: [p.opacity, p.opacity * 1.5, p.opacity],
            }}
            transition={{
              duration: p.duration,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: p.delay,
            }}
          />
        ))}
      </div>

      {/* ── Orbital ring ──────────────────────────────────────── */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <div
          className="auth-orbit-ring"
          style={{
            width: '800px',
            height: '800px',
            border: '1px solid rgba(0, 194, 203, 0.1)',
            boxShadow: '0 0 50px rgba(0,194,203,0.05), inset 0 0 50px rgba(0,194,203,0.03)',
          }}
        />
        <div
          className="auth-orbit-ring-2"
          style={{
            width: '550px',
            height: '550px',
            border: '1px solid rgba(99, 102, 241, 0.08)',
          }}
        />
      </div>

      {/* ── Subtle dot grid overlay ────────────────────────────── */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(rgba(148, 163, 184, 0.2) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
          maskImage: 'radial-gradient(ellipse at center, transparent 30%, black 80%)',
          WebkitMaskImage: 'radial-gradient(ellipse at center, transparent 30%, black 80%)',
        }}
      />

      {/* ── Page content ──────────────────────────────────────── */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        {children}
      </div>
    </div>
  );
}
