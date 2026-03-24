import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  batchAnalyzeResumes,
  getDashboardState,
  parseFileToText,
  saveDashboardState,
  searchOccupations,
} from '../services/api';
import { parseResumeText } from '../services/resumeParser';
import { LogoIcon } from '../components/Logo';

const DEMO_CANDIDATES = [
  {
    id: 1,
    candidate_name: 'Aisha Khan',
    overall_score: 88.2,
    decision_score: 89.4,
    core_match: 90.0,
    secondary_match: 84.5,
    bonus_match: 82.4,
    matched_count: 42,
    missing_count: 7,
    skill_coverage_ratio: 85.7,
    match_label: 'Excellent',
    risk_level: 'Low',
    recommendation: 'Strong Shortlist',
    top_strengths: ['Python', 'Docker', 'SQL', 'FastAPI'],
    top_gaps: ['Kubernetes'],
  },
  {
    id: 2,
    candidate_name: 'Liam Chen',
    overall_score: 76.5,
    decision_score: 74.3,
    core_match: 72.1,
    secondary_match: 79.4,
    bonus_match: 70.4,
    matched_count: 36,
    missing_count: 12,
    skill_coverage_ratio: 75.0,
    match_label: 'Good',
    risk_level: 'Medium',
    recommendation: 'Shortlist',
    top_strengths: ['React', 'TypeScript', 'Node.js'],
    top_gaps: ['System design'],
  },
  {
    id: 3,
    candidate_name: 'Mateo Silva',
    overall_score: 62.4,
    decision_score: 58.1,
    core_match: 55.0,
    secondary_match: 67.5,
    bonus_match: 64.2,
    matched_count: 30,
    missing_count: 18,
    skill_coverage_ratio: 62.5,
    match_label: 'Fair',
    risk_level: 'Medium',
    recommendation: 'Review',
    top_strengths: ['Java', 'Spring', 'SQL'],
    top_gaps: ['API security'],
  },
  {
    id: 4,
    candidate_name: 'Priya Patel',
    overall_score: 54.1,
    decision_score: 44.9,
    core_match: 48.2,
    secondary_match: 59.1,
    bonus_match: 53.7,
    matched_count: 22,
    missing_count: 25,
    skill_coverage_ratio: 46.8,
    match_label: 'Weak',
    risk_level: 'High',
    recommendation: 'Hold',
    top_strengths: ['Kubernetes', 'Ansible', 'CI/CD'],
    top_gaps: ['Backend architecture'],
  },
];

const RECRUITER_DASHBOARD_STORAGE_KEY = 'careerlens_recruiter_dashboard_v1';
const ANALYSIS_MODE_OPTIONS = [
  { id: 'esco', label: 'ESCO' },
  { id: 'hybrid', label: 'Hybrid' },
];

const formatPct = (value) => `${Number(value || 0).toFixed(1)}%`;

const scoreColor = (score) => {
  if (score >= 80) {
    return '#22c55e';
  }
  if (score >= 60) {
    return '#00C2CB';
  }
  return '#f59e0b';
};

const riskClass = (risk) => {
  if (risk === 'Low') {
    return 'bg-emerald-100 text-emerald-700 border-emerald-200';
  }
  if (risk === 'Medium') {
    return 'bg-amber-100 text-amber-700 border-amber-200';
  }
  return 'bg-red-100 text-red-700 border-red-200';
};

const escapeCsvCell = (value) => {
  const text = String(value ?? '');
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
};

const buildInterviewQuestions = (candidate, role) => {
  const name = candidate?.candidate_name || candidate?.name || 'Candidate';
  const target = role || 'this role';
  const strengths = candidate?.top_strengths || [];
  const gaps = candidate?.top_gaps || [];
  const primaryGap = gaps[0] || 'one critical missing skill';
  const secondaryGap = gaps[1] || 'architecture and scale decisions';
  const primaryStrength = strengths[0] || 'your strongest technical area';

  return [
    `Walk me through a project where you applied ${primaryStrength} for ${target}, and what measurable outcome you delivered.`,
    `How would you close the gap in ${primaryGap} within your first 30 days in this role?`,
    `Describe a technical trade-off you made related to ${secondaryGap}. What options did you evaluate and why?`,
    `If production performance degrades for a core workflow, what is your triage and recovery approach?`,
    `What would your 60-day plan look like to become fully productive as ${target}?`,
  ].map((question, idx) => ({
    id: `${name}-q-${idx + 1}`,
    text: question,
  }));
};

function MetricBar({ label, value, color }) {
  const pct = Math.max(0, Math.min(100, Number(value || 0)));

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-ink-muted">{label}</span>
        <span className="font-semibold text-ink">{formatPct(pct)}</span>
      </div>
      <div className="h-2 rounded-full bg-surface-alt/70 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6 }}
          className="h-full"
          style={{ background: color }}
        />
      </div>
    </div>
  );
}

function CandidateCard({ candidate, index, shortlisted, onToggleShortlist }) {
  const decision = Number(candidate.decision_score ?? candidate.overall_score ?? 0);
  const name = candidate.candidate_name || candidate.name || 'Unknown Candidate';
  const strengths = candidate.top_strengths || [];
  const gaps = candidate.top_gaps || [];

  return (
    <motion.div
      layout
      initial={{ y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.04 * index }}
      className="glass-card p-5"
    >
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-semibold bg-primary/10 text-ink">
              {name.split(' ').map((n) => n[0]).slice(0, 2).join('')}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-ink truncate">#{candidate.rank || index + 1} {name}</div>
              <div className="text-xs text-ink-muted truncate">{candidate.recommendation || 'Review Pending'}</div>
            </div>
            <span className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${riskClass(candidate.risk_level || 'Medium')}`}>
              Risk: {candidate.risk_level || 'Medium'}
            </span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${
              String(candidate.analysis_mode || 'esco').toLowerCase() === 'hybrid'
                ? 'bg-indigo-100 text-indigo-700 border-indigo-200'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}>
              Source: {String(candidate.analysis_mode || 'esco').toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
            <MetricBar label="Core Match" value={candidate.core_match} color="#22c55e" />
            <MetricBar label="Secondary" value={candidate.secondary_match} color="#00C2CB" />
            <MetricBar label="Bonus" value={candidate.bonus_match} color="#3b82f6" />
          </div>

          <div className="flex flex-wrap gap-2 mb-2">
            {(strengths || []).slice(0, 4).map((skill, i) => (
              <span key={`${skill}-${i}`} className="px-2 py-0.5 text-xs rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                {skill}
              </span>
            ))}
            {strengths.length === 0 && (
              <span className="text-xs text-ink-muted">No standout strengths detected</span>
            )}
          </div>

          {gaps.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {gaps.slice(0, 3).map((gap, i) => (
                <span key={`${gap}-${i}`} className="px-2 py-0.5 text-xs rounded-md bg-orange-50 text-orange-700 border border-orange-200">
                  Gap: {gap}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="w-full lg:w-52 shrink-0 rounded-xl border border-surface-alt bg-surface/50 p-4">
          <p className="text-[11px] uppercase tracking-wider text-ink-muted">Decision Score</p>
          <p className="text-3xl font-bold" style={{ color: scoreColor(decision) }}>{formatPct(decision)}</p>
          <div className="mt-2 text-xs text-ink-muted space-y-1">
            <p>Overall: {formatPct(candidate.overall_score)}</p>
            <p>Coverage: {formatPct(candidate.skill_coverage_ratio)}</p>
            <p>Missing: {candidate.missing_count ?? 0}</p>
          </div>

          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={() => onToggleShortlist(name)}
              className={`flex-1 text-xs font-semibold rounded-md px-2 py-2 border ${
                shortlisted
                  ? 'bg-emerald-600 border-emerald-700 text-white'
                  : 'bg-white border-surface-alt text-ink-muted hover:bg-surface'
              }`}
            >
              {shortlisted ? 'Shortlisted' : 'Shortlist'}
            </button>
            <Link to="/demo" className="text-xs font-semibold rounded-md px-2 py-2 border border-surface-alt text-ink-muted hover:bg-surface">
              View
            </Link>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function RecruiterPage() {
  const [candidates, setCandidates] = useState([]);
  const [targetRole, setTargetRole] = useState('');
  const [roleSearch, setRoleSearch] = useState('');
  const [roleSuggestions, setRoleSuggestions] = useState([]);
  const [analysisMode, setAnalysisMode] = useState('esco');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [error, setError] = useState('');
  const [useDemo, setUseDemo] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [sortBy, setSortBy] = useState('decision');
  const [matchFilter, setMatchFilter] = useState('All');
  const [riskFilter, setRiskFilter] = useState('All');
  const [shortlist, setShortlist] = useState([]);
  const [isStateHydrated, setIsStateHydrated] = useState(false);

  const fileInputRef = useRef(null);
  const saveTimerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const hydrate = async () => {
      let hasRemoteState = false;

      try {
        const remote = await getDashboardState('recruiter');
        const saved = remote?.state || {};

        if (saved && Object.keys(saved).length > 0) {
          hasRemoteState = true;
          if (typeof saved.targetRole === 'string') {
            setTargetRole(saved.targetRole);
          }
          if (typeof saved.roleSearch === 'string') {
            setRoleSearch(saved.roleSearch);
          }
          if (typeof saved.useDemo === 'boolean') {
            setUseDemo(saved.useDemo);
          }
          if (typeof saved.analysisMode === 'string') {
            setAnalysisMode(saved.analysisMode === 'hybrid' ? 'hybrid' : 'esco');
          }
          if (Array.isArray(saved.candidates)) {
            setCandidates(saved.candidates);
          }
          if (Array.isArray(saved.uploadedFiles)) {
            setUploadedFiles(saved.uploadedFiles);
          }
          if (typeof saved.sortBy === 'string') {
            setSortBy(saved.sortBy);
          }
          if (typeof saved.matchFilter === 'string') {
            setMatchFilter(saved.matchFilter);
          }
          if (typeof saved.riskFilter === 'string') {
            setRiskFilter(saved.riskFilter);
          }
          if (Array.isArray(saved.shortlist)) {
            setShortlist(saved.shortlist);
          }
        }
      } catch {
        // Ignore backend hydration failures and use local fallback.
      }

      if (!hasRemoteState) {
        try {
          const raw = localStorage.getItem(RECRUITER_DASHBOARD_STORAGE_KEY);
          if (raw) {
            const saved = JSON.parse(raw);
            if (typeof saved.targetRole === 'string') {
              setTargetRole(saved.targetRole);
            }
            if (typeof saved.roleSearch === 'string') {
              setRoleSearch(saved.roleSearch);
            }
            if (typeof saved.useDemo === 'boolean') {
              setUseDemo(saved.useDemo);
            }
            if (typeof saved.analysisMode === 'string') {
              setAnalysisMode(saved.analysisMode === 'hybrid' ? 'hybrid' : 'esco');
            }
            if (Array.isArray(saved.candidates)) {
              setCandidates(saved.candidates);
            }
            if (Array.isArray(saved.uploadedFiles)) {
              setUploadedFiles(saved.uploadedFiles);
            }
            if (typeof saved.sortBy === 'string') {
              setSortBy(saved.sortBy);
            }
            if (typeof saved.matchFilter === 'string') {
              setMatchFilter(saved.matchFilter);
            }
            if (typeof saved.riskFilter === 'string') {
              setRiskFilter(saved.riskFilter);
            }
            if (Array.isArray(saved.shortlist)) {
              setShortlist(saved.shortlist);
            }
          }
        } catch {
          // Ignore malformed local persisted dashboard state.
        }
      }

      if (!cancelled) {
        setIsStateHydrated(true);
      }
    };

    hydrate();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isStateHydrated) {
      return;
    }

    const snapshot = {
      targetRole,
      roleSearch,
      useDemo,
      analysisMode,
      candidates,
      // Keep metadata only; resume text can be too large for browser storage.
      uploadedFiles: uploadedFiles.map((file) => ({
        file_name: file.file_name,
        candidate_name: file.candidate_name,
      })),
      sortBy,
      matchFilter,
      riskFilter,
      shortlist,
      savedAt: Date.now(),
    };

    try {
      localStorage.setItem(RECRUITER_DASHBOARD_STORAGE_KEY, JSON.stringify(snapshot));
    } catch {
      // Ignore local fallback storage quota or serialization issues.
    }

    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      saveDashboardState('recruiter', snapshot).catch(() => {
        // Ignore transient backend persistence errors.
      });
    }, 700);

    return () => clearTimeout(saveTimerRef.current);
  }, [
    isStateHydrated,
    targetRole,
    roleSearch,
    useDemo,
    analysisMode,
    candidates,
    uploadedFiles,
    sortBy,
    matchFilter,
    riskFilter,
    shortlist,
  ]);

  const handleRoleSearch = async (query) => {
    setRoleSearch(query);
    if (query.trim().length < 2) {
      setRoleSuggestions([]);
      return;
    }

    try {
      const results = await searchOccupations(query, 8, analysisMode);
      setRoleSuggestions(results);
    } catch {
      setRoleSuggestions([]);
    }
  };

  const selectRole = (label) => {
    setTargetRole(label);
    setRoleSearch(label);
    setRoleSuggestions([]);
  };

  const handleFilesAdd = async (files) => {
    const fileList = Array.from(files || []);
    if (!fileList.length) {
      return;
    }

    setError('');
    setLoadingMsg(`Reading ${fileList.length} file${fileList.length > 1 ? 's' : ''}...`);

    try {
      const parsedFiles = await Promise.all(
        fileList.map(async (file) => {
          const text = await parseFileToText(file);
          if (!text || text.trim().length < 20) {
            return null;
          }

          const parsed = parseResumeText(text);
          return {
            file_name: file.name,
            resume_text: text,
            candidate_name: parsed?.name || file.name.replace(/\.[^.]+$/, ''),
          };
        })
      );

      const validFiles = parsedFiles.filter(Boolean);
      if (!validFiles.length) {
        setError('Could not extract useful text from selected files.');
        return;
      }

      setUploadedFiles((prev) => {
        const seenNames = new Set(prev.map((f) => f.file_name));
        const deduped = validFiles.filter((f) => !seenNames.has(f.file_name));
        return [...prev, ...deduped].slice(0, 10);
      });
    } catch (err) {
      setError(err.message || 'Failed to read files.');
    } finally {
      setLoadingMsg('');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFilesAdd(e.dataTransfer.files);
  };

  const removeFile = (idx) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAnalyzeBatch = async () => {
    if (!targetRole.trim()) {
      setError('Please select a target role.');
      return;
    }
    if (uploadedFiles.length === 0) {
      setError('Please upload at least one resume.');
      return;
    }

    if (uploadedFiles.some((file) => !file.resume_text)) {
      setError('Please re-upload resumes after refresh before running a new analysis.');
      return;
    }

    setError('');
    setIsLoading(true);
    setLoadingMsg('Analyzing and ranking candidates...');

    try {
      const batchData = uploadedFiles.map((f) => ({
        resume_text: f.resume_text,
        candidate_name: f.candidate_name,
      }));

      const result = await batchAnalyzeResumes(batchData, targetRole, analysisMode);
      const normalizedCandidates = (result.candidates || []).map((candidate) => ({
        ...candidate,
        analysis_mode: candidate.analysis_mode || analysisMode,
      }));
      setCandidates(normalizedCandidates);
      setUseDemo(false);
      setShortlist([]);
    } catch (err) {
      setError(err.message || 'Batch analysis failed.');
    } finally {
      setIsLoading(false);
      setLoadingMsg('');
    }
  };

  const rawCandidates = useDemo ? DEMO_CANDIDATES : candidates;

  const filteredCandidates = useMemo(() => {
    let rows = [...rawCandidates];

    if (matchFilter !== 'All') {
      rows = rows.filter((c) => (c.match_label || c.match || 'Unrated') === matchFilter);
    }

    if (riskFilter !== 'All') {
      rows = rows.filter((c) => (c.risk_level || 'Medium') === riskFilter);
    }

    rows.sort((a, b) => {
      if (sortBy === 'core') {
        return (b.core_match || 0) - (a.core_match || 0);
      }
      if (sortBy === 'overall') {
        return (b.overall_score || b.score || 0) - (a.overall_score || a.score || 0);
      }
      if (sortBy === 'missing') {
        return (a.missing_count || 0) - (b.missing_count || 0);
      }
      return (b.decision_score || b.overall_score || 0) - (a.decision_score || a.overall_score || 0);
    });

    return rows.map((row, idx) => ({ ...row, rank: idx + 1 }));
  }, [rawCandidates, matchFilter, riskFilter, sortBy]);

  const stats = useMemo(() => {
    const list = filteredCandidates;
    const avgDecision = list.length
      ? list.reduce((acc, c) => acc + Number(c.decision_score || c.overall_score || 0), 0) / list.length
      : 0;
    const strongCore = list.filter((c) => Number(c.core_match || 0) >= 70).length;
    const highRisk = list.filter((c) => (c.risk_level || 'Medium') === 'High').length;
    const top = list[0];

    return {
      topName: top?.candidate_name || top?.name || '-',
      topScore: Number(top?.decision_score || top?.overall_score || 0),
      avgDecision,
      strongCore,
      highRisk,
    };
  }, [filteredCandidates]);

  const toggleShortlist = (name) => {
    setShortlist((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]));
  };

  const shortlistedCandidates = useMemo(() => {
    if (!shortlist.length) {
      return [];
    }
    return rawCandidates.filter((candidate) => shortlist.includes(candidate.candidate_name || candidate.name || ''));
  }, [rawCandidates, shortlist]);

  const topThreeComparison = useMemo(() => filteredCandidates.slice(0, 3), [filteredCandidates]);

  const handleExportShortlistCsv = () => {
    if (!shortlistedCandidates.length) {
      setError('Shortlist is empty. Add candidates to export CSV.');
      return;
    }

    const headers = [
      'Candidate Name',
      'Recommendation',
      'Risk Level',
      'Decision Score',
      'Overall Score',
      'Core Match',
      'Secondary Match',
      'Bonus Match',
      'Coverage Ratio',
      'Missing Skills Count',
      'Top Strengths',
      'Top Gaps',
    ];

    const rows = shortlistedCandidates.map((candidate) => [
      candidate.candidate_name || candidate.name || '',
      candidate.recommendation || '',
      candidate.risk_level || '',
      formatPct(candidate.decision_score || candidate.overall_score),
      formatPct(candidate.overall_score),
      formatPct(candidate.core_match),
      formatPct(candidate.secondary_match),
      formatPct(candidate.bonus_match),
      formatPct(candidate.skill_coverage_ratio),
      String(candidate.missing_count ?? 0),
      (candidate.top_strengths || []).join(' | '),
      (candidate.top_gaps || []).join(' | '),
    ]);

    const csv = [headers, ...rows]
      .map((row) => row.map(escapeCsvCell).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const now = new Date();
    const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
    const file = `shortlist-${stamp}.csv`;

    const a = document.createElement('a');
    a.href = url;
    a.download = file;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen pt-28 pb-20">
      <div className="section-container">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-ink" style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>
                Recruiter Intelligence Dashboard
              </h2>
              <p className="text-ink-muted text-sm">
                Advanced candidate ranking with stronger scoring accuracy, risk indicators, and shortlist workflow.
              </p>
            </div>
            <LogoIcon size={40} />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
            <div className="glass-card p-4">
              <p className="text-xs text-ink-muted uppercase tracking-wider">Top Candidate</p>
              <p className="text-sm font-semibold text-ink mt-1 truncate">{stats.topName}</p>
              <p className="text-lg font-bold mt-1" style={{ color: scoreColor(stats.topScore) }}>{formatPct(stats.topScore)}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-ink-muted uppercase tracking-wider">Average Decision</p>
              <p className="text-lg font-bold text-ink mt-2">{formatPct(stats.avgDecision)}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-ink-muted uppercase tracking-wider">Strong Core ({'>='}70)</p>
              <p className="text-lg font-bold text-emerald-600 mt-2">{stats.strongCore}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-ink-muted uppercase tracking-wider">High Risk</p>
              <p className="text-lg font-bold text-red-600 mt-2">{stats.highRisk}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-ink-muted uppercase tracking-wider">Shortlisted</p>
              <p className="text-lg font-bold text-primary mt-2">{shortlist.length}</p>
            </div>
          </div>

          <div className="glass-card p-5 mb-6">
            <label className="text-xs font-semibold uppercase tracking-wider text-ink-muted block mb-2">Target Role</label>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. Software Developer, Data Engineer..."
                value={roleSearch}
                onChange={(e) => handleRoleSearch(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-surface border border-surface-alt text-sm"
              />
              {roleSuggestions.length > 0 && (
                <div className="absolute top-full mt-1 w-full bg-surface border border-surface-alt rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
                  {roleSuggestions.map((r, i) => (
                    <button
                      key={`${r.preferred_label}-${i}`}
                      onClick={() => selectRole(r.preferred_label)}
                      className="w-full text-left px-4 py-2 hover:bg-surface-alt text-sm text-ink"
                    >
                      {r.preferred_label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {targetRole && <p className="text-xs text-primary mt-2">Selected: {targetRole}</p>}

            <div className="mt-4">
              <label className="text-xs font-semibold uppercase tracking-wider text-ink-muted block mb-2">Analysis Mode</label>
              <div className="inline-flex rounded-xl border border-surface-alt bg-surface p-1">
                {ANALYSIS_MODE_OPTIONS.map((option) => {
                  const selected = analysisMode === option.id;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => setAnalysisMode(option.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                        selected
                          ? 'bg-primary text-white shadow-sm'
                          : 'text-ink-muted hover:text-ink'
                      }`}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div
          className="glass-card p-8 mb-8 border-2 border-dashed border-surface-alt/50"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <div className="text-center">
            <h3 className="text-sm font-semibold text-ink mb-1">Upload Candidate Resumes</h3>
            <p className="text-xs text-ink-muted mb-4">Drag and drop multiple files or choose files manually. Max 10 resumes.</p>
            <button onClick={() => fileInputRef.current?.click()} className="btn-secondary text-sm">
              Choose Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => handleFilesAdd(e.target.files)}
              className="hidden"
            />
          </div>

          {uploadedFiles.length > 0 && (
            <div className="mt-6 pt-6 border-t border-surface-alt space-y-2">
              {uploadedFiles.map((f, i) => (
                <div key={`${f.file_name}-${i}`} className="flex items-center justify-between p-3 bg-surface rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-ink truncate">{f.candidate_name}</p>
                    <p className="text-xs text-ink-muted truncate">{f.file_name}</p>
                  </div>
                  <button onClick={() => removeFile(i)} className="ml-3 text-xs text-danger hover:text-danger font-medium">
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 rounded-lg bg-danger/8 border border-danger/20 text-danger text-sm"
          >
            {error}
          </motion.div>
        )}

        <div className="mb-8 flex items-center gap-3 justify-center flex-wrap">
          {uploadedFiles.length > 0 && targetRole && (
            <button onClick={handleAnalyzeBatch} disabled={isLoading} className="btn-primary">
              {isLoading ? loadingMsg : `Analyze ${uploadedFiles.length} ${uploadedFiles.length === 1 ? 'Resume' : 'Resumes'}`}
            </button>
          )}
          <button
            onClick={() => {
              setUploadedFiles([]);
              setTargetRole('');
              setRoleSearch('');
              setCandidates([]);
              setUseDemo(true);
              setShortlist([]);
              setError('');
            }}
            className="btn-secondary"
          >
            Reset
          </button>
          <button onClick={() => setUseDemo((prev) => !prev)} className="btn-secondary">
            {useDemo ? 'Use Live Upload Mode' : 'Show Demo Data'}
          </button>
        </div>

        <div className="glass-card p-4 mb-4 flex flex-wrap items-center gap-3">
          <div>
            <label className="text-xs text-ink-muted">Sort by</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="ml-2 px-2 py-1 text-sm rounded-md border border-surface-alt bg-surface">
              <option value="decision">Decision Score</option>
              <option value="overall">Overall Score</option>
              <option value="core">Core Match</option>
              <option value="missing">Least Missing Skills</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-ink-muted">Match</label>
            <select value={matchFilter} onChange={(e) => setMatchFilter(e.target.value)} className="ml-2 px-2 py-1 text-sm rounded-md border border-surface-alt bg-surface">
              <option>All</option>
              <option>Excellent</option>
              <option>Good</option>
              <option>Fair</option>
              <option>Weak</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-ink-muted">Risk</label>
            <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} className="ml-2 px-2 py-1 text-sm rounded-md border border-surface-alt bg-surface">
              <option>All</option>
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
            </select>
          </div>
          <button
            type="button"
            onClick={handleExportShortlistCsv}
            disabled={shortlistedCandidates.length === 0}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Export Shortlist CSV ({shortlistedCandidates.length})
          </button>
        </div>

        <div className="glass-card p-5 mb-8">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h3 className="text-sm font-semibold text-ink">Top 3 Side-by-Side Comparison</h3>
            <span className="text-xs text-ink-muted">Quick compare by decision, score and risk</span>
          </div>

          {topThreeComparison.length === 0 ? (
            <p className="text-sm text-ink-muted">No candidates to compare yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {topThreeComparison.map((candidate) => {
                const name = candidate.candidate_name || candidate.name || 'Candidate';
                return (
                  <div key={`compare-${name}`} className="rounded-xl border border-surface-alt bg-surface/60 p-4">
                    <p className="text-xs uppercase tracking-wider text-ink-muted">Rank #{candidate.rank}</p>
                    <p className="text-sm font-semibold text-ink mt-1 truncate">{name}</p>
                    <p className="text-xs text-ink-muted mt-1">{candidate.recommendation || 'Review Pending'}</p>

                    <div className="mt-3 space-y-1 text-xs text-ink-muted">
                      <p>Decision: <span className="font-semibold text-ink">{formatPct(candidate.decision_score || candidate.overall_score)}</span></p>
                      <p>Overall: <span className="font-semibold text-ink">{formatPct(candidate.overall_score)}</span></p>
                      <p>Core: <span className="font-semibold text-ink">{formatPct(candidate.core_match)}</span></p>
                      <p>Risk: <span className="font-semibold text-ink">{candidate.risk_level || 'Medium'}</span></p>
                      <p>Missing: <span className="font-semibold text-ink">{candidate.missing_count ?? 0}</span></p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-ink">
              {useDemo ? 'Demo Candidates' : `Results for "${targetRole}"`} ({filteredCandidates.length})
            </h3>
          </div>

          {filteredCandidates.length > 0 ? (
            <div className="space-y-3">
              {filteredCandidates.map((candidate, i) => (
                <CandidateCard
                  key={`${candidate.candidate_name || candidate.name || 'candidate'}-${i}`}
                  candidate={candidate}
                  index={i}
                  shortlisted={shortlist.includes(candidate.candidate_name || candidate.name || '')}
                  onToggleShortlist={toggleShortlist}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-ink-muted">
              <p className="text-sm">No candidates match current filters. Try changing filter settings.</p>
            </div>
          )}
        </div>

        <div className="glass-card p-5 mb-8">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h3 className="text-sm font-semibold text-ink">Interview Questions For Shortlisted Candidates</h3>
            <span className="text-xs text-ink-muted">Generated from strengths, gaps and selected role</span>
          </div>

          {shortlistedCandidates.length === 0 ? (
            <p className="text-sm text-ink-muted">Shortlist candidates to auto-generate targeted interview questions.</p>
          ) : (
            <div className="space-y-4">
              {shortlistedCandidates.map((candidate) => {
                const name = candidate.candidate_name || candidate.name || 'Candidate';
                const questions = buildInterviewQuestions(candidate, targetRole || 'this role');

                return (
                  <div key={`questions-${name}`} className="rounded-xl border border-surface-alt bg-surface/60 p-4">
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <p className="text-sm font-semibold text-ink">{name}</p>
                      <span className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${riskClass(candidate.risk_level || 'Medium')}`}>
                        {candidate.risk_level || 'Medium'} Risk
                      </span>
                    </div>
                    <ol className="space-y-2 text-sm text-ink-muted list-decimal list-inside">
                      {questions.map((q) => (
                        <li key={q.id}>{q.text}</li>
                      ))}
                    </ol>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-8 text-center">
          <Link to="/upload" className="btn-secondary">Upload Individual Resume</Link>
        </div>
      </div>

      <div className="noise-overlay" />
    </div>
  );
}
