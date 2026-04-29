import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import {
  LogOut, Upload, BarChart3, Lightbulb,
  FileText, TrendingUp, Target, CheckCircle, AlertCircle, CalendarDays,
  SendHorizontal, Menu, X
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  analyzeWithRoadmap,
  chatWithCareerBot,
  getDashboardState,
  parseFileToText,
  saveDashboardState,
  searchOccupations,
} from '../../services/api';
import { parseResumeText } from '../../services/resumeParser';
import Logo from '../../components/Logo';

const LANGUAGE_PATTERNS = [
  { label: 'Python', regex: /\bpython\b/i },
  { label: 'JavaScript', regex: /\bjavascript\b|\bjs\b/i },
  { label: 'TypeScript', regex: /\btypescript\b|\bts\b/i },
  { label: 'Java', regex: /\bjava\b/i },
  { label: 'C++', regex: /\bc\+\+\b|\bcpp\b/i },
  { label: 'C#', regex: /\bc#\b|\bc sharp\b/i },
  { label: 'SQL', regex: /\bsql\b|\bpostgresql\b|\bmysql\b/i },
  { label: 'R', regex: /\br\b programming|\blanguage r\b/i },
  { label: 'Go', regex: /\bgolang\b|\bgo\b language/i },
  { label: 'Rust', regex: /\brust\b/i },
  { label: 'PHP', regex: /\bphp\b/i },
  { label: 'Swift', regex: /\bswift\b/i },
  { label: 'Kotlin', regex: /\bkotlin\b/i },
  { label: 'Scala', regex: /\bscala\b/i },
  { label: 'HTML/CSS', regex: /\bhtml\b|\bcss\b/i },
];

const uniqueByLower = (items) => {
  const seen = new Set();
  const result = [];

  (items || []).forEach((item) => {
    const text = String(item || '').trim();
    const key = text.toLowerCase();
    if (!text || seen.has(key)) {
      return;
    }
    seen.add(key);
    result.push(text);
  });

  return result;
};

const extractLanguages = (items, maxItems = 8) => {
  const found = [];
  const textItems = uniqueByLower(items);

  textItems.forEach((item) => {
    LANGUAGE_PATTERNS.forEach(({ label, regex }) => {
      if (regex.test(item)) {
        found.push(label);
      }
    });
  });

  return uniqueByLower(found).slice(0, maxItems);
};

const extractKeySkills = (items, maxItems = 10) => {
  const unique = uniqueByLower(items);
  const languageSet = new Set(extractLanguages(unique, 30).map((lang) => lang.toLowerCase()));

  return unique.filter((skill) => !languageSet.has(skill.toLowerCase())).slice(0, maxItems);
};

const parseDurationRange = (duration, fallbackStart = 1, fallbackEnd = 1) => {
  const text = String(duration || '').trim();
  const match = text.match(/months?\s*(\d+)\s*[-–]\s*(\d+)/i);

  if (match) {
    const start = Number(match[1]);
    const end = Number(match[2]);
    if (Number.isFinite(start) && Number.isFinite(end) && start > 0 && end >= start) {
      return { start, end };
    }
  }

  return { start: fallbackStart, end: fallbackEnd };
};

const parseActionMonthRange = (actionText) => {
  const text = String(actionText || '').trim();
  const match = text.match(/months?\s*(\d+)\s*[-–]\s*(\d+)/i);
  if (!match) {
    return null;
  }

  const start = Number(match[1]);
  const end = Number(match[2]);
  if (!Number.isFinite(start) || !Number.isFinite(end) || start <= 0 || end < start) {
    return null;
  }

  return { start, end };
};

const pickMonthlyActions = (actions, month, phaseStart, phaseEnd) => {
  const cleanActions = (actions || []).map((a) => String(a).trim()).filter(Boolean);
  if (cleanActions.length === 0) {
    return [];
  }

  const byRange = cleanActions.filter((action) => {
    const range = parseActionMonthRange(action);
    return range ? month >= range.start && month <= range.end : false;
  });

  if (byRange.length > 0) {
    return byRange;
  }

  const phaseSpan = Math.max(phaseEnd - phaseStart + 1, 1);
  const progress = Math.min(Math.max((month - phaseStart) / phaseSpan, 0), 0.999);
  const idx = Math.floor(progress * cleanActions.length);
  return [cleanActions[Math.min(idx, cleanActions.length - 1)]];
};

const pickMonthlySlice = (items, month, phaseStart, phaseEnd, maxItems = 3) => {
  const cleanItems = (items || []).map((i) => String(i).trim()).filter(Boolean);
  if (cleanItems.length <= maxItems) {
    return cleanItems;
  }

  const phaseSpan = Math.max(phaseEnd - phaseStart + 1, 1);
  const chunkSize = Math.max(1, Math.ceil(cleanItems.length / phaseSpan));
  const offset = Math.max(0, (month - phaseStart) * chunkSize);
  const picked = cleanItems.slice(offset, offset + maxItems);
  if (picked.length > 0) {
    return picked;
  }

  return cleanItems.slice(0, maxItems);
};

const buildMonthWisePlan = (roadmap) => {
  const phases = roadmap?.phases || [];
  if (phases.length === 0) {
    return [];
  }

  const totalMonths = Math.max(Number(roadmap?.timeline_months) || phases.length * 4, 1);
  const fallbackSpan = Math.max(Math.floor(totalMonths / phases.length), 1);

  let fallbackStart = 1;
  const monthRows = [];

  phases.forEach((phase, index) => {
    const fallbackEnd = index === phases.length - 1
      ? totalMonths
      : Math.min(totalMonths, fallbackStart + fallbackSpan - 1);

    const { start, end } = parseDurationRange(phase.duration, fallbackStart, fallbackEnd);

    for (let month = start; month <= end; month += 1) {
      const monthlyActions = pickMonthlyActions(phase.suggested_actions || [], month, start, end);
      const activeRange = parseActionMonthRange(monthlyActions[0]);

      monthRows.push({
        id: `month-${month}`,
        month,
        phaseNumber: phase.phase,
        phaseTitle: phase.title,
        duration: phase.duration,
        monthWindow: activeRange ? `Months ${activeRange.start}-${activeRange.end}` : `Month ${month}`,
        focusArea: phase.focus_area,
        description: phase.enhanced_description || phase.title,
        skills: pickMonthlySlice(phase.skills_to_learn || [], month, start, end, 4),
        actions: monthlyActions.slice(0, 3),
        objectives: pickMonthlySlice(phase.learning_objectives || [], month, start, end, 3),
        resources: pickMonthlySlice(phase.recommended_resources || [], month, start, end, 3),
      });
    }

    fallbackStart = fallbackEnd + 1;
  });

  return monthRows.sort((a, b) => a.month - b.month);
};

const BotMascotAnimation = ({ compact = false }) => {
  const sizeWrap = compact ? 'w-10 h-10' : 'w-24 h-24';
  const headSize = compact ? 'w-7 h-5.5' : 'w-16 h-12';
  const bodySize = compact ? 'w-5 h-6' : 'w-12 h-14';
  const bubbleOffset = compact ? '-top-5 -left-4' : '-top-10 -left-8';
  const antennaH = compact ? 'h-1.5' : 'h-2.5';
  const sparkY = compact ? '-top-2' : '-top-3';

  return (
    <motion.div
      className={`relative ${sizeWrap} flex items-center justify-center drop-shadow-md`}
      animate={{ y: [0, -6, 0] }}
      transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
    >
      {/* Glowing Backdrop */}
      <div className="absolute inset-0 rounded-full bg-cyan-500/10 blur-xl animate-pulse" />

      {/* Bubble */}
      <motion.div
        className={`absolute ${bubbleOffset} rounded-2xl rounded-bl-sm bg-gradient-to-r from-cyan-600 to-blue-600 px-2.5 py-1 text-[10px] font-bold text-white shadow z-[60] shrink-0 whitespace-nowrap`}
        animate={{ scale: [0.95, 1.05, 0.95], rotate: [-1, 1, -1] }}
        transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
      >
        Hello! 👋
      </motion.div>

      {/* Head */}
      <motion.div
        className={`absolute z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-[65%] ${headSize} rounded-[0.4rem] sm:rounded-2xl bg-gradient-to-br from-cyan-400 via-blue-500 to-blue-600 shadow-inner`}
      >
        {/* Face Screen */}
        <div className="absolute top-[35%] left-1/2 -translate-x-1/2 w-[80%] h-[45%] rounded-[0.2rem] sm:rounded-xl bg-slate-900 flex items-center justify-center gap-[15%] shadow-inner border border-white/20">
          <motion.span
            className={`${compact ? 'w-1 h-1' : 'w-2 h-2'} rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.9)]`}
            animate={{ scaleY: [1, 0.1, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', times: [0, 0.05, 0.1] }}
          />
          <motion.span
            className={`${compact ? 'w-1 h-1' : 'w-2 h-2'} rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.9)]`}
            animate={{ scaleY: [1, 0.1, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', times: [0, 0.05, 0.1] }}
          />
        </div>
        {/* Antenna */}
        <div className={`absolute -top-1 left-1/2 -translate-x-1/2 w-[2px] ${antennaH} rounded-t-full bg-cyan-200`} />
        <motion.div 
          className={`absolute ${sparkY} left-1/2 -translate-x-1/2 ${compact ? 'w-1.5 h-1.5' : 'w-2 h-2'} rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(34,211,238,0.9)]`} 
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      </motion.div>

      {/* Body */}
      <motion.div
        className={`absolute bottom-[10%] left-1/2 -translate-x-1/2 ${bodySize} rounded-[0.4rem] rounded-b-xl sm:rounded-2xl sm:rounded-b-3xl bg-gradient-to-br from-cyan-500 to-blue-700 shadow-md`}
      >
        <div className="absolute top-1 left-1/2 -translate-x-1/2 w-[40%] h-[1px] sm:h-1 rounded-full bg-white/20" />
      </motion.div>
    </motion.div>
  );
};

const BotAvatarBadge = ({ size = 'md' }) => {
  const avatarSize = size === 'sm' ? 'w-8 h-8' : 'w-10 h-10';
  const eyeSize = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2';

  return (
    <div className="relative inline-flex items-center justify-center shrink-0">
      {/* Outer pulsing glow */}
      <div className="absolute inset-0 rounded-full animate-ping bg-cyan-400 opacity-20 duration-1000" />
      {/* Main badge */}
      <div
        className={`relative ${avatarSize} flex-shrink-0 z-10 rounded-full border-[2.5px] border-cyan-100 bg-gradient-to-br from-cyan-400 to-blue-600 shadow-md flex items-center justify-center overflow-hidden`}
        aria-label="FutureFit AI avatar"
      >
        {/* Face background */}
        <div className="w-[75%] h-[55%] rounded-full bg-slate-900/40 backdrop-blur-sm flex flex-col items-center justify-center shadow-inner pt-0.5">
          <div className="flex items-center justify-center gap-[15%]">
            <span className={`${eyeSize} rounded-full bg-cyan-200 animate-pulse shadow-[0_0_4px_rgba(165,243,252,0.8)]`} />
            <span className={`${eyeSize} rounded-full bg-cyan-200 animate-pulse shadow-[0_0_4px_rgba(165,243,252,0.8)]`} />
          </div>
          {/* Subtle smile */}
          <div className="w-2 h-0.5 border-b-[1.5px] border-cyan-100 rounded-full mt-[2px]" />
        </div>
      </div>
    </div>
  );
};

const AnimatedScore = ({ value, duration = 1.2 }) => {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const target = Number(value) || 0;
    const start = performance.now();
    let frame;

    const tick = (now) => {
      const progress = Math.min((now - start) / (duration * 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(target * eased * 10) / 10);
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return <>{display.toFixed(1)}</>;
};

const ScoreRing = ({ score, size = 180 }) => {
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, Number(score) || 0));
  const offset = circumference - (pct / 100) * circumference;
  const color = pct >= 75 ? '#16a34a' : pct >= 50 ? '#0891b2' : '#ea580c';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute text-center">
        <p className="text-3xl font-bold text-gray-900">
          <AnimatedScore value={pct} />%
        </p>
        <p className="text-xs uppercase tracking-wider text-gray-500">Overall Match</p>
      </div>
    </div>
  );
};

const StatPill = ({ label, value, tone = 'neutral' }) => {
  const toneClasses = {
    neutral: 'text-gray-900 bg-gray-50 border-gray-200',
    cyan: 'text-cyan-700 bg-cyan-50 border-cyan-200',
    green: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    amber: 'text-amber-700 bg-amber-50 border-amber-200',
  };

  return (
    <div className={`rounded-xl border px-4 py-3 text-center ${toneClasses[tone] || toneClasses.neutral}`}>
      <p className="text-xl font-bold">{value}</p>
      <p className="text-[11px] uppercase tracking-wider">{label}</p>
    </div>
  );
};

const SkillRadar = ({ corePct, secondaryPct, bonusPct }) => {
  const data = [
    { category: 'Core Skills', value: corePct },
    { category: 'Secondary', value: secondaryPct },
    { category: 'Bonus Tools', value: bonusPct },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="category" tick={{ fontSize: 12, fill: '#6b7280' }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
        <Radar name="Match %" dataKey="value" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
      </RadarChart>
    </ResponsiveContainer>
  );
};

const STUDENT_DASHBOARD_STORAGE_KEY = 'careerlens_student_dashboard_v1';
const ANALYSIS_MODE_OPTIONS = [
  { id: 'esco', label: 'ESCO' },
  { id: 'hybrid', label: 'Hybrid' },
];

const StudentDashboard = () => {
  const navigate = useNavigate();
  const { user, logout, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('resume');

  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [targetRole, setTargetRole] = useState('');
  const [analysisMode, setAnalysisMode] = useState('esco');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [error, setError] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [selectedMonthId, setSelectedMonthId] = useState(null);
  const [botMessages, setBotMessages] = useState([
    {
      role: 'assistant',
      content: 'I am FutureFit AI. I can help with resume strategy, roadmap steps, and recruiter-style interview prep.',
      action_items: [],
      suggested_prompts: [
        'Give me a 7-day plan from my roadmap',
        'Which missing skill should I learn first?',
        'Generate interview questions for my weak areas',
      ],
    },
  ]);
  const [botInput, setBotInput] = useState('');
  const [botError, setBotError] = useState('');
  const [isBotLoading, setIsBotLoading] = useState(false);
  const [isBotOpen, setIsBotOpen] = useState(false);
  const [isStateHydrated, setIsStateHydrated] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);

  const fileInputRef = useRef(null);
  const debounceRef = useRef(null);
  const suggestionsRef = useRef(null);
  const botScrollRef = useRef(null);
  const saveTimerRef = useRef(null);

  const storageKey = useMemo(() => {
    const identity = user?.id || user?.email || 'anonymous';
    return `${STUDENT_DASHBOARD_STORAGE_KEY}:${identity}`;
  }, [user?.id, user?.email]);

  useEffect(() => {
    if (!user) {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      let hasRemoteState = false;

      try {
        const remote = await getDashboardState('student');
        const saved = remote?.state || {};

        if (saved && Object.keys(saved).length > 0) {
          hasRemoteState = true;
          if (typeof saved.activeTab === 'string') {
            setActiveTab(saved.activeTab);
          }
          if (typeof saved.resumeText === 'string') {
            setResumeText(saved.resumeText);
          }
          if (typeof saved.fileName === 'string') {
            setFileName(saved.fileName);
          }
          if (typeof saved.targetRole === 'string') {
            setTargetRole(saved.targetRole);
          }
          if (typeof saved.analysisMode === 'string') {
            setAnalysisMode(saved.analysisMode === 'hybrid' ? 'hybrid' : 'esco');
          }
          if (saved.analysisData && typeof saved.analysisData === 'object') {
            setAnalysisData(saved.analysisData);
          }
          if (typeof saved.selectedMonthId === 'string' || saved.selectedMonthId === null) {
            setSelectedMonthId(saved.selectedMonthId);
          }
          if (typeof saved.isBotOpen === 'boolean') {
            setIsBotOpen(saved.isBotOpen);
          }
        }
      } catch {
        // Ignore backend hydration failures and try local fallback.
      }

      if (!hasRemoteState) {
        try {
          const raw = localStorage.getItem(storageKey);
          if (raw) {
            const saved = JSON.parse(raw);
            if (typeof saved.activeTab === 'string') {
              setActiveTab(saved.activeTab);
            }
            if (typeof saved.resumeText === 'string') {
              setResumeText(saved.resumeText);
            }
            if (typeof saved.fileName === 'string') {
              setFileName(saved.fileName);
            }
            if (typeof saved.targetRole === 'string') {
              setTargetRole(saved.targetRole);
            }
            if (typeof saved.analysisMode === 'string') {
              setAnalysisMode(saved.analysisMode === 'hybrid' ? 'hybrid' : 'esco');
            }
            if (saved.analysisData && typeof saved.analysisData === 'object') {
              setAnalysisData(saved.analysisData);
            }
            if (typeof saved.selectedMonthId === 'string' || saved.selectedMonthId === null) {
              setSelectedMonthId(saved.selectedMonthId);
            }
            if (typeof saved.isBotOpen === 'boolean') {
              setIsBotOpen(saved.isBotOpen);
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
  }, [storageKey, user]);

  useEffect(() => {
    if (!isStateHydrated || !user) {
      return;
    }

    const snapshot = {
      activeTab,
      resumeText,
      fileName,
      targetRole,
      analysisMode,
      analysisData,
      selectedMonthId,
      isBotOpen,
      savedAt: Date.now(),
    };

    try {
      localStorage.setItem(storageKey, JSON.stringify(snapshot));
    } catch {
      // Ignore local fallback storage errors.
    }

    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      saveDashboardState('student', snapshot).catch(() => {
        // Ignore transient backend persistence errors.
      });
    }, 700);

    return () => clearTimeout(saveTimerRef.current);
  }, [
    isStateHydrated,
    user,
    storageKey,
    activeTab,
    resumeText,
    fileName,
    targetRole,
    analysisMode,
    analysisData,
    selectedMonthId,
    isBotOpen,
  ]);

  const handleLogout = async () => {
    const result = await logout();
    if (result.success) {
      navigate('/', { replace: true });
      window.scrollTo({ top: 0, behavior: 'auto' });
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

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

  useEffect(() => {
    setSuggestions([]);
    setShowSuggestions(false);
    setActiveSuggestion(-1);
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
    if (!showSuggestions) {
      return;
    }

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

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      clearTimeout(debounceRef.current);
    };
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  };

  const handleFile = async (file) => {
    if (!file) {
      return;
    }

    setError('');
    setFileName(file.name);

    try {
      setLoadingMsg('Reading resume...');
      const text = await parseFileToText(file);
      if (!text || text.trim().length < 20) {
        throw new Error('Could not extract meaningful text from this file. Try another file or paste text manually.');
      }
      setResumeText(text);
    } catch (err) {
      setError(err.message || 'Failed to read file.');
      setResumeText('');
      setFileName('');
    } finally {
      setLoadingMsg('');
    }
  };

  const clearResume = () => {
    setResumeText('');
    setFileName('');
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyze = async () => {
    if (!resumeText.trim()) {
      setError('Please upload a resume or paste resume text.');
      return;
    }

    if (!targetRole.trim()) {
      setError('Please enter a target role.');
      return;
    }

    if (resumeText.trim().length < 20) {
      setError('Resume text is too short. Please provide more detail.');
      return;
    }

    setError('');
    setIsAnalyzing(true);
    setLoadingMsg('Analyzing your resume...');

    try {
      const data = await analyzeWithRoadmap(resumeText, targetRole.trim(), analysisMode);

      // Candidate extraction is best-effort and should never block analysis.
      try {
        const candidate = parseResumeText(resumeText);
        if (candidate) {
          data.candidate = candidate;
        }
      } catch {
        // ignore parser failures
      }

      setAnalysisData(data);
      setActiveTab('results');
    } catch (err) {
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
      setLoadingMsg('');
    }
  };

  const buildBotContext = useCallback(() => {
    if (!analysisData) {
      return null;
    }
    return {
      analysis: analysisData.analysis || null,
      roadmap: analysisData.roadmap || null,
    };
  }, [analysisData]);

  const sendBotMessage = useCallback(async (rawMessage) => {
    const message = String(rawMessage || '').trim();
    if (!message || isBotLoading) {
      return;
    }

    setBotError('');
    setIsBotLoading(true);

    const userMessage = { role: 'user', content: message };
    setBotMessages((prev) => [...prev, userMessage]);

    try {
      const history = [...botMessages, userMessage]
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .slice(-12)
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await chatWithCareerBot(
        message,
        history,
        buildBotContext(),
      );

      setBotMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.reply,
          action_items: response.action_items || [],
          suggested_prompts: response.suggested_prompts || [],
          source: response.source || 'fallback',
          intent: response.intent || 'general',
        },
      ]);
    } catch (err) {
      setBotError(err.message || 'Bot is temporarily unavailable. Please try again.');
      setBotMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I am temporarily unavailable, but I can still help: focus on one missing skill this week and ship one small project artifact.',
          action_items: [
            'Pick one high-priority missing skill and complete one guided module.',
            'Build one mini-project and add it to your portfolio.',
            'Update resume bullets with measurable outcomes.',
          ],
          suggested_prompts: [
            'Give me a 7-day plan',
            'What should I study first?',
            'How do I improve my resume bullets?',
          ],
          source: 'fallback',
          intent: 'general',
        },
      ]);
    } finally {
      setIsBotLoading(false);
      setBotInput('');
    }
  }, [analysisData, botMessages, buildBotContext, isBotLoading]);

  const handleBotSubmit = async (e) => {
    e.preventDefault();
    await sendBotMessage(botInput);
  };

  useEffect(() => {
    if (botScrollRef.current) {
      botScrollRef.current.scrollTop = botScrollRef.current.scrollHeight;
    }
  }, [botMessages, isBotLoading]);

  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsSidebarOpen(false);
        setIsBotOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  // Navigation items
  const navItems = [
    { id: 'resume', label: 'Resume', icon: FileText },
    { id: 'results', label: 'Results', icon: Target },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'roadmap', label: 'Roadmap', icon: TrendingUp },
    { id: 'tips', label: 'Tips', icon: Lightbulb },
  ];

  const analysis = analysisData?.analysis;
  const resultSourceMode = analysis?.hybrid_meta?.onet ? 'hybrid' : 'esco';
  const roadmap = analysisData?.roadmap;
  const matchedSkills = analysis?.matched_skills || [];
  const missingSkills = analysis?.missing_skills || [];
  const skillConfidence = analysis?.skill_confidence || [];
  const improvementPriority = analysis?.improvement_priority || [];

  const monthWisePlan = useMemo(() => buildMonthWisePlan(roadmap), [roadmap]);
  const selectedMonth = monthWisePlan.find((item) => item.id === selectedMonthId) || monthWisePlan[0] || null;
  const roadmapSkillPool = useMemo(() => {
    const phaseSkills = (roadmap?.phases || []).flatMap((phase) => phase.skills_to_learn || []);
    return uniqueByLower([...phaseSkills, ...matchedSkills, ...missingSkills]);
  }, [roadmap, matchedSkills, missingSkills]);
  const roadmapKeySkills = useMemo(() => extractKeySkills(roadmapSkillPool, 10), [roadmapSkillPool]);
  const roadmapLanguages = useMemo(() => extractLanguages(roadmapSkillPool, 8), [roadmapSkillPool]);
  const selectedMonthLanguages = useMemo(
    () => extractLanguages([...(selectedMonth?.skills || []), ...(selectedMonth?.actions || [])], 6),
    [selectedMonth],
  );
  const llmInsights = analysis?.llm_insights || null;
  const analyticsSummary = llmInsights?.analytics_summary || analysis?.analysis_summary || '';
  const llmTips = llmInsights?.tips || [];
  const llmPriorityActions = llmInsights?.priority_actions || [];

  useEffect(() => {
    if (!monthWisePlan.length) {
      setSelectedMonthId(null);
      return;
    }

    if (!monthWisePlan.some((item) => item.id === selectedMonthId)) {
      setSelectedMonthId(monthWisePlan[0].id);
    }
  }, [monthWisePlan, selectedMonthId]);

  const renderResumeTab = () => (
    <motion.div
      key="resume"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 gap-6 lg:grid-cols-3 lg:gap-8"
    >
      <div className="col-span-2 glass-panel p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Resume Analyzer</h2>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !resumeText && fileInputRef.current?.click()}
          className={`rounded-xl border-2 border-dashed p-8 text-center transition-all duration-300 cursor-pointer ${
            isDragging
              ? 'border-cyan-500 bg-cyan-50'
              : 'border-gray-300 bg-gray-50 hover:border-cyan-400'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.text,.pdf,.docx,.doc"
            onChange={(e) => handleFile(e.target.files?.[0])}
            className="hidden"
          />

          {resumeText ? (
            <div className="text-left">
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                className="w-full h-56 p-4 rounded-lg border border-gray-200 bg-white text-sm text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
              {fileName && (
                <p className="mt-3 text-sm text-gray-600">
                  Loaded file: <span className="font-semibold text-gray-900">{fileName}</span>
                </p>
              )}
            </div>
          ) : (
            <>
              <Upload className={`mx-auto mb-4 ${isDragging ? 'text-cyan-600' : 'text-gray-400'}`} size={48} />
              <p className="text-lg font-semibold text-gray-900 mb-1">Drop your resume here</p>
              <p className="text-sm text-gray-600 mb-4">or click to upload</p>
              <p className="text-xs text-gray-500">Supports .pdf, .docx, .txt</p>
            </>
          )}
        </div>

        {resumeText && (
          <button
            onClick={clearResume}
            className="mt-3 text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            Clear resume
          </button>
        )}

        <div className="mt-6 space-y-3" ref={suggestionsRef}>
          <label className="block text-sm font-semibold text-gray-900">Target Job Role</label>
          <div className="relative">
            <input
              type="text"
              value={targetRole}
              onChange={handleRoleChange}
              onKeyDown={handleRoleKeyDown}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              placeholder="e.g. software developer"
              className="w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />

            <AnimatePresence>
              {showSuggestions && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="absolute top-full left-0 right-0 mt-1 z-20 rounded-lg border border-gray-200 bg-white shadow-lg overflow-hidden"
                >
                  {suggestions.map((item, index) => (
                    <button
                      key={item.esco_id || `${item.preferred_label}-${index}`}
                      type="button"
                      onClick={() => selectSuggestion(item.preferred_label)}
                      className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                        index === activeSuggestion
                          ? 'bg-cyan-50 text-cyan-700'
                          : 'text-gray-800 hover:bg-gray-50'
                      }`}
                    >
                      {item.preferred_label}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="pt-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Analysis Mode</p>
            <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1">
              {ANALYSIS_MODE_OPTIONS.map((option) => {
                const selected = analysisMode === option.id;
                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setAnalysisMode(option.id)}
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                      selected
                        ? 'bg-cyan-600 text-white shadow-sm'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              className="mt-4 p-3 rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleAnalyze}
          disabled={isAnalyzing || !resumeText.trim() || !targetRole.trim()}
          className="mt-6 w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isAnalyzing ? loadingMsg || 'Analyzing...' : 'Analyze Resume'}
        </motion.button>

        {analysis && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 rounded-2xl border border-cyan-200 bg-gradient-to-br from-cyan-50 via-white to-blue-50 p-6"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-xl font-bold text-gray-900">Analysis is ready</h3>
                <p className="text-sm text-gray-600">Open the Results tab to view the full Demo-style score page.</p>
              </div>
              <button
                type="button"
                onClick={() => setActiveTab('results')}
                className="px-4 py-2 rounded-lg bg-cyan-600 text-white text-sm font-semibold hover:bg-cyan-700 transition-colors"
              >
                Open Results
              </button>
            </div>
          </motion.div>
        )}
      </div>

      <div className="space-y-6">
        <div className="rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 p-6">
          <div className="flex items-start gap-3">
            <Lightbulb className="text-amber-600 flex-shrink-0 mt-1" size={24} />
            <div>
              <p className="font-semibold text-amber-900 mb-3">Pro Tips</p>
              <ul className="space-y-2 text-sm text-amber-800">
                <li>Use measurable achievements in each experience point.</li>
                <li>Match your resume keywords to the target role language.</li>
                <li>Keep resume sections clean and skimmable.</li>
                <li>List tools and technologies used in real projects.</li>
              </ul>
            </div>
          </div>
        </div>

        {analysis && (
          <div className="rounded-xl border border-cyan-200 bg-gradient-to-br from-cyan-50 to-blue-50 p-6">
            <div className="flex items-center justify-between gap-3 mb-2">
              <p className="font-semibold text-gray-900">Latest Score</p>
              <span className={`text-[11px] px-2.5 py-1 rounded-full border font-semibold uppercase ${
                resultSourceMode === 'hybrid'
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}>
                Source {resultSourceMode}
              </span>
            </div>
            <p className="text-3xl font-bold text-cyan-700">{analysis.overall_score.toFixed(1)}%</p>
            <p className="text-sm text-gray-600 mt-2">Target: {analysis.role}</p>
          </div>
        )}
      </div>
    </motion.div>
  );

  const renderAnalyticsTab = () => (
    <motion.div
      key="analytics"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {!analysis ? (
        <div className="glass-panel p-10 text-center">
          <BarChart3 className="mx-auto text-gray-400 mb-3" size={42} />
          <h3 className="text-xl font-semibold text-gray-900">No analysis yet</h3>
          <p className="text-gray-600 mt-2">Upload and analyze a resume in the Resume tab to view your analytics.</p>
          <button
            onClick={() => setActiveTab('resume')}
            className="mt-5 px-5 py-2.5 rounded-lg bg-cyan-600 text-white font-medium"
          >
            Go to Resume Tab
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 sm:gap-6">
            {[
              { label: 'Overall', value: `${analysis.overall_score.toFixed(1)}%` },
              { label: 'Core Match', value: `${analysis.core_match.toFixed(1)}%` },
              { label: 'Secondary', value: `${analysis.secondary_match.toFixed(1)}%` },
              { label: 'Bonus', value: `${analysis.bonus_match.toFixed(1)}%` },
            ].map((card) => (
              <div key={card.label} className="glass-card p-5">
                <p className="text-sm text-gray-600">{card.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{card.value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-8">
            <div className="rounded-2xl border border-green-200 bg-white/80 p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <CheckCircle className="text-green-600" size={22} />
                Matched Skills
              </h3>
              {matchedSkills.length === 0 ? (
                <p className="text-sm text-gray-600">No matched skills found.</p>
              ) : (
                <div className="space-y-3 max-h-[420px] overflow-auto pr-1">
                  {matchedSkills.map((skill, i) => {
                    const confidence = skillConfidence.find((item) => item.skill === skill);
                    const pct = confidence ? Math.round(confidence.confidence * 100) : 0;

                    return (
                      <div key={`${skill}-${i}`} className="p-3 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-center justify-between gap-4">
                          <span className="font-medium text-gray-900">{skill}</span>
                          <span className="text-xs font-semibold text-green-700">{pct}%</span>
                        </div>
                        <div className="mt-2 h-2 bg-green-100 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            className="h-full bg-green-500"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-orange-200 bg-white/80 p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="text-orange-600" size={22} />
                Skills to Improve
              </h3>
              {missingSkills.length === 0 ? (
                <p className="text-sm text-gray-600">No missing skills detected.</p>
              ) : (
                <div className="space-y-3 max-h-[420px] overflow-auto pr-1">
                  {missingSkills.map((skill, i) => {
                    const priority = improvementPriority.find((item) => item.skill === skill)?.priority || 'Medium';
                    return (
                      <div key={`${skill}-${i}`} className="p-3 bg-orange-50 rounded-lg border border-orange-200 flex items-center justify-between gap-4">
                        <span className="font-medium text-gray-900">{skill}</span>
                        <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                          priority === 'High' ? 'bg-red-100 text-red-700' : priority === 'Low' ? 'bg-emerald-100 text-emerald-700' : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {priority}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="glass-panel p-8">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-xl font-bold text-gray-900">Summary</h3>
              {llmInsights && (
                <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold uppercase">
                  AI Insight
                </span>
              )}
            </div>
            <p className="text-gray-700 leading-relaxed">{analyticsSummary}</p>
          </div>
        </>
      )}
    </motion.div>
  );

  const renderResultsTab = () => (
    <motion.div
      key="results"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {!analysis ? (
        <div className="glass-panel p-10 text-center">
          <Target className="mx-auto text-gray-400 mb-3" size={42} />
          <h3 className="text-xl font-semibold text-gray-900">No results yet</h3>
          <p className="text-gray-600 mt-2">Analyze your resume first, then your full result page will appear here.</p>
          <button
            onClick={() => setActiveTab('resume')}
            className="mt-5 px-5 py-2.5 rounded-lg bg-cyan-600 text-white font-medium"
          >
            Go to Resume Tab
          </button>
        </div>
      ) : (
        <>
          <div className="glass-panel p-8">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div>
                <h2 className="text-3xl font-bold text-gray-900">Overall Result</h2>
                <p className="text-sm text-gray-600 mt-1">Detailed match view for your target role.</p>
              </div>
              <span className="px-3 py-1.5 rounded-full bg-white border border-cyan-200 text-cyan-700 text-xs font-semibold uppercase">
                {analysis.role}
              </span>
              <span className={`px-3 py-1.5 rounded-full text-xs font-semibold uppercase border ${
                resultSourceMode === 'hybrid'
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}>
                Source {resultSourceMode}
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
              <div className="lg:col-span-1 flex justify-center">
                <ScoreRing score={analysis.overall_score} size={220} />
              </div>

              <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatPill label="Core" value={`${analysis.core_match.toFixed(1)}%`} tone="cyan" />
                <StatPill label="Secondary" value={`${analysis.secondary_match.toFixed(1)}%`} tone="green" />
                <StatPill label="Bonus" value={`${analysis.bonus_match.toFixed(1)}%`} tone="amber" />
                <StatPill label="Missing" value={String(missingSkills.length)} tone="neutral" />
              </div>
            </div>

            <div className="mt-6 rounded-xl border border-white/70 bg-white/80 p-5">
              <p className="text-gray-800 leading-relaxed">{analyticsSummary}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div className="glass-panel p-7">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Skill Breakdown Radar</h3>
              <SkillRadar
                corePct={analysis.core_match}
                secondaryPct={analysis.secondary_match}
                bonusPct={analysis.bonus_match}
              />
            </div>

            <div className="glass-panel p-7">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Top Improvement Priorities</h3>
              {improvementPriority.length === 0 ? (
                <p className="text-sm text-gray-600">No critical improvements flagged.</p>
              ) : (
                <div className="space-y-3">
                  {improvementPriority.slice(0, 6).map((item, i) => (
                    <div key={`${item.skill}-${i}`} className="p-3 rounded-lg border border-orange-200 bg-orange-50 flex items-center justify-between gap-3">
                      <span className="text-gray-900 font-medium">{item.skill}</span>
                      <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                        item.priority === 'High' ? 'bg-red-100 text-red-700' : item.priority === 'Low' ? 'bg-emerald-100 text-emerald-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {item.priority}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div className="rounded-2xl border border-green-200 bg-white/80 p-7">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <CheckCircle className="text-green-600" size={20} />
                Matched Skills
              </h3>
              {matchedSkills.length === 0 ? (
                <p className="text-sm text-gray-600">No matched skills found yet.</p>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-[300px] overflow-auto pr-1">
                  {matchedSkills.slice(0, 40).map((skill, i) => (
                    <span key={`${skill}-${i}`} className="text-xs px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-200 font-medium">
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-orange-200 bg-white/80 p-7">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="text-orange-600" size={20} />
                Missing Skills
              </h3>
              {missingSkills.length === 0 ? (
                <p className="text-sm text-gray-600">No missing skills detected.</p>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-[300px] overflow-auto pr-1">
                  {missingSkills.map((skill, i) => (
                    <span key={`${skill}-${i}`} className="text-xs px-2.5 py-1 rounded-full bg-orange-50 text-orange-700 border border-orange-200 font-medium">
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </motion.div>
  );

  const renderRoadmapTab = () => (
    <motion.div
      key="roadmap"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {!roadmap ? (
        <div className="glass-panel p-10 text-center">
          <TrendingUp className="mx-auto text-gray-400 mb-3" size={42} />
          <h3 className="text-xl font-semibold text-gray-900">Roadmap unavailable</h3>
          <p className="text-gray-600 mt-2">Analyze your resume first to generate your personalized learning roadmap.</p>
        </div>
      ) : (
        <>
          <div className="glass-panel p-8">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="px-2.5 py-1 rounded-full bg-white text-cyan-700 text-xs font-semibold uppercase">{roadmap.level}</span>
              {roadmap.timeline_months && (
                <span className="px-2.5 py-1 rounded-full bg-white text-blue-700 text-xs font-semibold uppercase">
                  {roadmap.timeline_months}-Month Plan
                </span>
              )}
              {roadmap.ai_enhanced && (
                <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold uppercase">
                  AI Enhanced
                </span>
              )}
              <h2 className="text-2xl font-bold text-gray-900">{roadmap.title}</h2>
            </div>
            <p className="text-gray-700">{roadmap.summary}</p>
          </div>

          <div className="glass-panel p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                <p className="text-sm font-semibold text-gray-900 mb-3">Key Skills Focus</p>
                {roadmapKeySkills.length === 0 ? (
                  <p className="text-sm text-gray-600">Key skills will appear after roadmap generation.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {roadmapKeySkills.map((skill, i) => (
                      <span key={`${skill}-${i}`} className="text-xs px-2.5 py-1 rounded-full bg-white text-indigo-700 font-medium border border-indigo-200">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="text-sm font-semibold text-gray-900 mb-3">Language Focus</p>
                {roadmapLanguages.length === 0 ? (
                  <p className="text-sm text-gray-600">No specific programming language focus detected yet.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {roadmapLanguages.map((lang, i) => (
                      <span key={`${lang}-${i}`} className="text-xs px-2.5 py-1 rounded-full bg-white text-blue-700 font-medium border border-blue-200">
                        {lang}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 mb-4">
              <CalendarDays className="text-indigo-600" size={20} />
              <h3 className="text-lg font-bold text-gray-900">Your Roadmap (Month by Month)</h3>
            </div>

            {monthWisePlan.length === 0 ? (
              <p className="text-sm text-gray-600">Month-wise details will appear after roadmap generation.</p>
            ) : (
              <>
                <div className="flex flex-wrap gap-2 mb-6">
                  {monthWisePlan.map((monthItem) => {
                    const active = selectedMonth?.id === monthItem.id;
                    return (
                      <button
                        key={monthItem.id}
                        type="button"
                        onClick={() => setSelectedMonthId(monthItem.id)}
                        className={`px-4 py-2 rounded-lg border transition-all ${
                          active
                            ? 'border-indigo-600 bg-indigo-600 text-white font-semibold'
                            : 'border-gray-300 bg-white text-gray-700 hover:border-indigo-400 hover:bg-gray-50'
                        }`}
                      >
                        Month {monthItem.month}
                      </button>
                    );
                  })}
                </div>

                {selectedMonth && (
                  <div className="border-t pt-6">
                    <div className="flex flex-wrap items-center gap-2 mb-4">
                      <span className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold uppercase">
                        Month {selectedMonth.month}
                      </span>
                      <span className="px-3 py-1 rounded-full bg-cyan-100 text-cyan-700 text-xs font-semibold uppercase">
                        Phase {selectedMonth.phaseNumber}
                      </span>
                      <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold uppercase">
                        {selectedMonth.monthWindow}
                      </span>
                    </div>

                    <h4 className="text-lg font-bold text-gray-900 mb-2">{selectedMonth.phaseTitle}</h4>
                    <p className="text-sm text-gray-700 mb-3">
                      <span className="font-semibold">Focus:</span> {selectedMonth.focusArea}
                    </p>
                    <p className="text-sm text-gray-700 mb-4 leading-relaxed">{selectedMonth.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-semibold text-gray-900 mb-3">Key skills this month</p>
                        {selectedMonth.skills.length === 0 ? (
                          <p className="text-sm text-gray-600">No specific skill tags for this month.</p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {selectedMonth.skills.map((skill, i) => (
                              <span key={`${skill}-${i}`} className="text-xs px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-semibold text-gray-900 mb-3">Languages to practice</p>
                        {selectedMonthLanguages.length === 0 ? (
                          <p className="text-sm text-gray-600">No language-specific focus detected in this month.</p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {selectedMonthLanguages.map((lang, i) => (
                              <span key={`${lang}-${i}`} className="text-xs px-2.5 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                                {lang}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-semibold text-gray-900 mb-3">Actions to take</p>
                        <ul className="space-y-1.5 text-sm text-gray-700">
                          {selectedMonth.actions.map((action, i) => (
                            <li key={`${action}-${i}`} className="flex items-start gap-2">
                              <span className="text-indigo-600 mt-1">•</span>
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-semibold text-gray-900 mb-3">Learning objectives</p>
                        <ul className="space-y-1.5 text-sm text-gray-700">
                          {selectedMonth.objectives.map((objective, i) => (
                            <li key={`${objective}-${i}`} className="flex items-start gap-2">
                              <span className="text-emerald-600 mt-1">•</span>
                              <span>{objective}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-sm font-semibold text-gray-900 mb-3">Recommended resources</p>
                        <ul className="space-y-1.5 text-sm text-gray-700">
                          {selectedMonth.resources.map((resource, i) => (
                            <li key={`${resource}-${i}`} className="flex items-start gap-2">
                              <span className="text-teal-600 mt-1">•</span>
                              <span>{resource}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}
    </motion.div>
  );

  const renderTipsTab = () => {
    const defaultTips = [
      'Tailor your resume summary for each target role.',
      'Show outcomes with numbers (impact, growth, savings).',
      'Place critical skills in projects, not only in a skills list.',
      'Use consistent section headings for better parsing.',
    ];
    const tipsToShow = llmTips.length > 0
      ? llmTips
      : (analysis?.strengths?.length ? analysis.strengths : defaultTips);

    return (
      <motion.div
        key="tips"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 gap-8"
      >
        <div className="glass-panel p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="text-cyan-600" size={22} />
            {llmTips.length > 0 ? 'AI Tips for You' : 'Strengths to Keep'}
          </h3>
          <ul className="space-y-2 text-gray-700 text-sm">
            {tipsToShow.map((tip, i) => (
              <li key={`${tip}-${i}`} className="flex items-start gap-2">
                <span className="text-cyan-600 mt-1">•</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-panel p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="text-orange-600" size={22} />
            {llmPriorityActions.length > 0 ? 'AI Priority Actions' : 'Priority Actions'}
          </h3>
          {llmPriorityActions.length > 0 ? (
            <ul className="space-y-2 text-sm text-gray-700">
              {llmPriorityActions.slice(0, 8).map((action, i) => (
                <li key={`${action}-${i}`} className="flex items-start gap-2 p-2.5 rounded-lg border border-orange-200 bg-orange-50">
                  <span className="text-orange-600 font-semibold">{i + 1}.</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          ) : improvementPriority.length > 0 ? (
            <ul className="space-y-3 text-sm text-gray-700">
              {improvementPriority.slice(0, 8).map((item, i) => (
                <li key={`${item.skill}-${i}`} className="p-3 rounded-lg border border-orange-200 bg-orange-50 flex items-center justify-between gap-3">
                  <span>{item.skill}</span>
                  <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                    item.priority === 'High' ? 'bg-red-100 text-red-700' : item.priority === 'Low' ? 'bg-emerald-100 text-emerald-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {item.priority}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <ul className="space-y-2 text-gray-700 text-sm">
              {defaultTips.map((tip, i) => (
                <li key={`${tip}-${i}`} className="flex items-start gap-2">
                  <span className="text-orange-600 mt-1">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </motion.div>
    );
  };

  const renderBotPopup = () => {
    const lastAssistantMessage = [...botMessages].reverse().find((m) => m.role === 'assistant');
    const userInitial = String(user?.name || 'U').trim().charAt(0).toUpperCase() || 'U';
    const quickPrompts = (lastAssistantMessage?.suggested_prompts?.length
      ? lastAssistantMessage.suggested_prompts
      : [
          'Give me a 7-day plan from my roadmap',
          'Which skill should I focus on first?',
          'Give interview questions for my weak skills',
          'How should I improve my resume this week?',
        ]).slice(0, 4);

    return (
      <AnimatePresence>
        {isBotOpen && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.9, rotate: -2 }}
            animate={{ opacity: 1, y: 0, scale: 1, rotate: 0 }}
            exit={{ opacity: 0, y: 20, scale: 0.95, rotate: 1 }}
            transition={{ type: 'spring', stiffness: 350, damping: 25 }}
            className="fixed bottom-[calc(5rem+env(safe-area-inset-bottom))] left-4 right-4 z-50 flex max-h-[calc(100vh-7rem)] w-auto flex-col overflow-hidden rounded-3xl border border-cyan-200 bg-white/95 shadow-[0_16px_50px_-12px_rgba(6,182,212,0.4)] backdrop-blur-xl sm:bottom-24 sm:left-auto sm:right-6 sm:w-[420px] sm:max-h-[calc(100vh-8rem)]"
          >
            {/* Header with rounded-t-3xl so container doesn't need overflow-hidden but background still respects border */}
            <div className="flex items-center justify-between rounded-t-[1.35rem] bg-gradient-to-r from-cyan-50 to-blue-50 border-b border-cyan-100 px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="relative">
                  {/* Keep mascot properly bounded on layout */}
                  <BotMascotAnimation compact />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900">FutureFit AI</h3>
                  <p className="text-[11px] font-medium text-cyan-700">Career + Roadmap + Recruiter helper</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsBotOpen(false)}
                className="p-1.5 rounded-full text-gray-400 hover:bg-white hover:text-gray-700 hover:shadow-sm"
                aria-label="Close chatbot"
              >
                <X size={18} />
              </button>
            </div>

            <div ref={botScrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {botMessages.map((msg, idx) => (
                <div
                  key={`${msg.role}-${idx}`}
                  className={`flex items-end gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && <BotAvatarBadge size="sm" />}

                  <div className={`max-w-[88%] rounded-xl p-2.5 border ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white border-cyan-700'
                      : 'bg-gray-50 text-gray-800 border-gray-200'
                  }`}>
                    <p className="text-xs leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                    {msg.role === 'assistant' && Array.isArray(msg.action_items) && msg.action_items.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs">
                        {msg.action_items.slice(0, 3).map((item, i) => (
                          <li key={`${item}-${i}`} className="flex items-start gap-1.5">
                            <span className="mt-0.5">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div
                      className="w-7 h-7 shrink-0 rounded-full bg-slate-200 border border-slate-300 text-slate-700 text-xs font-semibold flex items-center justify-center"
                      aria-label="User avatar"
                    >
                      {userInitial}
                    </div>
                  )}
                </div>
              ))}

              {isBotLoading && (
                <div className="flex items-end gap-2 justify-start">
                  <BotAvatarBadge size="sm" />
                  <div className="rounded-xl p-2.5 border bg-gray-50 border-gray-200 text-xs text-gray-600">
                    Thinking...
                  </div>
                </div>
              )}
            </div>

            <div className="border-t border-gray-100 px-4 py-3">
              <div className="flex flex-wrap gap-1.5 mb-2">
                {quickPrompts.slice(0, 2).map((prompt, i) => (
                  <button
                    key={`${prompt}-${i}`}
                    type="button"
                    onClick={() => sendBotMessage(prompt)}
                    disabled={isBotLoading}
                    className="text-[11px] px-2 py-1 rounded-full border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 disabled:opacity-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              <AnimatePresence>
                {botError && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="mb-2 p-2 rounded-md border border-red-200 bg-red-50 text-red-700 text-xs"
                  >
                    {botError}
                  </motion.div>
                )}
              </AnimatePresence>

              <form onSubmit={handleBotSubmit} className="flex items-center gap-2">
                <input
                  type="text"
                  value={botInput}
                  onChange={(e) => setBotInput(e.target.value)}
                  placeholder="Ask FutureFit AI..."
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
                <button
                  type="submit"
                  disabled={isBotLoading || !botInput.trim()}
                  className="px-3 py-2 rounded-lg bg-cyan-600 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <SendHorizontal size={16} />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    );
  };

  const renderActiveTab = () => {
    if (activeTab === 'resume') {
      return renderResumeTab();
    }
    if (activeTab === 'results') {
      return renderResultsTab();
    }
    if (activeTab === 'analytics') {
      return renderAnalyticsTab();
    }
    if (activeTab === 'roadmap') {
      return renderRoadmapTab();
    }
    return renderTipsTab();
  };

  return (
    <div className="min-h-screen overflow-x-hidden bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <motion.button
        type="button"
        onClick={() => setIsSidebarOpen((prev) => !prev)}
        className="fixed left-4 top-4 z-[70] inline-flex h-11 w-11 items-center justify-center rounded-full border border-cyan-200 bg-white/95 text-cyan-700 shadow-[0_8px_30px_rgba(6,182,212,0.18)] backdrop-blur-md md:hidden"
        aria-label={isSidebarOpen ? 'Close navigation' : 'Open navigation'}
      >
        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </motion.button>

      {isSidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-[1px] md:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-label="Close navigation overlay"
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-gray-200 bg-white/80 p-6 backdrop-blur-xl transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <Logo size="md" />
        </div>

        {/* User Info */}
        <div className="rounded-lg bg-gradient-to-r from-cyan-50 to-blue-50 p-4 mb-8 border border-cyan-200">
          <p className="text-sm font-semibold text-gray-900">Welcome back!</p>
          <p className="text-sm text-gray-600 mt-1">{user?.name}</p>
          <p className="text-xs text-gray-500 mt-2">{user?.email}</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <motion.button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsSidebarOpen(false);
                }}
                whileHover={{ x: 4 }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300 ${
                  activeTab === item.id
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </motion.button>
            );
          })}
        </nav>

        {/* Logout Button */}
        <motion.button
          onClick={handleLogout}
          disabled={isLoading}
          whileHover={{ scale: 1.02 }}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg font-medium transition-all duration-300 disabled:opacity-50"
        >
          <LogOut size={20} />
          Logout
        </motion.button>
      </div>

      {/* Main Content */}
      <div className="relative z-0 min-h-screen p-4 pt-20 pb-28 sm:p-6 sm:pt-6 sm:pb-8 md:ml-64 lg:p-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Student Dashboard</h1>
              <p className="text-gray-600">Run analysis, review insights, and follow your roadmap from one place.</p>
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ staggerChildren: 0.1 }}
          className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 sm:gap-6"
        >
          {[
            { label: 'Resume Loaded', value: fileName ? '1' : '0', icon: FileText, color: 'cyan' },
            { label: 'Analyzed', value: analysis ? '1' : '0', icon: BarChart3, color: 'blue' },
            { label: 'Overall Score', value: analysis ? `${analysis.overall_score.toFixed(1)}%` : '-', icon: TrendingUp, color: 'emerald' },
            { label: 'Missing Skills', value: analysis ? String(missingSkills.length) : '0', icon: AlertCircle, color: 'orange' },
          ].map((stat, i) => {
            const Icon = stat.icon;
            const colors = {
              cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-200',
              blue: 'from-blue-500/20 to-blue-500/5 border-blue-200',
              emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-200',
              orange: 'from-orange-500/20 to-orange-500/5 border-orange-200',
            };

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`rounded-xl border bg-gradient-to-br ${colors[stat.color]} p-6 backdrop-blur-sm`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{stat.label}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  </div>
                  <Icon size={32} className={`text-${stat.color}-600 opacity-50`} />
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        <AnimatePresence mode="wait">
          {renderActiveTab()}
        </AnimatePresence>
      </div>

      {/* Floating chatbot launcher + popup */}
      {renderBotPopup()}
      <motion.button
        type="button"
        onClick={() => setIsBotOpen((prev) => !prev)}
        whileHover={{ scale: 1.05, y: -4 }}
        whileTap={{ scale: 0.95 }}
        className="fixed bottom-[calc(1rem+env(safe-area-inset-bottom))] right-4 z-[60] flex max-w-[calc(100vw-2rem)] items-center gap-3 rounded-full border-[2px] border-cyan-200 bg-white/95 p-2 pr-4 shadow-[0_8px_30px_rgba(6,182,212,0.25)] backdrop-blur-md transition-all duration-300 group hover:border-cyan-400 hover:shadow-[0_8px_30px_rgba(6,182,212,0.4)] sm:right-6 sm:bottom-6 sm:pr-6"
        aria-label={isBotOpen ? 'Close FutureFit AI chat' : 'Open FutureFit AI chat'}
      >
        {!isBotOpen && (
          <motion.span
            className="absolute -top-12 right-0 hidden rounded-2xl rounded-br-sm border border-cyan-400/50 bg-gradient-to-r from-cyan-500 to-blue-600 px-3.5 py-2 text-[12px] font-bold text-white shadow-lg z-[70] sm:block"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
          >
            Chat with AI 👋
          </motion.span>
        )}
        <div className="relative">
          <div className="absolute inset-0 rounded-full animate-ping bg-cyan-400 opacity-30 duration-1000" />
          <BotAvatarBadge size="md" />
        </div>
        <span className="hidden text-[15px] font-extrabold bg-gradient-to-r from-cyan-600 to-blue-700 bg-clip-text text-transparent transition-all group-hover:from-cyan-500 group-hover:to-blue-600 sm:inline">
          FutureFit AI
        </span>
      </motion.button>
    </div>
  );
};

export default StudentDashboard;
