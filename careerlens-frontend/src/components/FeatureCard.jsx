/* ═══════════════════════════════════════════════════════════════════
   FeatureCard — Glass card for the feature panels
   ═══════════════════════════════════════════════════════════════════ */

import { motion } from 'framer-motion';

export default function FeatureCard({ icon, title, description, delay = 0 }) {
  return (
    <motion.div
      className="glass-card p-8 flex flex-col gap-4"
      initial={{ y: 40, opacity: 0 }}
      whileInView={{ y: 0, opacity: 1 }}
      whileHover={{ y: -4, scale: 1.02 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ delay, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
    >
      {/* Icon */}
      <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'rgba(0,194,203,0.10)', color: '#00C2CB' }}>
        {icon}
      </div>

      {/* Title */}
      <h3
        className="text-lg text-ink tracking-tight"
        style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
      >
        {title}
      </h3>

      {/* Description */}
      <p className="text-sm text-ink-secondary leading-relaxed">
        {description}
      </p>
    </motion.div>
  );
}
