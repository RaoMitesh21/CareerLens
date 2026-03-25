/* ═══════════════════════════════════════════════════════════════════
   Demo Page — Public showcase of CareerLens analysis capabilities
   NO LOGIN REQUIRED — Displays sample Data Scientist analysis
   ═══════════════════════════════════════════════════════════════════ */

import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { LogoIcon } from '../components/Logo';

/* ═══════════════════════════════════════════════════════════════════
   DEMO DATA — Mitesh Rao × Data Scientist (sample analysis)
   ═══════════════════════════════════════════════════════════════════ */
const DEMO_DATA = {
  candidate: {
    name: 'Rao Mitesh',
    title: 'Data Science Student | ML Intern | Full-Stack Developer',
    education: 'B.Sc (IT) — Data Science, JG University — CGPA: 8.83/10.0',
    location: 'Ahmedabad, Gujarat, India',
    contact: { email: 'raomitesh12@gmail.com', phone: '+91 9924246809' },
    certifications: ['Legacy Responsive Web Design — freeCodeCamp', 'Rank 1 — Data Science Stream (Sem 1–3)', 'AI Hackathon — LJ University'],
    projects: [
      { name: 'CareerLens', tech: 'React, FastAPI, ESCO, MySQL', status: 'Ongoing' },
      { name: 'Talksy', tech: 'React, PHP, WebSocket (Ratchet)', status: 'Completed' },
      { name: 'ThunderCast', tech: 'Python, Machine Learning', status: 'Completed' },
      { name: 'Profit Paradox', tech: 'Python, XGBoost, Streamlit', status: 'Completed' },
    ],
    skills: {
      'Programming Languages': ['Python', 'JavaScript', 'Java', 'C++', 'C', 'SQL', 'PHP'],
      'Web Development': ['React.js', 'HTML', 'CSS', 'Responsive Web Design', 'WebSocket (Ratchet)', 'Streamlit'],
      'Data Science & ML': ['Machine Learning', 'Predictive Modeling', 'XGBoost', 'Random Forest', 'Scikit-learn', 'Clustering', 'Feature Engineering'],
      'Database': ['SQL (Intermediate)', 'Database Design & Management'],
      'Tools & Technologies': ['Git', 'Jupyter Notebook', 'VS Code', 'Cursor', 'AI Tools Integration'],
      'Concepts': ['Data Analysis', 'REST APIs', 'Authentication', 'Model Evaluation', 'Deployment'],
      'Soft Skills': ['Public Speaking', 'Leadership', 'Problem Solving', 'Team Collaboration', 'Quick Learner'],
    },
  },
  analysis: {
    role: 'data scientist',
    overall_score: 87.0,
    core_match: 85.0,
    secondary_match: 88.5,
    bonus_match: 89.2,
    matched_skills: [
      'statistics', 'data mining', 'online analytical processing',
      'execute analytical mathematical calculations',
      'business intelligence', 'unstructured data',
      'manage ICT data classification', 'manage ICT data architecture',
      'design database in the cloud', 'apply blended learning',
      'develop professional network with researchers and scientists',
      'communicate with a non-scientific audience',
      'increase the impact of science on policy and society',
      'visual presentation techniques', 'information extraction',
      'query languages', 'data models',
      'normalise data', 'manage research data',
      'use data processing techniques', 'interpret current data',
      'operate open source software', 'establish data processes',
      'perform scientific research', 'build recommender systems',
      'perform data cleansing', 'design database scheme',
      'implement data quality processes', 'collect ICT data',
      'deliver visual presentation of data', 'report analysis results',
      'perform project management', 'synthesise information',
      'develop data processing applications', 'use spreadsheets software',
      'integrate ICT data', 'define data quality criteria',
      'manage data', 'create data models',
    ],
    missing_skills: [
      'advanced statistical inference', 'time series forecasting advanced techniques',
    ],
    strengths: [
      'data mining', 'statistics', 'machine learning implementation',
      'online analytical processing', 'business intelligence',
      'execute analytical mathematical calculations',
      'manage ICT data classification',
      'design database in the cloud',
      'develop professional network with researchers and scientists',
      'communicate with a non-scientific audience',
      'visual presentation techniques',
      'report analysis results',
    ],
    improvement_priority: [
      { skill: 'advanced statistical inference', priority: 'Medium' },
      { skill: 'time series forecasting advanced techniques', priority: 'Medium' },
      { skill: 'deep learning frameworks optimization', priority: 'Low' },
      { skill: 'distributed computing at scale', priority: 'Low' },
    ],
    skill_confidence: [
      { skill: 'data mining', mentions: 12, in_project_context: true, confidence: 0.95 },
      { skill: 'statistics', mentions: 14, in_project_context: true, confidence: 0.94 },
      { skill: 'machine learning', mentions: 11, in_project_context: true, confidence: 0.92 },
      { skill: 'online analytical processing', mentions: 8, in_project_context: false, confidence: 0.88 },
      { skill: 'business intelligence', mentions: 9, in_project_context: false, confidence: 0.87 },
      { skill: 'data visualization', mentions: 7, in_project_context: true, confidence: 0.85 },
      { skill: 'database design', mentions: 6, in_project_context: true, confidence: 0.84 },
      { skill: 'SQL & querying', mentions: 10, in_project_context: true, confidence: 0.91 },
    ],
    analysis_summary: "Excellent match! You are a strong candidate for Data Scientist. Your skills in statistics, machine learning, and data analysis align very well with role requirements. Focus on the few remaining gaps to become a perfect fit.",
    meta: {
      total_required_skills: 54,
      core_skills_count: 54,
      secondary_skills_count: 12,
      bonus_skills_count: 8,
      total_matched: 50,
      total_missing: 2,
    },
  },
  roadmap: {
    level: 'advanced',
    title: 'Advanced Roadmap — Specialization & Leadership Path',
    summary: 'Your current score is 87.0%! You are a strong candidate. This roadmap focuses on advanced specialization, leadership development, and filling the small gaps to reach mastery.',
    phases: [
      {
        phase: 1,
        title: 'Advanced Specialization',
        duration: 'Weeks 1–4',
        focus_area: 'Deep expertise in specialized domains',
        skills_to_learn: ['advanced statistical inference', 'bayesian methods', 'causal inference', 'network analysis', 'advanced time series forecasting'],
        suggested_actions: [
          'Take advanced courses in statistical theory and methods',
          'Pursue certifications in specific data science domains',
          'Read research papers and implement novel algorithms',
          'Contribute to open-source ML/AI projects at leadership level',
        ],
      },
      {
        phase: 2,
        title: 'Production & Scale',
        duration: 'Weeks 5–8',
        focus_area: 'Enterprise-level deployment and optimization',
        skills_to_learn: ['distributed computing', 'ML ops & model deployment', 'model monitoring & governance', 'cost optimization', 'real-time analytics'],
        suggested_actions: [
          'Build production ML pipelines with monitoring',
          'Learn cloud platforms (AWS SageMaker, GCP Vertex)',
          'Implement MLOps best practices',
          'Mentor junior data scientists in your organization',
        ],
      },
      {
        phase: 3,
        title: 'Leadership & Innovation',
        duration: 'Weeks 9–12',
        focus_area: 'Technical leadership and innovation',
        skills_to_learn: ['strategic data initiatives', 'stakeholder management', 'emerging technologies', 'research publication', 'technical mentorship'],
        suggested_actions: [
          'Lead cross-functional data science projects',
          'Publish research or technical blog posts',
          'Present at conferences or webinars',
          'Develop strategies for AI/ML adoption in your organization',
        ],
      },
    ],
  },
};

/* ═══════════════════════════════════════════════════════════════════ */
/*  COMPONENTS                                                       */
/* ═══════════════════════════════════════════════════════════════════ */

function AnimatedScore({ value, duration = 1.5 }) {
  const [display, setDisplay] = useState(0);
  const raf = useRef(null);

  useEffect(() => {
    const end = value;
    const startTime = performance.now();
    function tick(now) {
      const p = Math.min((now - startTime) / 1000 / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(eased * end * 10) / 10);
      if (p < 1) raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [value, duration]);

  return <>{display.toFixed(1)}</>;
}

function ScoreRing({ score, size = 220 }) {
  const sw = 12;
  const r = (size - sw) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = score >= 70 ? '#22c55e' : score >= 40 ? '#00C2CB' : '#ef4444';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-surface-alt)" strokeWidth={sw} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={sw} strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.8, ease: [0.4, 0, 0.2, 1], delay: 0.3 }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-ink" style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: size * 0.2 }}>
          <AnimatedScore value={score} />%
        </span>
        <span className="text-xs text-ink-muted uppercase tracking-wider mt-1">Overall Match</span>
      </div>
    </div>
  );
}

function StatPill({ label, value, color = 'var(--color-ink)' }) {
  return (
    <div className="flex flex-col items-center px-4 py-2">
      <span className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color }}>{value}</span>
      <span className="text-xs text-ink-muted uppercase tracking-wider">{label}</span>
    </div>
  );
}

function SkillRadar({ corePct, secondaryPct, bonusPct }) {
  const data = [
    { category: 'Core Skills', value: corePct },
    { category: 'Secondary', value: secondaryPct },
    { category: 'Bonus Tools', value: bonusPct },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <PolarGrid stroke="var(--color-surface-alt)" />
        <PolarAngleAxis dataKey="category" tick={{ fontSize: 12, fill: 'var(--color-ink-muted)' }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--color-ink-muted)' }} />
        <Radar name="Match %" dataKey="value" stroke="#00C2CB" fill="#00C2CB" fillOpacity={0.35} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  MAIN DEMO PAGE                                                   */
/* ═══════════════════════════════════════════════════════════════════ */

export default function DemoPage() {
  const data = DEMO_DATA;
  const [showAllMissing, setShowAllMissing] = useState(false);

  const { analysis, roadmap, candidate } = data;
  const meta = analysis.meta || {};
  const matchedSkills = analysis.matched_skills || [];
  const missingSkills = analysis.missing_skills || [];
  const missingToShow = showAllMissing ? missingSkills : missingSkills.slice(0, 12);
  const improvementPriority = analysis.improvement_priority || [];

  return (
    <div className="min-h-screen pt-28 pb-20">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        <div className="absolute rounded-full blur-3xl opacity-12" style={{ width: 600, height: 600, top: '5%', right: '-8%', background: 'radial-gradient(circle, rgba(0,194,203,0.18) 0%, transparent 70%)' }} />
        <div className="absolute rounded-full blur-3xl opacity-8" style={{ width: 400, height: 400, bottom: '10%', left: '-5%', background: 'radial-gradient(circle, rgba(35,43,50,0.10) 0%, transparent 70%)' }} />
      </div>

      <div className="section-container relative" style={{ zIndex: 1 }}>

        {/* ═══ DEMO BANNER ════════════════════════════════════════ */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="glass-card p-6 mb-8 border-2 border-success/30 bg-success/5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#22c55e' }}>
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <div>
                <h2 className="text-lg font-semibold text-ink" style={{ fontFamily: 'var(--font-display)' }}>87% Match — Excellent Fit! 🎯</h2>
                <p className="text-xs text-ink-muted">Showcase demo: See what strong results look like after analysis</p>
              </div>
            </div>
            <Link to="/signup" className="btn-primary text-sm">Analyze Your Resume</Link>
          </div>
        </motion.div>

        {/* ═══ CANDIDATE PROFILE HEADER ═══════════════════════════ */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass-card p-6 md:p-8 mb-8"
        >
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold flex-shrink-0" style={{ fontFamily: 'var(--font-display)', background: 'rgba(0,194,203,0.10)', color: '#00C2CB' }}>
              RM
            </div>

            <div className="flex-1 min-w-0">
              <h1 className="text-ink tracking-tight" style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.25rem, 2.5vw, 1.75rem)' }}>
                {candidate?.name}
              </h1>
              {candidate.title && <p className="text-sm text-ink-secondary mt-0.5">{candidate.title}</p>}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1">
                {candidate.education && (
                  <p className="text-xs text-ink-muted flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                    {candidate.education}
                  </p>
                )}
                {candidate.location && (
                  <p className="text-xs text-ink-muted flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    {candidate.location}
                  </p>
                )}
              </div>
              {candidate.certifications && candidate.certifications.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {candidate.certifications.map((cert, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md bg-primary/6 text-primary text-xs font-medium">{cert}</span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <span className="text-xs text-ink-muted uppercase tracking-wider">Target Role</span>
              <span className="px-3 py-1 rounded-full bg-ink text-white text-sm font-semibold capitalize">{analysis.role}</span>
            </div>
          </div>

          {candidate?.projects && (
            <div className="mt-5 pt-5 border-t border-surface-alt/60">
              <span className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-2.5 block">Projects</span>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                {candidate.projects.map((proj, i) => (
                  <div key={i} className="flex flex-col p-3 rounded-xl bg-surface/60 border border-surface-alt/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-ink truncate" style={{ fontFamily: 'var(--font-display)' }}>{proj.name}</span>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded-md flex-shrink-0 ml-1 ${proj.status === 'Ongoing' ? 'bg-primary/10 text-primary' : 'bg-success/10 text-success'}`}>
                        {proj.status === 'Ongoing' ? '● Live' : '✓ Done'}
                      </span>
                    </div>
                    <span className="text-xs text-ink-muted">{proj.tech}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* ═══ STATS BAR ═════════════════════════════════════════ */}
        <motion.div
          className="glass-card p-4 mb-8 flex items-center justify-around flex-wrap gap-2"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.5 }}
        >
          <StatPill label="Required" value={meta.total_required_skills || '—'} />
          <div className="w-px h-8 bg-surface-alt" />
          <StatPill label="Matched" value={meta.total_matched || matchedSkills.length} color="#00C2CB" />
          <div className="w-px h-8 bg-surface-alt" />
          <StatPill label="Missing" value={meta.total_missing || missingSkills.length} color="var(--color-danger)" />
          <div className="w-px h-8 bg-surface-alt" />
          <StatPill label="Core Skills" value={meta.core_skills_count || '—'} color="#232B32" />
        </motion.div>

        {/* ═══ SCORE + RADAR ════════════════════════════════════ */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          <motion.div
            className="glass-card p-8 flex flex-col items-center justify-center lg:col-span-1"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            <ScoreRing score={analysis.overall_score} />
            <div className="flex items-center gap-6 mt-6 text-center">
              {[
                { label: 'Core', value: analysis.core_match, color: '#00C2CB' },
                { label: 'Secondary', value: analysis.secondary_match, color: '#22c55e' },
                { label: 'Bonus', value: analysis.bonus_match, color: '#f59e0b' },
              ].map((tier, i) => (
                <div key={i} className="flex flex-col items-center">
                  <span className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: tier.color }}>{tier.value}%</span>
                  <span className="text-xs text-ink-muted uppercase tracking-wider">{tier.label}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="glass-card p-6 flex flex-col items-center lg:col-span-1"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.25, duration: 0.6 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-4">Skill Distribution</h3>
            <SkillRadar corePct={analysis.core_match} secondaryPct={analysis.secondary_match} bonusPct={analysis.bonus_match} />
          </motion.div>

          <motion.div
            className="glass-card p-8 lg:col-span-1"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">Top Matches</h3>
            <div className="space-y-2">
              {[
                { skill: 'data mining', conf: 95 },
                { skill: 'statistics', conf: 94 },
                { skill: 'machine learning', conf: 92 },
                { skill: 'SQL & querying', conf: 91 },
                { skill: 'online analytical processing', conf: 88 },
              ].map((item, i) => (
                <div key={i} className="text-xs text-ink-secondary flex items-center justify-between">
                  <span className="truncate">{item.skill}</span>
                  <span className="text-primary font-semibold">{item.conf}%</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* ═══ SKILLS FROM RESUME ════════════════════════════════ */}
        {candidate?.skills && (
          <motion.div
            className="glass-card p-8 mb-8"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.35, duration: 0.6 }}
          >
            <div className="mb-8">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-ink-muted mb-2">Expertise Profile</h3>
              <h2 className="text-2xl font-bold text-ink" style={{ fontFamily: 'var(--font-display)' }}>Technical Skills & Expertise</h2>
              <p className="text-xs text-ink-muted mt-2">Verified skills extracted from resume with proficiency assessment</p>
            </div>

            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
              {/* Data Science & ML */}
              <motion.div
                className="group relative overflow-hidden rounded-2xl p-6 border-2 transition-all hover:border-cyan-500/50"
                style={{ background: 'rgba(34, 197, 94, 0.08)', borderColor: 'rgba(34, 197, 94, 0.25)' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20" style={{ background: 'rgba(34, 197, 94, 0.4)' }} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' }}>
                      📊
                    </div>
                    <div>
                      <h4 className="font-semibold text-ink" style={{ color: '#22c55e' }}>Data Science & ML</h4>
                      <span className="text-xs text-ink-muted">Expert</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {candidate.skills['Data Science & ML'].map((skill, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-xs font-medium text-ink">{skill}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-surface-alt overflow-hidden">
                          <motion.div
                            className="h-full rounded-full"
                            style={{ background: '#22c55e' }}
                            initial={{ width: 0 }}
                            animate={{ width: `${85 + Math.random() * 15}%` }}
                            transition={{ delay: 0.5 + i * 0.05, duration: 1 }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Programming Languages */}
              <motion.div
                className="group relative overflow-hidden rounded-2xl p-6 border-2 transition-all hover:border-primary/50"
                style={{ background: 'rgba(0, 194, 203, 0.08)', borderColor: 'rgba(0, 194, 203, 0.25)' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.45 }}
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20" style={{ background: 'rgba(0, 194, 203, 0.4)' }} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0, 194, 203, 0.15)', color: '#00C2CB' }}>
                      ◈
                    </div>
                    <div>
                      <h4 className="font-semibold text-ink" style={{ color: '#00C2CB' }}>Programming</h4>
                      <span className="text-xs text-ink-muted">Proficient</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills['Programming Languages'].map((skill, i) => (
                      <span key={i} className="px-3 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(0, 194, 203, 0.15)', color: '#00C2CB', border: '1px solid rgba(0, 194, 203, 0.3)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Web Development */}
              <motion.div
                className="group relative overflow-hidden rounded-2xl p-6 border-2 transition-all hover:border-violet-500/50"
                style={{ background: 'rgba(139, 92, 246, 0.08)', borderColor: 'rgba(139, 92, 246, 0.25)' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20" style={{ background: 'rgba(139, 92, 246, 0.4)' }} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8B5CF6' }}>
                      ◐
                    </div>
                    <div>
                      <h4 className="font-semibold text-ink" style={{ color: '#8B5CF6' }}>Web Development</h4>
                      <span className="text-xs text-ink-muted">Advanced</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills['Web Development'].map((skill, i) => (
                      <span key={i} className="px-3 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8B5CF6', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Database & Tools */}
              <motion.div
                className="group relative overflow-hidden rounded-2xl p-6 border-2 transition-all hover:border-orange-500/50"
                style={{ background: 'rgba(249, 115, 22, 0.08)', borderColor: 'rgba(249, 115, 22, 0.25)' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.55 }}
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20" style={{ background: 'rgba(249, 115, 22, 0.4)' }} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(249, 115, 22, 0.15)', color: '#F97316' }}>
                      ◈
                    </div>
                    <div>
                      <h4 className="font-semibold text-ink" style={{ color: '#F97316' }}>Database & Tools</h4>
                      <span className="text-xs text-ink-muted">Proficient</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {[...candidate.skills['Database'], ...candidate.skills['Tools & Technologies'].slice(0, 4)].map((skill, i) => (
                      <div key={i} className="text-xs text-ink flex items-center gap-2">
                        <span style={{ color: '#F97316' }}>▸</span>
                        {skill}
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Concepts & Frameworks */}
              <motion.div
                className="group relative overflow-hidden rounded-2xl p-6 border-2 transition-all hover:border-pink-500/50"
                style={{ background: 'rgba(236, 72, 153, 0.08)', borderColor: 'rgba(236, 72, 153, 0.25)' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.6 }}
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20" style={{ background: 'rgba(236, 72, 153, 0.4)' }} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#EC4899' }}>
                      ◉
                    </div>
                    <div>
                      <h4 className="font-semibold text-ink" style={{ color: '#EC4899' }}>Core Concepts</h4>
                      <span className="text-xs text-ink-muted">Strong</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills['Concepts'].map((skill, i) => (
                      <span key={i} className="px-3 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#EC4899', border: '1px solid rgba(236, 72, 153, 0.3)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Soft Skills */}
              <motion.div
                className="group relative overflow-hidden rounded-2xl p-6 border-2 transition-all hover:border-green-500/50"
                style={{ background: 'rgba(34, 197, 94, 0.08)', borderColor: 'rgba(34, 197, 94, 0.25)' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.65 }}
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20" style={{ background: 'rgba(34, 197, 94, 0.4)' }} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' }}>
                      ★
                    </div>
                    <div>
                      <h4 className="font-semibold text-ink" style={{ color: '#22c55e' }}>Soft Skills</h4>
                      <span className="text-xs text-ink-muted">Outstanding</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills['Soft Skills'].map((skill, i) => (
                      <span key={i} className="px-3 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e', border: '1px solid rgba(34, 197, 94, 0.3)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Summary Stats */}
            <div className="mt-8 pt-8 border-t border-surface-alt/50">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 rounded-xl bg-surface/50">
                  <div className="text-2xl font-bold text-ink" style={{ fontFamily: 'var(--font-display)', color: '#22c55e' }}>50+</div>
                  <div className="text-xs text-ink-muted uppercase tracking-wider mt-1">Total Skills</div>
                </div>
                <div className="text-center p-4 rounded-xl bg-surface/50">
                  <div className="text-2xl font-bold text-ink" style={{ fontFamily: 'var(--font-display)', color: '#00C2CB' }}>6</div>
                  <div className="text-xs text-ink-muted uppercase tracking-wider mt-1">Categories</div>
                </div>
                <div className="text-center p-4 rounded-xl bg-surface/50">
                  <div className="text-2xl font-bold text-ink" style={{ fontFamily: 'var(--font-display)', color: '#8B5CF6' }}>Expert</div>
                  <div className="text-xs text-ink-muted uppercase tracking-wider mt-1">Level</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* ═══ SKILL GAP ANALYSIS ════════════════════════════════ */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          <motion.div
            className="glass-card p-8"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#22c55e' }}>✓ Matched Skills</h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold" style={{ background: 'rgba(34,197,94,0.10)', color: '#22c55e' }}>{matchedSkills.length}</span>
            </div>
            <p className="text-xs text-ink-muted mb-4">Outstanding! Your resume aligns perfectly with Data Scientist requirements.</p>
            <div className="flex flex-wrap gap-2">
              {matchedSkills.slice(0, 30).map((skill, i) => (
                <motion.span key={i} className="px-2.5 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(34,197,94,0.12)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.25)' }} initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.5 + i * 0.015 }}>
                  {skill}
                </motion.span>
              ))}
            </div>
            {matchedSkills.length > 30 && (
              <p className="text-xs text-ink-muted mt-3">+ {matchedSkills.length - 30} more matched skills ✓</p>
            )}
          </motion.div>

          <motion.div
            className="glass-card p-8"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.45, duration: 0.6 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#f59e0b' }}>✦ Minor Gaps</h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold" style={{ background: 'rgba(245,158,11,0.10)', color: '#f59e0b' }}>{missingSkills.length}</span>
            </div>
            <p className="text-xs text-ink-muted mb-4">Just a couple of advanced skills to master for perfection.</p>
            <div className="flex flex-wrap gap-2">
              {missingToShow.map((skill, i) => (
                <motion.span key={i} className="px-2.5 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.25)' }} initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.55 + i * 0.02 }}>
                  {skill}
                </motion.span>
              ))}
            </div>
          </motion.div>
        </div>

        {/* ═══ IMPROVEMENT PRIORITIES ════════════════════════════ */}
        <motion.div
          className="glass-card p-8 mb-8"
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">Optional Enhancements</h3>
          <div className="grid md:grid-cols-2 gap-3">
            {improvementPriority.map((item, i) => (
              <motion.div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-surface/60" initial={{ x: -15, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.55 + i * 0.04 }}>
                <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${item.priority === 'High' ? 'bg-danger' : item.priority === 'Medium' ? 'bg-warning' : 'bg-ink-muted'}`} />
                <span className="text-sm text-ink flex-1">{item.skill}</span>
                <span className={`text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md ${item.priority === 'High' ? 'text-danger bg-danger/8' : item.priority === 'Medium' ? 'text-warning bg-warning/8' : 'text-ink-muted bg-surface-alt'}`}>
                  {item.priority}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* ═══ SUMMARY + CTA ════════════════════════════════════ */}
        <motion.div className="mt-10 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>
          <div className="glass-card p-6 inline-block max-w-2xl mx-auto mb-6 border-2 border-success/20 bg-success/5">
            <div className="flex items-center justify-center mb-3">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#22c55e' }}>
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <p className="text-sm text-ink leading-relaxed font-semibold" style={{ fontFamily: 'var(--font-display)' }}>Excellent match! You are a strong candidate for Data Scientist. Your skills in statistics, machine learning, and data analysis align very well with role requirements.</p>
          </div>
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <Link to="/signup" className="btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
              Get Your Analysis Now
            </Link>
            <Link to="/" className="btn-secondary">Back to Home</Link>
          </div>
        </motion.div>
      </div>

      <div className="noise-overlay" />
    </div>
  );
}
