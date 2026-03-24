/* ═══════════════════════════════════════════════════════════════════
   Results Page — Premium Score Dashboard + Gaps + Roadmap
   PROTECTED ROUTE — Login required to view your analysis results
   ═══════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════ */
/*  COMPONENTS                                                       */
/* ═══════════════════════════════════════════════════════════════════ */

/* ── Animated Counter ─────────────────────────────────────────────── */
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

/* ── Score Ring (SVG) ─────────────────────────────────────────────── */
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

/* ── Confidence Bar ───────────────────────────────────────────────── */
function ConfidenceBar({ skill, confidence, mentions, delay = 0 }) {
  const pct = Math.round(confidence * 100);
  return (
    <motion.div
      className="flex items-center gap-3"
      initial={{ x: -10, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay }}
    >
      <span className="text-xs text-ink w-44 truncate" title={skill}>{skill}</span>
      <div className="flex-1 h-2 rounded-full bg-surface-alt overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: pct >= 60 ? '#22c55e' : pct >= 35 ? '#00C2CB' : '#f59e0b' }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, delay: delay + 0.2, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
      <span className="text-xs text-ink-muted w-10 text-right">{pct}%</span>
      <span className="text-xs text-ink-muted w-16 text-right">{mentions} hits</span>
    </motion.div>
  );
}

/* ── Stat Pill ────────────────────────────────────────────────────── */
function StatPill({ label, value, color = 'var(--color-ink)' }) {
  return (
    <div className="flex flex-col items-center px-4 py-2">
      <span className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color }}>{value}</span>
      <span className="text-xs text-ink-muted uppercase tracking-wider">{label}</span>
    </div>
  );
}

/* ── Radar Chart Viz ──────────────────────────────────────────────── */
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
/*  MAIN PAGE                                                        */
/* ═══════════════════════════════════════════════════════════════════ */

export default function ResultsPage() {
  const { mode } = useParams();
  const [data, setData] = useState(null);
  const [showAllMissing, setShowAllMissing] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem('analysisResult');
    if (stored) setData(JSON.parse(stored));
  }, [mode]);

  /* ── Empty state ────────────────────────────────────────────────── */
  if (!data) {
    return (
      <div className="min-h-screen pt-32 text-center">
        <div className="section-container flex flex-col items-center">
          <LogoIcon size={56} />
          <h2 className="text-xl text-ink mb-4 mt-5" style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}>No analysis results yet</h2>
          <p className="text-ink-secondary mb-6">Upload your resume to get a detailed skill analysis and personalized roadmap.</p>
          <div className="flex items-center justify-center gap-4">
            <Link to="/student/analyzer" className="btn-primary">Upload Resume</Link>
            <Link to="/demo" className="btn-secondary">View Demo First</Link>
          </div>
        </div>
      </div>
    );
  }

  const { analysis, roadmap, candidate } = data;
  const meta = analysis.meta || {};
  const matchedSkills = analysis.matched_skills || [];
  const missingSkills = analysis.missing_skills || [];
  const missingToShow = showAllMissing ? missingSkills : missingSkills.slice(0, 12);
  const improvementPriority = analysis.improvement_priority || [];
  const skillConfidence = analysis.skill_confidence || [];

  return (
    <div className="min-h-screen pt-28 pb-20">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        <div className="absolute rounded-full blur-3xl opacity-12" style={{ width: 600, height: 600, top: '5%', right: '-8%', background: 'radial-gradient(circle, rgba(0,194,203,0.18) 0%, transparent 70%)' }} />
        <div className="absolute rounded-full blur-3xl opacity-8" style={{ width: 400, height: 400, bottom: '10%', left: '-5%', background: 'radial-gradient(circle, rgba(35,43,50,0.10) 0%, transparent 70%)' }} />
      </div>

      <div className="section-container relative" style={{ zIndex: 1 }}>

        {/* ═══ CANDIDATE PROFILE HEADER ═══════════════════════════ */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="glass-card p-6 md:p-8 mb-8"
        >
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold flex-shrink-0" style={{ fontFamily: 'var(--font-display)', background: 'rgba(0,194,203,0.10)', color: '#00C2CB' }}>
              {candidate?.name
                ? candidate.name.split(' ').map(n => n[0]).join('')
                : <LogoIcon size={36} />}
            </div>

            <div className="flex-1 min-w-0">
              {candidate?.name ? (
                <>
                  <h1 className="text-ink tracking-tight" style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.25rem, 2.5vw, 1.75rem)' }}>
                    {candidate.name}
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
                    {candidate.contact?.email && (
                      <p className="text-xs text-ink-muted flex items-center gap-1">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                        {candidate.contact.email}
                      </p>
                    )}
                  </div>
                  {/* Certifications */}
                  {candidate.certifications && candidate.certifications.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {candidate.certifications.map((cert, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-md bg-primary/6 text-primary text-xs font-medium">{cert}</span>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <>
                  <span className="text-xs font-semibold uppercase tracking-widest text-primary">Analysis Results</span>
                  <h1 className="text-ink mt-1 tracking-tight capitalize" style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.25rem, 2.5vw, 1.75rem)' }}>
                    {analysis.role}
                  </h1>
                </>
              )}
            </div>

            {/* Target role badge */}
            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <span className="text-xs text-ink-muted uppercase tracking-wider">Target Role</span>
              <span className="px-3 py-1 rounded-full bg-ink text-white text-sm font-semibold capitalize">{analysis.role}</span>
            </div>
          </div>

          {/* ── Projects row (if candidate has projects) ────────── */}
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
          transition={{ delay: 0.08, duration: 0.5 }}
        >
          <StatPill label="Required" value={meta.total_required_skills || '—'} />
          <div className="w-px h-8 bg-surface-alt" />
          <StatPill label="Matched" value={meta.total_matched || matchedSkills.length} color="#00C2CB" />
          <div className="w-px h-8 bg-surface-alt" />
          <StatPill label="Missing" value={meta.total_missing || missingSkills.length} color="var(--color-danger)" />
          <div className="w-px h-8 bg-surface-alt" />
          <StatPill label="Core Skills" value={meta.core_skills_count || '—'} color="#232B32" />
        </motion.div>

        {/* ═══ SCORE + TIER BREAKDOWN + RADAR ════════════════════════════ */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Score Card */}
          <motion.div
            className="glass-card p-8 flex flex-col items-center justify-center lg:col-span-1"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1, duration: 0.6 }}
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

          {/* Skill Radar Chart */}
          <motion.div
            className="glass-card p-6 flex flex-col items-center lg:col-span-1"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.15, duration: 0.6 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-4">Skill Distribution</h3>
            <SkillRadar corePct={analysis.core_match} secondaryPct={analysis.secondary_match} bonusPct={analysis.bonus_match} />
          </motion.div>

          {/* Skill Confidence Panel */}
          <motion.div
            className="glass-card p-8 lg:col-span-1"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2, duration: 0.6 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">
              <span className="inline-flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                Top Matches
              </span>
            </h3>
            {skillConfidence.length > 0 ? (
              <div className="space-y-2">
                {skillConfidence.slice(0, 5).map((item, i) => (
                  <div key={i} className="text-xs text-ink-secondary flex items-center justify-between">
                    <span className="truncate">{item.skill}</span>
                    <span className="text-primary font-semibold"> {Math.round(item.confidence * 100)}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-ink-muted">No matches found.</p>
            )}
          </motion.div>
        </div>

        {/* OLD: Skill Confidence Panel (removed in favor of radar layout) */}
        {false && (
        <motion.div
            className="glass-card p-8 lg:col-span-2"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2, duration: 0.6 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">
              <span className="inline-flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                Skill Confidence — How strongly each skill was detected
              </span>
            </h3>
            {skillConfidence.length > 0 ? (
              <div className="space-y-3">
                {skillConfidence.map((item, i) => (
                  <ConfidenceBar key={i} skill={item.skill} confidence={item.confidence} mentions={item.mentions} delay={0.3 + i * 0.06} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-ink-muted">No confidence data available.</p>
            )}
          </motion.div>
        )}
        

        {/* ═══ YOUR TECHNICAL SKILLS (from CV) ═══════════════════ */}
        {candidate?.skills && (
          <motion.div
            className="glass-card p-8 mb-8"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.22, duration: 0.6 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">
              <span className="inline-flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                Your Technical Skills — Extracted from Resume
              </span>
            </h3>
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
              {Object.entries(candidate.skills).map(([category, skills], ci) => {
                const categoryColors = [
                  { bg: 'bg-primary/6', text: 'text-primary', border: 'border-primary/12', dot: 'bg-primary' },
                  { bg: 'bg-success/6', text: 'text-success', border: 'border-success/12', dot: 'bg-success' },
                  { bg: 'bg-warning/6', text: 'text-warning', border: 'border-warning/12', dot: 'bg-warning' },
                  { bg: 'bg-danger/6', text: 'text-danger', border: 'border-danger/12', dot: 'bg-danger' },
                  { bg: 'bg-violet-500/6', text: 'text-violet-600', border: 'border-violet-500/12', dot: 'bg-violet-500' },
                  { bg: 'bg-cyan-500/6', text: 'text-cyan-600', border: 'border-cyan-500/12', dot: 'bg-cyan-500' },
                  { bg: 'bg-pink-500/6', text: 'text-pink-600', border: 'border-pink-500/12', dot: 'bg-pink-500' },
                ];
                const c = categoryColors[ci % categoryColors.length];
                return (
                  <motion.div
                    key={category}
                    className="p-4 rounded-xl bg-surface/50 border border-surface-alt/50"
                    initial={{ y: 15, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.3 + ci * 0.06 }}
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${c.dot}`} />
                      <span className="text-xs font-semibold uppercase tracking-wider text-ink-secondary">{category}</span>
                      <span className="text-xs text-ink-muted ml-auto">{skills.length}</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {skills.map((skill, si) => (
                        <span key={si} className={`px-2 py-0.5 rounded-md text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ═══ SKILL TIER RADAR CHART ══════════════════════════ */}
        <motion.div
          className="glass-card p-8 mb-8"
          initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.34, duration: 0.6 }}
        >
          <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">
            <span className="inline-flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v10M7 12h10" /></svg>
              Skill Coverage by Tier
            </span>
          </h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={[
                { tier: 'Core', score: analysis.core_match, fullMark: 100 },
                { tier: 'Secondary', score: analysis.secondary_match, fullMark: 100 },
                { tier: 'Bonus', score: analysis.bonus_match, fullMark: 100 },
              ]}>
                <PolarGrid stroke="var(--color-surface-alt)" />
                <PolarAngleAxis dataKey="tier" stroke="var(--color-ink-muted)" style={{ fontSize: '12px' }} />
                <PolarRadiusAxis stroke="var(--color-surface-alt)" style={{ fontSize: '11px' }} angle={90} domain={[0, 100]} />
                <Radar name="Coverage %" dataKey="score" stroke="#00C2CB" fill="#00C2CB" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* ═══ ESCO SKILL GAP ANALYSIS ══════════════════════════ */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Matched Skills */}
          <motion.div
            className="glass-card p-8"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.28, duration: 0.6 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#00C2CB' }}>
                <span className="inline-flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  Matched Skills
                </span>
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold" style={{ background: 'rgba(0,194,203,0.10)', color: '#00C2CB' }}>{matchedSkills.length}</span>
            </div>
            <p className="text-xs text-ink-muted mb-4">ESCO-mapped skills from your resume that match the target role requirements.</p>
            <div className="flex flex-wrap gap-2">
              {matchedSkills.map((skill, i) => (
                <motion.span key={i} className="tag-matched" initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.4 + i * 0.025 }}>
                  {skill}
                </motion.span>
              ))}
            </div>
          </motion.div>

          {/* Missing Skills */}
          <motion.div
            className="glass-card p-8"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.32, duration: 0.6 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#232B32' }}>
                <span className="inline-flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                  Missing Skills
                </span>
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold" style={{ background: 'rgba(239,68,68,0.10)', color: '#ef4444' }}>{missingSkills.length}</span>
            </div>
            <p className="text-xs text-ink-muted mb-4">Skills required for this role that were not detected in your resume. Focus on high-priority ones first.</p>
            <div className="flex flex-wrap gap-2">
              {missingToShow.map((skill, i) => (
                <motion.span key={i} className="tag-missing" initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.5 + i * 0.02 }}>
                  {skill}
                </motion.span>
              ))}
            </div>
            {missingSkills.length > 12 && (
              <button onClick={() => setShowAllMissing(!showAllMissing)} className="mt-4 text-xs text-primary font-medium hover:underline flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {showAllMissing
                    ? <><polyline points="18 15 12 9 6 15" /></>
                    : <><polyline points="6 9 12 15 18 9" /></>
                  }
                </svg>
                {showAllMissing ? 'Show less' : `Show all ${missingSkills.length} missing skills`}
              </button>
            )}
          </motion.div>
        </div>

        {/* ═══ IMPROVEMENT PRIORITIES ════════════════════════════ */}
        <motion.div
          className="glass-card p-8 mb-8"
          initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }}
        >
          <h3 className="text-xs font-semibold uppercase tracking-widest text-ink-muted mb-5">
            <span className="inline-flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" /></svg>
              Improvement Priorities
            </span>
          </h3>
          <div className="grid md:grid-cols-2 gap-3">
            {improvementPriority.map((item, i) => (
              <motion.div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-surface/60" initial={{ x: -15, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.4 + i * 0.04 }}>
                <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${item.priority === 'High' ? 'bg-danger' : item.priority === 'Medium' ? 'bg-warning' : 'bg-ink-muted'}`} />
                <span className="text-sm text-ink flex-1">{item.skill}</span>
                <span className={`text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md ${item.priority === 'High' ? 'text-danger bg-danger/8' : item.priority === 'Medium' ? 'text-warning bg-warning/8' : 'text-ink-muted bg-surface-alt'}`}>
                  {item.priority}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* ═══ LEARNING ROADMAP ══════════════════════════════════ */}
        {roadmap && (
          <motion.div
            className="glass-card p-8"
            initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4, duration: 0.6 }}
          >
            {/* Roadmap header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${roadmap.level === 'beginner' ? 'bg-danger/10 text-danger' : roadmap.level === 'intermediate' ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'}`}>
                    {roadmap.level}
                  </span>
                  <span className="text-xs font-semibold uppercase tracking-widest text-ink-muted">Learning Roadmap</span>
                </div>
                <h2 className="text-ink tracking-tight" style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.25rem' }}>
                  {roadmap.title}
                </h2>
              </div>
              <div className="hidden md:flex items-center gap-1 text-xs text-ink-muted">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                {roadmap.phases.length * 4} weeks total
              </div>
            </div>
            <p className="text-sm text-ink-secondary mb-8">{roadmap.summary}</p>

            {/* Phase cards */}
            <div className="relative pl-8">
              <div className="absolute left-3 top-2 bottom-2 w-px bg-surface-alt" />
              {roadmap.phases.map((phase, i) => (
                <motion.div key={i} className="relative mb-10 last:mb-0" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.6 + i * 0.15, duration: 0.5 }}>
                  {/* Node */}
                  <div className={`absolute -left-5 top-1 w-5 h-5 rounded-full border-2 border-surface flex items-center justify-center`} style={{ background: i === 0 ? '#00C2CB' : 'var(--color-surface-alt)' }}>
                    <span className="text-xs font-bold" style={{ color: i === 0 ? 'white' : 'var(--color-ink-muted)', fontSize: '0.6rem' }}>{phase.phase}</span>
                  </div>

                  <div className="bg-surface/60 rounded-xl p-5 border border-surface-alt/50">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#00C2CB' }}>Phase {phase.phase}</span>
                        <span className="px-2 py-0.5 rounded-md bg-surface-alt text-xs text-ink-muted">{phase.duration}</span>
                      </div>
                      <span className="text-xs text-ink-muted italic">{phase.focus_area}</span>
                    </div>

                    <h4 className="text-ink mb-3 tracking-tight" style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}>
                      {phase.title}
                    </h4>

                    {/* Skills to learn */}
                    <div className="mb-3">
                      <span className="text-xs text-ink-muted uppercase tracking-wider">Skills to learn:</span>
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        {phase.skills_to_learn.map((skill, j) => (
                          <span key={j} className="px-2.5 py-1 rounded-lg text-xs font-medium" style={{ background: 'rgba(0,194,203,0.08)', color: '#00C2CB', border: '1px solid rgba(0,194,203,0.15)' }}>{skill}</span>
                        ))}
                      </div>
                    </div>

                    {/* Actions */}
                    <div>
                      <span className="text-xs text-ink-muted uppercase tracking-wider">Actions:</span>
                      <ul className="mt-1.5 space-y-1.5">
                        {phase.suggested_actions.map((action, j) => (
                          <li key={j} className="text-xs text-ink-secondary flex items-start gap-2">
                            <span className="w-4 h-4 rounded-full bg-surface-alt flex items-center justify-center flex-shrink-0 mt-0.5 text-xs" style={{ color: '#00C2CB' }}>
                              {j + 1}
                            </span>
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* ═══ SUMMARY + CTA ════════════════════════════════════ */}
        <motion.div className="mt-10 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }}>
          <div className="glass-card p-6 inline-block max-w-2xl mx-auto mb-6">
            <p className="text-sm text-ink leading-relaxed">{analysis.analysis_summary}</p>
          </div>
          <div className="flex items-center justify-center gap-4">
            <Link to="/student/analyzer" className="btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
              Analyze Another Resume
            </Link>
          </div>
        </motion.div>
      </div>

      <div className="noise-overlay" />
    </div>
  );
}
