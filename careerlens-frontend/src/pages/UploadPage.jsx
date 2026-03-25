/* ═══════════════════════════════════════════════════════════════════
   Upload Page — Resume upload + role selection → analyze flow
   ═══════════════════════════════════════════════════════════════════ */

import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { analyzeWithRoadmap, parseFileToText, searchOccupations } from '../services/api';
import { parseResumeText } from '../services/resumeParser';
import { LogoIcon } from '../components/Logo';

const ACCEPTED = '.txt,.text,.pdf,.docx,.doc';
const ANALYSIS_MODE_OPTIONS = [
  { id: 'esco', label: 'ESCO' },
  { id: 'hybrid', label: 'Hybrid' },
];

export default function UploadPage() {
  /* ── State ────────────────────────────────────────────────────── */
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [analysisMode, setAnalysisMode] = useState('esco');
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const fileInputRef = useRef(null);
  const debounceRef = useRef(null);
  const suggestionsRef = useRef(null);
  const navigate = useNavigate();

  /* ── Role autocomplete (debounced 300ms) ──────────────────────── */
  const fetchSuggestions = useCallback(async (query) => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    try {
      const results = await searchOccupations(query, 8, analysisMode);
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
      setActiveSuggestion(-1);
    } catch {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [analysisMode]);

  const handleRoleChange = (e) => {
    const value = e.target.value;
    setTargetRole(value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 300);
  };

  const selectSuggestion = (label) => {
    setTargetRole(label);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleRoleKeyDown = (e) => {
    if (!showSuggestions) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveSuggestion((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && activeSuggestion >= 0) {
      e.preventDefault();
      selectSuggestion(suggestions[activeSuggestion].preferred_label);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  /* Close dropdown when clicking outside */
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /* ── File handling ────────────────────────────────────────────── */
  const handleFile = async (file) => {
    if (!file) return;
    setError('');
    setFileName(file.name);
    try {
      setLoadingMsg('Reading file...');
      const text = await parseFileToText(file);
      if (!text || text.trim().length < 20) {
        throw new Error('Could not extract meaningful text from file. Try pasting manually.');
      }
      setResumeText(text);
    } catch (err) {
      setError(err.message);
      setResumeText('');
      setFileName('');
    } finally {
      setLoadingMsg('');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const clearResume = () => {
    setResumeText('');
    setFileName('');
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  /* ── Submit ───────────────────────────────────────────────────── */
  const handleAnalyze = async () => {
    if (!resumeText.trim()) {
      setError('Please upload a resume file or paste your resume text.');
      return;
    }
    if (!targetRole.trim()) {
      setError('Please enter a target role.');
      return;
    }
    if (resumeText.trim().length < 20) {
      setError('Resume text is too short. Please provide more content.');
      return;
    }

    setError('');
    setIsLoading(true);
    setLoadingMsg('Analyzing your resume...');

    try {
      const data = await analyzeWithRoadmap(resumeText, targetRole.trim(), analysisMode);

      // Extract candidate profile from resume text
      setLoadingMsg('Extracting profile...');
      try {
        const candidate = parseResumeText(resumeText);
        if (candidate) {
          data.candidate = candidate;
        }
      } catch (parseErr) {
        console.warn('Resume parsing failed (non-critical):', parseErr);
        // Continue without candidate data — results page handles this gracefully
      }

      sessionStorage.setItem('analysisResult', JSON.stringify(data));
      setLoadingMsg('Done! Redirecting...');
      // small delay so user sees "Done"
      await new Promise((r) => setTimeout(r, 400));
      navigate('/results');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
      setLoadingMsg('');
    }
  };

  /* ── Render ───────────────────────────────────────────────────── */
  return (
    <div className="min-h-screen pt-28 pb-20">
      {/* Background blob */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        <div className="absolute rounded-full blur-3xl opacity-18"
          style={{ width: 500, height: 500, top: '20%', left: '50%', transform: 'translateX(-50%)',
            background: 'radial-gradient(circle, rgba(0,194,203,0.18) 0%, transparent 70%)' }}
        />
      </div>

      {/* ── Full-screen loading overlay ─────────────────────────── */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            key="loader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex flex-col items-center justify-center backdrop-blur-sm"
            style={{ background: 'rgba(246,247,251,0.85)' }}
          >
            {/* Brand icon with spinning ring */}
            <div className="relative mb-6 flex items-center justify-center">
              <div className="rounded-full border-4 border-surface-alt" style={{ width: 'clamp(80px, 20vw, 96px)', height: 'clamp(80px, 20vw, 96px)' }} />
              <div className="absolute rounded-full border-4 border-transparent animate-spin" style={{ inset: 0, width: 'clamp(80px, 20vw, 96px)', height: 'clamp(80px, 20vw, 96px)', borderTopColor: '#00C2CB' }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <LogoIcon size={40} />
              </div>
            </div>
            <p className="text-lg font-semibold text-ink" style={{ fontFamily: 'var(--font-display)' }}>
              {loadingMsg}
            </p>
            <p className="text-sm text-ink-muted mt-2">This may take a few seconds...</p>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="section-container relative" style={{ zIndex: 1 }}>
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
          className="max-w-2xl mx-auto"
        >
          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-ink tracking-tight mb-3"
              style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'clamp(1.75rem, 3vw, 2.5rem)' }}>
              Analyze Your Resume
            </h1>
            <p className="text-ink-secondary">
              Upload a <strong>.pdf</strong>, <strong>.docx</strong>, or <strong>.txt</strong> file — or paste your resume text directly.
            </p>
          </div>

          {/* Glass Card */}
          <div className="glass-card p-8 flex flex-col gap-6">

            {/* ── Drop Zone ─────────────────────────────────────── */}
            <div
              className={`
                relative rounded-xl border-2 border-dashed transition-all duration-300 cursor-pointer
                ${isDragging
                  ? 'border-primary bg-primary/5 shadow-[0_0_30px_var(--color-primary-glow)]'
                  : 'border-surface-alt hover:border-ink-muted'}
              `}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => !resumeText && fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                accept={ACCEPTED}
                className="hidden"
                onChange={(e) => handleFile(e.target.files[0])}
              />

              {resumeText ? (
                /* Show loaded text */
                <div className="relative">
                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    className="w-full h-52 p-4 bg-transparent text-sm text-ink resize-none focus:outline-none"
                    style={{ fontFamily: 'var(--font-body)' }}
                  />
                  {/* File badge */}
                  {fileName && (
                    <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-success/10 text-success text-xs font-medium">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      {fileName}
                    </div>
                  )}
                </div>
              ) : (
                /* Upload prompt */
                <div className="flex flex-col items-center justify-center py-16 text-ink-muted">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-3 text-ink-muted">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <p className="text-sm font-medium">Drop your resume here or click to upload</p>
                  <p className="text-xs mt-1">.pdf, .docx, .txt supported</p>
                </div>
              )}
            </div>

            {/* Clear button */}
            {resumeText && (
              <button onClick={clearResume}
                className="self-end text-xs text-ink-muted hover:text-danger transition-colors">
                Clear resume
              </button>
            )}

            {/* ── Role Input with Autocomplete ──────────────────── */}
            <div className="flex flex-col gap-2 relative" ref={suggestionsRef}>
              <label className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Target Role
              </label>
              <input
                type="text"
                value={targetRole}
                onChange={handleRoleChange}
                onKeyDown={handleRoleKeyDown}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                placeholder="e.g. software developer, data analyst, marketing manager"
                autoComplete="off"
                className="w-full px-4 py-3 rounded-xl bg-surface border border-surface-alt text-ink text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                style={{ fontFamily: 'var(--font-body)' }}
              />

              {/* Suggestions dropdown */}
              <AnimatePresence>
                {showSuggestions && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.15 }}
                    className="absolute top-full left-0 right-0 mt-1 z-50 rounded-xl bg-surface border border-surface-alt shadow-xl overflow-hidden"
                  >
                    {suggestions.map((item, i) => (
                      <button
                        key={item.esco_id || i}
                        type="button"
                        onClick={() => selectSuggestion(item.preferred_label)}
                        className={`
                          w-full text-left px-4 py-2.5 flex flex-col gap-0.5 transition-colors
                          ${i === activeSuggestion ? 'bg-primary/8' : 'hover:bg-surface-alt/60'}
                          ${i > 0 ? 'border-t border-surface-alt/50' : ''}
                        `}
                      >
                        <span className="text-sm text-ink font-medium">{item.preferred_label}</span>
                        {item.description && (
                          <span className="text-xs text-ink-muted line-clamp-1">{item.description}</span>
                        )}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Analysis Mode
              </label>
              <div className="inline-flex rounded-xl border border-surface-alt bg-surface p-1 w-fit">
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

            {/* ── Error ─────────────────────────────────────────── */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="flex items-start gap-2 p-3 rounded-xl bg-danger/5 border border-danger/20">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0 mt-0.5">
                      <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
                    </svg>
                    <p className="text-sm text-danger">{error}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Analyze Button ─────────────────────────────────── */}
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !resumeText.trim() || !targetRole.trim()}
              className="btn-primary w-full !py-4 !text-base disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                    <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" className="opacity-75" />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  Analyze Resume
                </span>
              )}
            </button>
          </div>

          {/* ── Tips ──────────────────────────────────────────────── */}
          <div className="mt-6 grid grid-cols-3 gap-4 text-center">
            {[
              { icon: '📄', text: 'Upload PDF, DOCX, or TXT' },
              { icon: '🎯', text: 'Enter exact role name' },
              { icon: '⚡', text: 'Results in seconds' },
            ].map((tip, i) => (
              <motion.div
                key={i}
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex flex-col items-center gap-1 text-ink-muted"
              >
                <span className="text-lg">{tip.icon}</span>
                <span className="text-xs">{tip.text}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="noise-overlay" />
    </div>
  );
}
