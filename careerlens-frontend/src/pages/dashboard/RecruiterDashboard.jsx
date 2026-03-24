/**
 * Recruiter Dashboard
 * Live batch candidate analysis, ranking, and shortlisting
 */

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import Papa from 'papaparse';
import {
  Users,
  Upload,
  Zap,
  CheckCircle,
  XCircle,
  Star,
  TrendingUp,
  Download,
  LogOut,
  Menu,
  X,
  FileText,
  Clipboard,
  Search,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import Logo from '../../components/Logo';
import {
  analyzeHybridDiagnostics,
  batchAnalyzeResumes,
  parseFileToText,
  searchOccupations,
} from '../../services/api';
import { parseResumeText } from '../../services/resumeParser';

const tierClassMap = {
  top: 'bg-green-100 text-green-700',
  suitable: 'bg-blue-100 text-blue-700',
  review: 'bg-amber-100 text-amber-700',
};

const ANALYSIS_MODE_OPTIONS = [
  { id: 'esco', label: 'ESCO' },
  { id: 'hybrid', label: 'Hybrid' },
];

function normalizeText(value = '') {
  return String(value).trim().toLowerCase();
}

function shortlistKey(roleTitle = '', candidateName = '') {
  return `${normalizeText(roleTitle)}::${normalizeText(candidateName)}`;
}

function toTier(matchLabel = '') {
  const label = String(matchLabel).toLowerCase();
  if (label.includes('excellent')) return 'top';
  if (label.includes('good')) return 'suitable';
  return 'review';
}

function recommendationFromScore(score) {
  if (score >= 75) return 'Strong fit. Prioritize interview scheduling.';
  if (score >= 55) return 'Good potential. Move to technical round.';
  if (score >= 35) return 'Moderate fit. Consider for backup pipeline.';
  return 'Low match for this role. Keep for future openings.';
}

function toSafePercent(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
}

function uniqueNormalized(values = []) {
  const seen = new Set();
  const output = [];
  values.forEach((value) => {
    const item = String(value || '').trim();
    if (!item) return;
    const key = normalizeText(item);
    if (seen.has(key)) return;
    seen.add(key);
    output.push(item);
  });
  return output;
}

function getComprehensiveClassification(candidate) {
  const decision = toSafePercent(candidate?.decision_score);
  const overall = toSafePercent(candidate?.overall_score);
  const core = toSafePercent(candidate?.core_match);
  const risk = String(candidate?.risk_level || '').toLowerCase();

  if (decision >= 80 && core >= 70 && risk === 'low') {
    return {
      label: 'High Priority Shortlist',
      toneClass: 'bg-green-50 border-green-200 text-green-800',
      summary: 'Strong technical alignment with low delivery risk.',
    };
  }
  if (decision >= 65 && core >= 55) {
    return {
      label: 'Interview Recommended',
      toneClass: 'bg-blue-50 border-blue-200 text-blue-800',
      summary: 'Solid role fit with manageable skill gaps.',
    };
  }
  if (overall >= 45) {
    return {
      label: 'Conditional Review',
      toneClass: 'bg-amber-50 border-amber-200 text-amber-800',
      summary: 'Potential match if role priorities are flexible.',
    };
  }
  return {
    label: 'Future Pipeline',
    toneClass: 'bg-rose-50 border-rose-200 text-rose-800',
    summary: 'Not ideal for this opening, but may fit future roles.',
  };
}

function downloadCsv(rows, fileName) {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const escaped = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const csv = [
    headers.join(','),
    ...rows.map((row) => headers.map((h) => escaped(row[h])).join(',')),
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
}

function splitIntoChunks(items = [], chunkSize = 10) {
  const safeSize = Math.max(1, Number(chunkSize) || 10);
  const chunks = [];
  for (let i = 0; i < items.length; i += safeSize) {
    chunks.push(items.slice(i, i + safeSize));
  }
  return chunks;
}

function rankBatchCandidates(candidates = [], mode = 'esco') {
  const normalizedMode = String(mode || '').toLowerCase() === 'hybrid' ? 'hybrid' : 'esco';

  return [...candidates]
    .sort((a, b) => {
      const decisionDiff = toSafePercent(b.decision_score) - toSafePercent(a.decision_score);
      if (decisionDiff !== 0) return decisionDiff;

      const coreDiff = toSafePercent(b.core_match) - toSafePercent(a.core_match);
      if (coreDiff !== 0) return coreDiff;

      const overallDiff = toSafePercent(b.overall_score) - toSafePercent(a.overall_score);
      if (overallDiff !== 0) return overallDiff;

      return toSafePercent(a.missing_count) - toSafePercent(b.missing_count);
    })
    .map((candidate, index) => ({
      ...candidate,
      rank: index + 1,
      id: `${candidate.candidate_name || 'candidate'}-${index}`,
      tier: toTier(candidate.match_label),
      analysis_mode: candidate.analysis_mode || normalizedMode,
    }));
}

function firstMatchingKey(row = {}, candidates = []) {
  const keys = Object.keys(row || {});
  for (const key of keys) {
    const normalized = normalizeText(key).replace(/[^a-z0-9]/g, '');
    if (candidates.includes(normalized)) {
      return key;
    }
  }
  return null;
}

async function parseCandidateCsv(file) {
  const text = await file.text();
  const parsed = Papa.parse(text, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => String(header || '').trim(),
  });

  if (parsed.errors?.length) {
    const firstError = parsed.errors[0];
    throw new Error(firstError?.message || 'invalid CSV format');
  }

  const rows = Array.isArray(parsed.data) ? parsed.data : [];
  if (!rows.length) {
    throw new Error('CSV is empty');
  }

  const sampleRow = rows[0] || {};
  const nameKey = firstMatchingKey(sampleRow, [
    'candidate',
    'candidatename',
    'name',
    'fullname',
    'applicant',
  ]);
  const resumeKey = firstMatchingKey(sampleRow, [
    'resumetext',
    'resume',
    'cv',
    'profile',
    'summary',
    'text',
  ]);

  if (!resumeKey) {
    throw new Error('CSV must include a resume text column (resume_text/resume/cv/text)');
  }

  const candidates = [];
  const failures = [];

  rows.forEach((row, index) => {
    const resumeText = String(row?.[resumeKey] || '').trim();
    const rawName = String(nameKey ? row?.[nameKey] || '' : '').trim();
    const fallbackName = `Candidate ${index + 1}`;
    const candidateName = rawName || parseResumeText(resumeText)?.name || fallbackName;

    if (resumeText.length < 20) {
      failures.push(`row ${index + 2}: resume text too short`);
      return;
    }

    candidates.push({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}-${index}`,
      fileName: `${file.name} [row ${index + 2}]`,
      candidateName,
      resumeText,
    });
  });

  return { candidates, failures };
}

const RecruiterDashboard = () => {
  const { user, logout, apiCall } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const roleDebounceRef = useRef(null);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeMenu, setActiveMenu] = useState('analyzer');
  const [resumeFiles, setResumeFiles] = useState([]);
  const [jobTitle, setJobTitle] = useState('');
  const [analysisMode, setAnalysisMode] = useState('esco');
  const [roleSuggestions, setRoleSuggestions] = useState([]);
  const [showRoleSuggestions, setShowRoleSuggestions] = useState(false);
  const [isParsingFiles, setIsParsingFiles] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [filterTier, setFilterTier] = useState('all');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [savedShortlists, setSavedShortlists] = useState([]);
  const [isLoadingShortlists, setIsLoadingShortlists] = useState(false);
  const [shortlistBusyKey, setShortlistBusyKey] = useState('');
  const [diagnosticsBusy, setDiagnosticsBusy] = useState(false);
  const [diagnosticsResult, setDiagnosticsResult] = useState(null);
  const [diagnosticsError, setDiagnosticsError] = useState('');
  const [error, setError] = useState('');
  const [isDragActive, setIsDragActive] = useState(false);
  const [reportCopied, setReportCopied] = useState(false);

  useEffect(() => {
    const onClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowRoleSuggestions(false);
      }
    };

    document.addEventListener('mousedown', onClickOutside);
    return () => {
      document.removeEventListener('mousedown', onClickOutside);
      clearTimeout(roleDebounceRef.current);
    };
  }, []);

  useEffect(() => {
    if (!user?.id) {
      return;
    }

    let active = true;

    const loadSavedShortlists = async () => {
      setIsLoadingShortlists(true);
      try {
        const rows = await apiCall('/recruiter/shortlists');
        if (active) {
          setSavedShortlists(Array.isArray(rows) ? rows : []);
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Could not load saved shortlists.');
        }
      } finally {
        if (active) {
          setIsLoadingShortlists(false);
        }
      }
    };

    loadSavedShortlists();

    return () => {
      active = false;
    };
  }, [user?.id]);

  useEffect(() => {
    if (!analysisResults.length) {
      setSelectedCandidate(null);
      return;
    }

    if (!selectedCandidate) {
      setSelectedCandidate(analysisResults[0]);
      return;
    }

    const exists = analysisResults.some((candidate) => candidate.id === selectedCandidate.id);
    if (!exists) {
      setSelectedCandidate(analysisResults[0]);
    }
  }, [analysisResults, selectedCandidate]);

  const handleRoleChange = (value) => {
    setJobTitle(value);
    setShowRoleSuggestions(false);

    clearTimeout(roleDebounceRef.current);
    roleDebounceRef.current = setTimeout(async () => {
      if (!value.trim() || value.trim().length < 2) {
        setRoleSuggestions([]);
        setShowRoleSuggestions(false);
        return;
      }

      try {
        const results = await searchOccupations(value.trim(), 8, analysisMode);
        setRoleSuggestions(results);
        setShowRoleSuggestions(results.length > 0);
      } catch {
        setRoleSuggestions([]);
        setShowRoleSuggestions(false);
      }
    }, 300);
  };

  useEffect(() => {
    setRoleSuggestions([]);
    setShowRoleSuggestions(false);
  }, [analysisMode]);

  const selectRoleSuggestion = (label) => {
    setJobTitle(label);
    setShowRoleSuggestions(false);
  };

  const processIncomingFiles = async (files) => {
    if (!files.length) return;

    setError('');
    setIsParsingFiles(true);

    const successEntries = [];
    const failedEntries = [];

    for (const file of files) {
      try {
        if (file.name.toLowerCase().endsWith('.csv')) {
          const csvResult = await parseCandidateCsv(file);
          successEntries.push(...csvResult.candidates);
          failedEntries.push(...csvResult.failures.map((error) => `${file.name}: ${error}`));
          continue;
        }

        const resumeText = await parseFileToText(file);
        if (!resumeText || resumeText.trim().length < 20) {
          throw new Error('insufficient text extracted');
        }

        const parsed = parseResumeText(resumeText);
        const baseName = file.name.replace(/\.[^.]+$/, '');

        successEntries.push({
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
          fileName: file.name,
          candidateName: parsed?.name || baseName,
          resumeText,
        });
      } catch (err) {
        failedEntries.push(`${file.name}: ${err.message || 'unable to process file'}`);
      }
    }

    if (successEntries.length) {
      setResumeFiles((prev) => [...prev, ...successEntries]);
    }

    if (failedEntries.length) {
      setError(`Some files were skipped. ${failedEntries.slice(0, 3).join(' | ')}`);
    }

    setIsParsingFiles(false);
  };

  const handleFilesUpload = async (event) => {
    const files = Array.from(event.target.files || []);
    await processIncomingFiles(files);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setIsDragActive(false);
    const files = Array.from(event.dataTransfer.files || []);
    await processIncomingFiles(files);
  };

  const removeResume = (id) => {
    setResumeFiles((prev) => prev.filter((file) => file.id !== id));
  };

  const findResumeTextForCandidate = (candidate) => {
    const candidateName = normalizeText(candidate?.candidate_name || '');
    if (!candidateName) return '';

    const match = resumeFiles.find((file) => normalizeText(file?.candidateName) === candidateName);
    return match?.resumeText || '';
  };

  const findSavedShortlist = (candidate, roleTitleOverride) => {
    const roleTitle = roleTitleOverride || candidate?.role_title || jobTitle;
    const key = shortlistKey(roleTitle, candidate?.candidate_name);
    return savedShortlists.find(
      (entry) => shortlistKey(entry.role_title, entry.candidate_name) === key
    );
  };

  const toggleShortlist = async (candidate, roleTitleOverride) => {
    if (!candidate?.candidate_name) {
      return;
    }

    const roleTitle = (roleTitleOverride || candidate.role_title || jobTitle || '').trim();
    if (!roleTitle) {
      setError('Please set a job role before saving shortlist entries.');
      return;
    }

    const key = shortlistKey(roleTitle, candidate.candidate_name);
    if (shortlistBusyKey === key) {
      return;
    }

    setShortlistBusyKey(key);
    setError('');

    try {
      const existing = findSavedShortlist(candidate, roleTitle);

      if (existing) {
        await apiCall(`/recruiter/shortlists/${existing.id}`, {
          method: 'DELETE',
        });

        setSavedShortlists((prev) => prev.filter((entry) => entry.id !== existing.id));
      } else {
        const payload = {
          role_title: roleTitle,
          candidate_name: candidate.candidate_name,
          rank: candidate.rank ?? null,
          overall_score: candidate.overall_score ?? null,
          core_match: candidate.core_match ?? null,
          secondary_match: candidate.secondary_match ?? null,
          bonus_match: candidate.bonus_match ?? null,
          match_label: candidate.match_label ?? null,
          analysis_mode: String(candidate.analysis_mode || analysisMode).toLowerCase() === 'hybrid' ? 'hybrid' : 'esco',
          top_strengths: candidate.top_strengths || [],
          top_gaps: candidate.top_gaps || [],
        };

        const saved = await apiCall('/recruiter/shortlists', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        setSavedShortlists((prev) => {
          const filtered = prev.filter(
            (entry) => shortlistKey(entry.role_title, entry.candidate_name) !== key
          );
          return [saved, ...filtered];
        });
      }
    } catch (err) {
      setError(err.message || 'Could not update shortlist.');
    } finally {
      setShortlistBusyKey('');
    }
  };

  const resetAnalysis = () => {
    setAnalysisResults([]);
    setSelectedCandidate(null);
    setFilterTier('all');
    setDiagnosticsResult(null);
    setDiagnosticsError('');
    setError('');
    setActiveMenu('analyzer');
  };

  const runSelectedCandidateDiagnostics = async () => {
    if (analysisMode !== 'hybrid') {
      setDiagnosticsError('Switch to Hybrid mode to run diagnostics.');
      return;
    }

    if (!selectedCandidate) {
      setDiagnosticsError('Select a candidate first.');
      return;
    }

    const resumeText = findResumeTextForCandidate(selectedCandidate);
    if (!resumeText) {
      setDiagnosticsError('Resume text not available for this candidate in current session. Re-upload to run diagnostics.');
      return;
    }

    if (!jobTitle.trim()) {
      setDiagnosticsError('Set a target role to run diagnostics.');
      return;
    }

    setDiagnosticsBusy(true);
    setDiagnosticsError('');

    try {
      const result = await analyzeHybridDiagnostics(resumeText, jobTitle.trim());
      setDiagnosticsResult(result);
    } catch (err) {
      setDiagnosticsError(err.message || 'Diagnostics call failed.');
    } finally {
      setDiagnosticsBusy(false);
    }
  };

  useEffect(() => {
    setDiagnosticsResult(null);
    setDiagnosticsError('');
  }, [selectedCandidate?.id, analysisMode, jobTitle]);

  const handleAnalyzeCandidates = async () => {
    if (!jobTitle.trim()) {
      setError('Please enter a job role before running analysis.');
      return;
    }
    if (resumeFiles.length === 0) {
      setError('Please upload at least one candidate resume.');
      return;
    }

    setError('');
    setAnalyzing(true);
    try {
      const payload = resumeFiles.map((file) => ({
        resume_text: file.resumeText,
        candidate_name: file.candidateName,
      }));

      const payloadChunks = splitIntoChunks(payload, 10);
      const chunkResults = [];

      for (const chunk of payloadChunks) {
        const result = await batchAnalyzeResumes(chunk, jobTitle.trim(), analysisMode);
        chunkResults.push(...(result?.candidates || []));
      }

      const normalized = rankBatchCandidates(chunkResults, analysisMode);

      setAnalysisResults(normalized);
      setSelectedCandidate(normalized[0] || null);
      setActiveMenu('analytics');

      if (normalized.length === 0) {
        setError('No candidates could be analyzed. Try different resumes.');
      } else if (payloadChunks.length > 1) {
        setError(`Analyzed ${normalized.length} candidates across ${payloadChunks.length} backend batches (${analysisMode.toUpperCase()}).`);
      }
    } catch (err) {
      setError(err.message || 'Batch analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  const allCandidates = analysisResults;
  const filteredCandidates = allCandidates
    .filter((candidate) => filterTier === 'all' || candidate.tier === filterTier)
    .sort((a, b) => b.overall_score - a.overall_score);
  const shortlistedCandidates = savedShortlists
    .filter((candidate) => {
      if (!jobTitle.trim()) {
        return true;
      }
      return normalizeText(candidate.role_title) === normalizeText(jobTitle);
    })
    .sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));

  const averageScore = allCandidates.length
    ? (allCandidates.reduce((sum, candidate) => sum + candidate.overall_score, 0) / allCandidates.length).toFixed(1)
    : '0.0';
  const topTierCount = allCandidates.filter((candidate) => candidate.tier === 'top').length;

  const selectedCandidateDetails = useMemo(() => {
    if (!selectedCandidate) {
      return null;
    }

    const apiSkillClassification = selectedCandidate.skill_classification || {};
    const apiComprehensive = selectedCandidate.comprehensive_classification;

    return {
      core: {
        matched: uniqueNormalized(apiSkillClassification.core?.matched || selectedCandidate.top_strengths || []),
        missing: uniqueNormalized(apiSkillClassification.core?.missing || selectedCandidate.top_gaps || []),
      },
      language: {
        matched: uniqueNormalized(apiSkillClassification.language?.matched || []),
        missing: uniqueNormalized(apiSkillClassification.language?.missing || []),
      },
      other: {
        matched: uniqueNormalized(apiSkillClassification.other?.matched || []),
        missing: uniqueNormalized(apiSkillClassification.other?.missing || []),
      },
      classification: apiComprehensive || getComprehensiveClassification(selectedCandidate),
      sourceAvailable: true,
    };
  }, [selectedCandidate]);

  const exportFullReport = () => {
    if (!allCandidates.length) return;
    const rows = allCandidates.map((candidate) => ({
      Rank: candidate.rank,
      Candidate: candidate.candidate_name,
      Source: String(candidate.analysis_mode || analysisMode).toUpperCase(),
      Score: candidate.overall_score,
      Match: candidate.match_label,
      Core: candidate.core_match,
      Secondary: candidate.secondary_match,
      Bonus: candidate.bonus_match,
      MatchedSkills: candidate.matched_count,
      MissingSkills: candidate.missing_count,
      TopStrengths: (candidate.top_strengths || []).join('; '),
      TopGaps: (candidate.top_gaps || []).join('; '),
    }));
    downloadCsv(rows, `recruiter-report-${Date.now()}.csv`);
  };

  const exportShortlistReport = () => {
    if (!shortlistedCandidates.length) return;
    const rows = shortlistedCandidates.map((candidate) => ({
      Role: candidate.role_title,
      Rank: candidate.rank,
      Candidate: candidate.candidate_name,
      Source: String(candidate.analysis_mode || analysisMode).toUpperCase(),
      Score: candidate.overall_score,
      Match: candidate.match_label,
      Core: candidate.core_match,
      Secondary: candidate.secondary_match,
      Bonus: candidate.bonus_match,
      TopStrengths: (candidate.top_strengths || []).join('; '),
    }));
    downloadCsv(rows, `recruiter-shortlist-${Date.now()}.csv`);
  };

  const copyExecutiveSummary = async () => {
    if (!allCandidates.length) return;
    const top3 = allCandidates.slice(0, 3).map((candidate) =>
      `${candidate.rank}. ${candidate.candidate_name} - ${candidate.overall_score.toFixed(1)}% (${candidate.match_label})`
    ).join('\n');
    const summary = [
      `Role: ${jobTitle}`,
      `Source mode: ${analysisMode.toUpperCase()}`,
      `Candidates analyzed: ${allCandidates.length}`,
      `Average score: ${averageScore}%`,
      `Top tier candidates: ${topTierCount}`,
      'Top 3 candidates:',
      top3,
    ].join('\n');

    try {
      await navigator.clipboard.writeText(summary);
      setReportCopied(true);
      setTimeout(() => setReportCopied(false), 1600);
    } catch {
      setError('Could not copy report summary to clipboard.');
    }
  };

  const Sidebar = () => (
    <aside
      className={`fixed inset-y-0 left-0 w-64 glass-panel !border-y-0 !border-l-0 !rounded-none z-[100] flex flex-col transform transition-transform duration-300 md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
    >
      {/* Logo */}
      <div className="p-6 border-b border-slate-200/60 flex items-center justify-center">
        <Logo size="md" />
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {[
          { id: 'analyzer', icon: Search, label: 'Analyzer' },
          { id: 'analytics', icon: TrendingUp, label: 'Analytics' },
          { id: 'shortlist', icon: Star, label: 'Shortlist' },
          { id: 'reports', icon: Download, label: 'Reports' },
        ].map(({ id, icon: Icon, label }) => (
          <motion.button
            key={id}
            onClick={() => {
              setActiveMenu(id);
              setSidebarOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeMenu === id
                ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 font-semibold'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
            whileHover={{ x: 5 }}
          >
            <Icon size={18} />
            <span className="font-medium">{label}</span>
          </motion.button>
        ))}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-gray-200 dark:border-slate-700">
        <motion.button
          onClick={async () => {
            const result = await logout();
            if (result.success) {
              navigate('/', { replace: true });
              window.scrollTo({ top: 0, behavior: 'auto' });
            }
          }}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-500 hover:bg-red-50 hover:text-red-600 transition-all font-semibold"
          whileHover={{ x: 5 }}
        >
          <LogOut size={18} />
          <span className="font-medium">Logout</span>
        </motion.button>
      </div>
    </aside>
  );

  const renderAnalyzer = () => (
    <div className="space-y-6">
      <div className="space-y-2" ref={suggestionsRef}>
        <label className="block text-sm font-bold uppercase tracking-wider text-slate-500">Job Position</label>
        <div className="relative">
          <input
            type="text"
            value={jobTitle}
            onChange={(event) => handleRoleChange(event.target.value)}
            placeholder="e.g., Senior Software Engineer"
            className="w-full px-5 py-4 rounded-2xl bg-slate-50/50 border-2 border-slate-100 focus:bg-white focus:border-cyan-400 focus:ring-4 focus:ring-cyan-500/10 outline-none transition-all text-slate-800 font-medium placeholder-slate-400"
          />

          {showRoleSuggestions && (
            <div className="absolute top-full left-0 right-0 mt-1 z-20 rounded-xl bg-white border border-slate-200 shadow-lg overflow-hidden max-h-60 overflow-y-auto">
              {roleSuggestions.map((suggestion, idx) => (
                <button
                  key={suggestion.esco_id || `${suggestion.preferred_label}-${idx}`}
                  type="button"
                  onClick={() => selectRoleSuggestion(suggestion.preferred_label)}
                  className="w-full text-left px-4 py-2.5 hover:bg-slate-50 text-sm text-slate-700"
                >
                  {suggestion.preferred_label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="pt-2">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Analysis Mode</p>
          <div className="inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1">
            {ANALYSIS_MODE_OPTIONS.map((option) => {
              const selected = analysisMode === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setAnalysisMode(option.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                    selected
                      ? 'bg-cyan-600 text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-800'
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragActive(true);
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-3xl p-10 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-cyan-400 bg-cyan-50/80 shadow-lg shadow-cyan-100'
            : 'border-cyan-200 bg-cyan-50/30 hover:bg-cyan-50/80 hover:border-cyan-300 hover:shadow-lg hover:shadow-cyan-100'
        }`}
      >
        <div className="w-20 h-20 bg-white rounded-full mx-auto flex items-center justify-center shadow-sm mb-4">
          <Upload size={32} className="text-cyan-500" strokeWidth={2.5} />
        </div>
        <p className="font-bold text-lg text-slate-800 tracking-tight">Drop resumes here</p>
        <p className="text-sm font-medium text-slate-500 mt-1">or click to select files and CSV candidate sheets</p>
        {resumeFiles.length > 0 && (
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-50 text-green-600 font-bold text-sm">
            <CheckCircle size={16} />
            {resumeFiles.length} file(s) ready
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.text,.csv"
          onChange={handleFilesUpload}
          className="hidden"
        />
      </div>

      {resumeFiles.length > 0 && (
        <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
          {resumeFiles.map((file) => (
            <div key={file.id} className="flex items-center justify-between p-4 bg-white border border-slate-100 shadow-sm rounded-2xl">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-700 truncate">{file.candidateName}</p>
                <p className="text-xs text-slate-500 truncate">{file.fileName}</p>
              </div>
              <button
                onClick={(event) => {
                  event.stopPropagation();
                  removeResume(file.id);
                }}
                className="text-red-500 hover:text-red-600"
              >
                <XCircle size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      <motion.button
        onClick={handleAnalyzeCandidates}
        disabled={!resumeFiles.length || !jobTitle.trim() || analyzing || isParsingFiles}
        className={`w-full py-5 px-6 font-bold flex items-center justify-center gap-3 btn-primary text-lg ${
          !(resumeFiles.length > 0 && jobTitle.trim() && !analyzing && !isParsingFiles)
            ? 'opacity-50 saturate-0 cursor-not-allowed pointer-events-none'
            : ''
        }`}
        whileHover={resumeFiles.length > 0 && jobTitle.trim() ? { scale: 1.02 } : {}}
        whileTap={resumeFiles.length > 0 && jobTitle.trim() ? { scale: 0.98 } : {}}
      >
        {isParsingFiles ? (
          <>Reading files...</>
        ) : analyzing ? (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity }}
              className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
            />
            Analyzing {resumeFiles.length} candidates...
          </>
        ) : (
          <>
            <Zap size={20} />
            Analyze Candidates
          </>
        )}
      </motion.button>
    </div>
  );

  const renderAnalytics = () => {
    if (!allCandidates.length) {
      return (
        <div className="text-center py-14">
          <FileText className="mx-auto text-slate-300" size={40} />
          <h3 className="mt-3 text-xl font-bold text-slate-800">No analysis results yet</h3>
          <p className="text-sm text-slate-500 mt-1">Upload resumes and run analyzer to see ranked candidates.</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex gap-2 flex-wrap">
          {[
            { value: 'all', label: 'All' },
            { value: 'top', label: 'Top Tier' },
            { value: 'suitable', label: 'Suitable' },
            { value: 'review', label: 'Needs Review' },
          ].map(({ value, label }) => (
            <motion.button
              key={value}
              onClick={() => setFilterTier(value)}
              className={`px-5 py-2.5 rounded-xl font-bold transition-all ${
                filterTier === value
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
              }`}
              whileHover={{ scale: 1.02 }}
            >
              {label}
            </motion.button>
          ))}
        </div>

        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {filteredCandidates.map((candidate, index) => {
            const shortlisted = Boolean(findSavedShortlist(candidate, jobTitle));
            const busy = shortlistBusyKey === shortlistKey(jobTitle, candidate.candidate_name);

            const decisionScore = toSafePercent(candidate.decision_score);
            const riskLevel = candidate.risk_level || 'N/A';

            return (
              <motion.div
                key={candidate.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.04 }}
                onClick={() => setSelectedCandidate(candidate)}
                className={`p-5 cursor-pointer transition-all ${
                  selectedCandidate?.id === candidate.id
                    ? 'glass-panel !border-cyan-400 !shadow-[0_0_15px_rgba(0,194,203,0.3)]'
                    : 'glass-card hover:!border-cyan-300'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-lg text-slate-900 tracking-tight truncate">{candidate.candidate_name}</h4>
                      <span className={`text-xs px-2.5 py-1 rounded-full font-bold ${tierClassMap[candidate.tier] || tierClassMap.review}`}>
                        {candidate.match_label}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-slate-500 mt-0.5">Rank #{candidate.rank} • Core {toSafePercent(candidate.core_match).toFixed(1)}% • Secondary {toSafePercent(candidate.secondary_match).toFixed(1)}%</p>
                    <p className="text-xs text-slate-500 mt-2 truncate">Top strengths: {(candidate.top_strengths || []).slice(0, 3).join(', ') || 'N/A'}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <span className="text-[11px] px-2 py-1 rounded-md bg-cyan-50 text-cyan-700 border border-cyan-100 font-semibold">
                        Decision {decisionScore.toFixed(1)}%
                      </span>
                      <span className={`text-[11px] px-2 py-1 rounded-md border font-semibold ${
                        String(candidate.analysis_mode || analysisMode).toLowerCase() === 'hybrid'
                          ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                          : 'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        Source {String(candidate.analysis_mode || analysisMode).toUpperCase()}
                      </span>
                      <span className="text-[11px] px-2 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                        Risk {riskLevel}
                      </span>
                      <span className="text-[11px] px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-100 font-semibold">
                        Coverage {toSafePercent(candidate.skill_coverage_ratio).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-right ml-3">
                    <div className="text-3xl font-extrabold text-slate-900 tracking-tighter">
                      {toSafePercent(candidate.overall_score).toFixed(1)}<span className="text-xl text-slate-400">%</span>
                    </div>
                    <button
                      onClick={async (event) => {
                        event.stopPropagation();
                        await toggleShortlist(candidate, jobTitle);
                      }}
                      disabled={busy}
                      className={`mt-2 text-xs px-3 py-1.5 rounded-lg font-bold transition-colors ${
                        shortlisted
                          ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      } ${busy ? 'opacity-60 cursor-not-allowed' : ''}`}
                    >
                      {busy ? 'Saving...' : shortlisted ? 'Shortlisted' : 'Add Shortlist'}
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        <motion.button
          onClick={resetAnalysis}
          className="w-full py-4 px-6 rounded-2xl font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-all"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
        >
          Analyze Different Role
        </motion.button>
      </div>
    );
  };

  const renderShortlist = () => {
    if (isLoadingShortlists) {
      return (
        <div className="text-center py-14">
          <Star className="mx-auto text-slate-300" size={40} />
          <h3 className="mt-3 text-xl font-bold text-slate-800">Loading shortlists...</h3>
        </div>
      );
    }

    if (!shortlistedCandidates.length) {
      return (
        <div className="text-center py-14">
          <Star className="mx-auto text-slate-300" size={40} />
          <h3 className="mt-3 text-xl font-bold text-slate-800">No shortlisted candidates</h3>
          <p className="text-sm text-slate-500 mt-1">Use Analytics tab and shortlist candidates to see them here.</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {shortlistedCandidates.map((candidate) => (
          <div key={candidate.id} className="glass-card p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h4 className="text-lg font-bold text-slate-900">{candidate.candidate_name}</h4>
                <p className="text-xs text-slate-500">{candidate.role_title}</p>
                <span className={`inline-flex mt-1 text-[11px] px-2 py-0.5 rounded-md border font-semibold ${
                  String(candidate.analysis_mode || 'esco').toLowerCase() === 'hybrid'
                    ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}>
                  Source {String(candidate.analysis_mode || 'esco').toUpperCase()}
                </span>
                <p className="text-sm text-slate-500">Rank #{candidate.rank ?? '-'} • {(candidate.overall_score ?? 0).toFixed(1)}% • {candidate.match_label || 'Unrated'}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setSelectedCandidate({
                      ...candidate,
                      tier: toTier(candidate.match_label),
                      top_strengths: candidate.top_strengths || [],
                      top_gaps: candidate.top_gaps || [],
                    });
                    setJobTitle(candidate.role_title || jobTitle);
                    setActiveMenu('analytics');
                  }}
                  className="px-3 py-1.5 rounded-lg text-sm bg-slate-100 text-slate-700 hover:bg-slate-200"
                >
                  View Details
                </button>
                <button
                  onClick={async () => {
                    await toggleShortlist(candidate, candidate.role_title);
                  }}
                  className="px-3 py-1.5 rounded-lg text-sm bg-red-50 text-red-600 hover:bg-red-100"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
        ))}

        <button
          onClick={exportShortlistReport}
          className="w-full mt-3 py-3.5 rounded-xl bg-slate-900 text-white font-semibold hover:bg-black transition-colors"
        >
          Export Shortlist CSV
        </button>
      </div>
    );
  };

  const renderReports = () => {
    if (!allCandidates.length) {
      return (
        <div className="text-center py-14">
          <Download className="mx-auto text-slate-300" size={40} />
          <h3 className="mt-3 text-xl font-bold text-slate-800">No report data yet</h3>
          <p className="text-sm text-slate-500 mt-1">Run candidate analysis to unlock export and reporting tools.</p>
        </div>
      );
    }

    return (
      <div className="space-y-5">
        <div className="grid md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <p className="text-xs uppercase tracking-wider text-slate-500">Role</p>
            <p className="text-lg font-bold text-slate-900 mt-1">{jobTitle}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <p className="text-xs uppercase tracking-wider text-slate-500">Candidates</p>
            <p className="text-lg font-bold text-slate-900 mt-1">{allCandidates.length}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <p className="text-xs uppercase tracking-wider text-slate-500">Average Score</p>
            <p className="text-lg font-bold text-slate-900 mt-1">{averageScore}%</p>
          </div>
        </div>

        <div className="space-y-2">
          {allCandidates.slice(0, 5).map((candidate) => (
            <div key={candidate.id} className="flex items-center justify-between px-4 py-3 rounded-xl bg-white border border-slate-200">
              <p className="text-sm font-semibold text-slate-800">#{candidate.rank} {candidate.candidate_name}</p>
              <p className="text-sm text-slate-600">{candidate.overall_score.toFixed(1)}% • {candidate.match_label}</p>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-3">
          <button
            onClick={exportFullReport}
            className="py-3 rounded-xl bg-slate-900 text-white font-semibold hover:bg-black transition-colors"
          >
            Export Full CSV
          </button>
          <button
            onClick={exportShortlistReport}
            disabled={!shortlistedCandidates.length}
            className="py-3 rounded-xl bg-slate-100 text-slate-700 font-semibold hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Export Shortlist
          </button>
          <button
            onClick={copyExecutiveSummary}
            className="py-3 rounded-xl bg-cyan-600 text-white font-semibold hover:bg-cyan-700 transition-colors"
          >
            {reportCopied ? 'Summary Copied' : 'Copy Summary'}
          </button>
        </div>
      </div>
    );
  };

  const renderCenterPanel = () => {
    if (activeMenu === 'analyzer') return renderAnalyzer();
    if (activeMenu === 'analytics') return renderAnalytics();
    if (activeMenu === 'shortlist') return renderShortlist();
    return renderReports();
  };

  const statColorClass = {
    cyan: {
      glow: 'bg-cyan-50',
      box: 'bg-cyan-50 text-cyan-500',
    },
    green: {
      glow: 'bg-green-50',
      box: 'bg-green-50 text-green-500',
    },
    yellow: {
      glow: 'bg-yellow-50',
      box: 'bg-yellow-50 text-yellow-500',
    },
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-50 via-white to-slate-100">
      <Sidebar />

      {/* Mobile Menu Button */}
      <motion.button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-50 p-2 rounded-xl bg-white/80 backdrop-blur-md border border-slate-200 shadow-sm md:hidden text-slate-700"
        whileHover={{ scale: 1.05 }}
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </motion.button>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        />
      )}

      {/* Main Content */}
      <div className="md:ml-64 min-h-screen p-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex justify-between items-start gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
                Welcome, {user?.name || 'Recruiter'}!
              </h1>
              <p className="text-slate-500 font-medium">
                Analyze candidates with live scoring, shortlist management, and reports.
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setActiveMenu('analyzer');
                setSidebarOpen(false);
              }}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40"
            >
              New Analysis
            </motion.button>
          </div>
        </motion.div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          {[
            { icon: Users, label: 'Candidates', value: resumeFiles.length, color: 'cyan' },
            { icon: Zap, label: 'Analyzed', value: allCandidates.length, color: 'cyan' },
            { icon: CheckCircle, label: 'Top Tier', value: topTierCount, color: 'green' },
            { icon: Star, label: 'Shortlisted', value: savedShortlists.length, color: 'yellow' },
          ].map(({ icon: Icon, label, value, color }, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="p-6 rounded-3xl bg-white border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] relative overflow-hidden group"
            >
              {/* Decorative background glow */}
              <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-50 group-hover:opacity-100 transition-opacity ${statColorClass[color]?.glow || statColorClass.cyan.glow}`} />
              
              <div className="flex items-center gap-5 relative z-10">
                <div
                  className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm ${statColorClass[color]?.box || statColorClass.cyan.box}`}
                >
                  <Icon size={26} strokeWidth={2.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-1">{label}</p>
                  <p className="text-3xl font-extrabold text-slate-900 tracking-tight">{value}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm font-medium"
          >
            {error}
          </motion.div>
        )}

        <div className="grid lg:grid-cols-12 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-8 xl:col-span-8"
          >
            <div className="p-8 rounded-[2rem] bg-white/80 backdrop-blur-xl border border-white shadow-[0_8px_30px_rgb(0,0,0,0.06)]">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 mb-8">
                {activeMenu === 'analyzer' && 'Batch Candidate Analysis'}
                {activeMenu === 'analytics' && 'Candidate Analytics'}
                {activeMenu === 'shortlist' && 'Shortlisted Candidates'}
                {activeMenu === 'reports' && 'Reporting Center'}
              </h2>
              {renderCenterPanel()}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-4 xl:col-span-4"
          >
            <div className="p-8 rounded-[2rem] bg-white/80 backdrop-blur-xl border border-white shadow-[0_8px_30px_rgb(0,0,0,0.06)] sticky top-6">
              {selectedCandidate ? (
                <>
                  <h3 className="text-2xl font-bold tracking-tight text-slate-900 mb-6">
                    {selectedCandidate.candidate_name}
                  </h3>

                  <div className="mb-8 p-6 rounded-3xl bg-gradient-to-br from-cyan-400 to-blue-500 text-white relative overflow-hidden shadow-lg shadow-cyan-500/20">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full blur-2xl -mr-10 -mt-10" />
                    <p className="text-cyan-50 font-bold uppercase tracking-wider text-xs mb-1 relative z-10">Overall Match Score</p>
                    <p className="text-5xl font-extrabold tracking-tighter relative z-10">
                      {toSafePercent(selectedCandidate.overall_score).toFixed(1)}<span className="text-2xl opacity-80">%</span>
                    </p>
                    <p className="text-xs font-semibold text-cyan-50/90 mt-2 relative z-10">
                      Decision {toSafePercent(selectedCandidate.decision_score).toFixed(1)}% • Risk {selectedCandidate.risk_level || 'N/A'}
                    </p>
                  </div>

                  <div className="mb-8 p-4 rounded-2xl border border-slate-200 bg-slate-50">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500">Hybrid Diagnostics</h4>
                      <button
                        type="button"
                        onClick={runSelectedCandidateDiagnostics}
                        disabled={analysisMode !== 'hybrid' || diagnosticsBusy}
                        className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {diagnosticsBusy ? 'Running...' : 'Run'}
                      </button>
                    </div>

                    {analysisMode !== 'hybrid' && (
                      <p className="text-xs text-slate-500 mt-2">Available only in Hybrid mode.</p>
                    )}

                    {diagnosticsError && (
                      <p className="text-xs text-red-600 mt-2">{diagnosticsError}</p>
                    )}

                    {diagnosticsResult && (
                      <div className="mt-3 space-y-2 text-xs">
                        <div className="grid grid-cols-3 gap-2">
                          <div className="p-2 rounded-lg bg-white border border-slate-200">
                            <p className="text-slate-500">ESCO</p>
                            <p className="font-bold text-slate-900">{toSafePercent(diagnosticsResult.esco_overall_score).toFixed(1)}%</p>
                          </div>
                          <div className="p-2 rounded-lg bg-white border border-slate-200">
                            <p className="text-slate-500">O*NET</p>
                            <p className="font-bold text-slate-900">{toSafePercent(diagnosticsResult.onet_skill_match_score).toFixed(1)}%</p>
                          </div>
                          <div className="p-2 rounded-lg bg-white border border-slate-200">
                            <p className="text-slate-500">Fused</p>
                            <p className="font-bold text-slate-900">{toSafePercent(diagnosticsResult.fused_score).toFixed(1)}%</p>
                          </div>
                        </div>

                        <p className="text-slate-600">
                          O*NET role: <span className="font-semibold text-slate-800">{diagnosticsResult.onet_matched_role || 'Not matched'}</span>
                        </p>

                        {!!(diagnosticsResult.onet_matched_via_alias || []).length && (
                          <p className="text-slate-600">
                            Alias hits: <span className="font-semibold text-slate-800">{diagnosticsResult.onet_matched_via_alias.slice(0, 5).join(', ')}</span>
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="mb-8 grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                      <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Coverage</p>
                      <p className="text-xl font-extrabold text-slate-900 mt-1">{toSafePercent(selectedCandidate.skill_coverage_ratio).toFixed(1)}%</p>
                    </div>
                    <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                      <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Recommendation</p>
                      <p className="text-sm font-bold text-slate-900 mt-2">{selectedCandidate.recommendation || 'Review'}</p>
                    </div>
                  </div>

                  <div className="mb-8 space-y-3">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500">Breakdown</h4>
                    {[
                      { label: 'Core', value: selectedCandidate.core_match },
                      { label: 'Secondary', value: selectedCandidate.secondary_match },
                      { label: 'Bonus', value: selectedCandidate.bonus_match },
                    ].map((item) => (
                      <div key={item.label}>
                        <div className="flex items-center justify-between text-xs font-semibold text-slate-600 mb-1">
                          <span>{item.label}</span>
                          <span>{toSafePercent(item.value).toFixed(1)}%</span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-cyan-400 to-blue-500" style={{ width: `${toSafePercent(item.value)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mb-8 p-4 rounded-2xl border border-slate-200 bg-slate-50">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">Comprehensive Classification</h4>
                    <div className={`rounded-xl border px-3 py-2 ${selectedCandidateDetails?.classification.toneClass || 'bg-slate-100 border-slate-200 text-slate-700'}`}>
                      <p className="text-sm font-bold">{selectedCandidateDetails?.classification.label || 'Review'}</p>
                      <p className="text-xs mt-1">{selectedCandidateDetails?.classification.summary || 'Classification is based on score quality and risk signals.'}</p>
                    </div>
                    <p className="text-xs text-slate-500 mt-3">{selectedCandidate.recommendation || recommendationFromScore(toSafePercent(selectedCandidate.overall_score))}</p>
                  </div>

                  <div className="mb-8 space-y-4">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500">Skill Classification</h4>

                    <div className="p-4 rounded-2xl bg-white border border-slate-200">
                      <p className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">Core Skills</p>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {(selectedCandidateDetails?.core.matched || []).slice(0, 5).map((skill, i) => (
                          <span key={`core-m-${i}`} className="text-xs font-semibold bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-lg">
                            {skill}
                          </span>
                        ))}
                        {!selectedCandidateDetails?.core.matched?.length && (
                          <span className="text-xs text-slate-500">No direct core strengths detected.</span>
                        )}
                      </div>
                      {!!selectedCandidateDetails?.core.missing?.length && (
                        <p className="text-xs text-amber-700">Missing: {selectedCandidateDetails.core.missing.slice(0, 4).join(', ')}</p>
                      )}
                    </div>

                    <div className="p-4 rounded-2xl bg-white border border-slate-200">
                      <p className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">Language Skills</p>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {(selectedCandidateDetails?.language.matched || []).slice(0, 6).map((skill, i) => (
                          <span key={`lang-m-${i}`} className="text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-lg">
                            {skill}
                          </span>
                        ))}
                        {!selectedCandidateDetails?.language.matched?.length && (
                          <span className="text-xs text-slate-500">Language data appears limited for this resume.</span>
                        )}
                      </div>
                      {!!selectedCandidateDetails?.language.missing?.length && (
                        <p className="text-xs text-amber-700">Missing: {selectedCandidateDetails.language.missing.slice(0, 4).join(', ')}</p>
                      )}
                    </div>

                    <div className="p-4 rounded-2xl bg-white border border-slate-200">
                      <p className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">Other Skills (Tools/Frameworks)</p>
                      <div className="flex flex-wrap gap-2">
                        {(selectedCandidateDetails?.other.matched || []).slice(0, 6).map((skill, i) => (
                          <span key={`other-m-${i}`} className="text-xs font-semibold bg-violet-50 text-violet-700 border border-violet-200 px-2.5 py-1 rounded-lg">
                            {skill}
                          </span>
                        ))}
                        {!selectedCandidateDetails?.other.matched?.length && (
                          <span className="text-xs text-slate-500">No additional tool/framework signals detected.</span>
                        )}
                      </div>
                    </div>

                    {!selectedCandidateDetails?.sourceAvailable && (
                      <p className="text-[11px] text-slate-500">Detailed language/tool classification is stronger when source resume text is available in the current upload session.</p>
                    )}
                  </div>

                  <div className="mb-8">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
                      Top Strengths
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {(selectedCandidate.top_strengths || []).slice(0, 5).map((skill, i) => (
                        <div
                          key={i}
                          className="text-xs font-bold bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-lg flex items-center gap-1"
                        >
                          <CheckCircle size={13} /> {skill}
                        </div>
                      ))}
                      {!selectedCandidate.top_strengths?.length && (
                        <p className="text-xs text-slate-500">No strengths available.</p>
                      )}
                    </div>
                  </div>

                  <div className="mb-8">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">Top Gaps</h4>
                    <div className="flex flex-wrap gap-2">
                      {(selectedCandidate.top_gaps || []).slice(0, 5).map((skill, i) => (
                        <div
                          key={i}
                          className="text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1.5 rounded-lg flex items-center gap-1"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> {skill}
                        </div>
                      ))}
                      {!selectedCandidate.top_gaps?.length && (
                        <p className="text-xs text-slate-500">No major gaps detected.</p>
                      )}
                    </div>
                  </div>

                  <div className="mb-8 p-4 rounded-2xl bg-blue-50 border border-blue-100">
                    <p className="text-sm text-blue-800 font-medium">
                      <strong className="block text-xs uppercase tracking-wider text-blue-600 mb-1">Recommendation</strong>
                      {recommendationFromScore(toSafePercent(selectedCandidate.overall_score))}
                    </p>
                  </div>

                  <div className="space-y-3">
                    <motion.button
                      onClick={async () => {
                        await toggleShortlist(selectedCandidate, selectedCandidate.role_title || jobTitle);
                      }}
                      className="w-full py-3.5 px-4 rounded-xl font-bold bg-slate-900 text-white shadow-lg hover:shadow-xl hover:bg-black transition-all flex items-center justify-center gap-2"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Star size={18} /> {findSavedShortlist(selectedCandidate, selectedCandidate.role_title || jobTitle) ? 'Remove from Shortlist' : 'Shortlist Candidate'}
                    </motion.button>
                    <motion.button
                      onClick={copyExecutiveSummary}
                      className="w-full py-3.5 px-4 rounded-xl font-bold bg-white border-2 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all flex items-center justify-center gap-2"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Clipboard size={18} /> Copy Report Summary
                    </motion.button>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                  <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-6">
                    <Users size={32} className="text-slate-300" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-800 mb-2">No Selection</h3>
                  <p className="text-sm font-medium text-slate-500">
                    Run analysis and select a candidate<br/>to view detailed insights.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default RecruiterDashboard;
