/* ═══════════════════════════════════════════════════════════════════
   CareerLens API Service — Connects to FastAPI Backend
   ═══════════════════════════════════════════════════════════════════
   All backend communication lives here. No fetch() calls elsewhere.
   ═══════════════════════════════════════════════════════════════════ */

function resolveApiBaseUrl() {
  const envUrl = (import.meta.env.VITE_API_URL || '').trim();
  
  if (typeof window === 'undefined') {
    return envUrl || 'http://127.0.0.1:8012';
  }

  const hostname = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;

  // React Dev server runs on port 5173. Capacitor Android runs on localhost with NO port. iOS runs on capacitor://
  const isCapacitor = (hostname === 'localhost' && port === '') || protocol === 'capacitor:';
  const isReactDevServer = (hostname === 'localhost' || hostname === '127.0.0.1') && port !== '';

  // Mobile App (Capacitor) should ALWAYS point to the live server
  if (isCapacitor) {
    return envUrl || 'https://careerlens-api-imy1.onrender.com';
  }

  // Local development: route through Vite proxy to avoid CORS issues
  if (isReactDevServer) {
    return '/api';
  }

  // Production: use explicit env URL, or auto-detect if on careerlens domains
  if (envUrl) {
    return envUrl;
  }

  // Auto-detect production API based on frontend domain
  if (hostname.includes('careerlens.in') || hostname.includes('vercel.app')) {
    return 'https://careerlens-api-imy1.onrender.com';
  }

  return envUrl || 'http://127.0.0.1:8012';
}

const API_BASE_URL = resolveApiBaseUrl();
const API_BASE = API_BASE_URL;
const DEFAULT_ANALYSIS_MODE = 'esco';

export function apiUrl(path = '') {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}

function normalizeAnalysisMode(mode) {
  return String(mode || '').toLowerCase() === 'hybrid' ? 'hybrid' : DEFAULT_ANALYSIS_MODE;
}

/* ── Helpers ───────────────────────────────────────────────────────── */
async function handleResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err?.detail;

    if (Array.isArray(detail)) {
      const message = detail
        .map((item) => {
          const location = Array.isArray(item?.loc) ? item.loc.join('.') : 'request';
          return `${location}: ${item?.msg || 'invalid value'}`;
        })
        .join(' | ');
      throw new Error(message || `Request failed (${res.status})`);
    }

    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function getAuthToken() {
  return localStorage.getItem('authToken');
}

async function authJsonFetch(url, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (!token) {
    throw new Error('Authentication required');
  }

  headers.Authorization = `Bearer ${token}`;

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401 && typeof window !== 'undefined') {
    window.dispatchEvent(new Event('careerlens:auth-expired'));
  }

  return handleResponse(res);
}

/* ── Analysis ──────────────────────────────────────────────────────── */

/**
 * POST /analyze — 3-tier gap analysis only
 */
export async function analyzeResume(resumeText, targetRole, mode = DEFAULT_ANALYSIS_MODE) {
  const normalizedMode = normalizeAnalysisMode(mode);

  const endpoint = normalizedMode === 'hybrid' ? '/analyze/hybrid' : '/analyze';
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume_text: resumeText,
      target_occupation: targetRole,
    }),
  });
  return handleResponse(res);
}

/**
 * POST /analyze/full — Analysis + roadmap in one call
 * Returns { analysis: GapAnalysisResponse, roadmap: RoadmapResponse }
 */
export async function analyzeWithRoadmap(resumeText, targetRole, mode = DEFAULT_ANALYSIS_MODE) {
  const normalizedMode = normalizeAnalysisMode(mode);

  const payload = {
    resume_text: resumeText,
    target_occupation: targetRole,
  };

  if (normalizedMode !== 'hybrid') {
    const res = await fetch(`${API_BASE}/analyze/full`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  }

  const [hybridResult, fullResult] = await Promise.allSettled([
    fetch(`${API_BASE}/analyze/hybrid`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),
    fetch(`${API_BASE}/analyze/full`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  ]);

  if (hybridResult.status !== 'fulfilled') {
    throw hybridResult.reason instanceof Error
      ? hybridResult.reason
      : new Error('Hybrid analysis failed.');
  }

  const hybrid = hybridResult.value || {};
  const full = fullResult.status === 'fulfilled' ? fullResult.value || {} : {};
  const hybridAnalysis = hybrid.analysis || {};
  const fusedScore = Number(hybrid.fused_score);

  return {
    analysis: {
      ...hybridAnalysis,
      overall_score: Number.isFinite(fusedScore)
        ? fusedScore
        : Number(hybridAnalysis.overall_score || 0),
      hybrid_meta: {
        fusion_strategy: hybrid.fusion_strategy || '',
        fused_score: Number.isFinite(fusedScore) ? fusedScore : Number(hybridAnalysis.overall_score || 0),
        onet: hybrid.onet || null,
      },
    },
    roadmap: full.roadmap || null,
  };
}

/**
 * POST /analyze/batch — Analyze multiple resumes vs one target role
 * Returns ranked candidate list
 */
export async function batchAnalyzeResumes(resumesData, targetRole, mode = DEFAULT_ANALYSIS_MODE) {
  const normalizedMode = normalizeAnalysisMode(mode);

  const endpoint = normalizedMode === 'hybrid' ? '/analyze/batch/hybrid' : '/analyze/batch';

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resumes: resumesData,
      target_occupation: targetRole,
    }),
  });
  return handleResponse(res);
}

/**
 * POST /analyze/hybrid/diagnostics — Debug hybrid scoring details
 */
export async function analyzeHybridDiagnostics(resumeText, targetRole) {
  const res = await fetch(`${API_BASE}/analyze/hybrid/diagnostics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume_text: resumeText,
      target_occupation: targetRole,
    }),
  });
  return handleResponse(res);
}

/**
 * POST /bot/chat — Hybrid bot (career coach + roadmap + recruiter helper)
 */
export async function chatWithCareerBot(message, history = [], context = null) {
  const res = await fetch(`${API_BASE}/bot/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history,
      context,
    }),
  });
  return handleResponse(res);
}

/* ── Occupations ───────────────────────────────────────────────────── */

/**
 * GET /occupations/search?q=...&limit=...
 */
export async function searchOccupations(query, limit = 10, mode = DEFAULT_ANALYSIS_MODE) {
  const normalizedMode = normalizeAnalysisMode(mode);

  const endpoint = normalizedMode === 'hybrid' ? '/occupations/search/hybrid' : '/occupations/search';

  const res = await fetch(
    `${API_BASE}${endpoint}?q=${encodeURIComponent(query)}&limit=${limit}`
  );
  return handleResponse(res);
}

/* ── Health ─────────────────────────────────────────────────────────── */

/**
 * GET / — Health check
 */
export async function healthCheck() {
  const res = await fetch(`${API_BASE}/`);
  return handleResponse(res);
}

/* ── Dashboard State Persistence (authenticated) ─────────────────── */

export async function getDashboardState(scope) {
  return authJsonFetch(`${API_BASE}/dashboard-state/${encodeURIComponent(scope)}`, {
    method: 'GET',
  });
}

export async function saveDashboardState(scope, state) {
  return authJsonFetch(`${API_BASE}/dashboard-state/${encodeURIComponent(scope)}`, {
    method: 'PUT',
    body: JSON.stringify({ state }),
  });
}

export async function listRecruiterAnalysisHistory(limit = 20) {
  return authJsonFetch(`${API_BASE}/recruiter/analysis-history?limit=${encodeURIComponent(limit)}`, {
    method: 'GET',
  });
}

export async function saveRecruiterAnalysisHistory(payload) {
  return authJsonFetch(`${API_BASE}/recruiter/analysis-history`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deleteRecruiterAnalysisHistory(analysisKey) {
  return authJsonFetch(`${API_BASE}/recruiter/analysis-history/${encodeURIComponent(analysisKey)}`, {
    method: 'DELETE',
  });
}

/* ── File Parsing (client-side) ────────────────────────────────────── */

/**
 * Read a .txt / .pdf / .docx file and return its text content.
 * - .txt  → FileReader.readAsText
 * - .pdf  → pdf.js  (loaded from CDN on demand)
 * - .docx → mammoth.js (loaded from CDN on demand)
 *
 * Returns a Promise<string>
 */
export async function parseFileToText(file) {
  const ext = file.name.split('.').pop().toLowerCase();

  if (ext === 'txt' || ext === 'text') {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error('Failed to read text file'));
      reader.readAsText(file);
    });
  }

  if (ext === 'pdf') {
    // Dynamically load pdf.js from CDN
    if (!window.pdfjsLib) {
      await loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');
      window.pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const pages = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      pages.push(content.items.map((item) => item.str).join(' '));
    }
    return pages.join('\n');
  }

  if (ext === 'docx' || ext === 'doc') {
    // Dynamically load mammoth.js from CDN
    if (!window.mammoth) {
      await loadScript('https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js');
    }
    const arrayBuffer = await file.arrayBuffer();
    const result = await window.mammoth.extractRawText({ arrayBuffer });
    return result.value;
  }

  throw new Error(`Unsupported file type: .${ext}. Please upload .txt, .pdf, or .docx`);
}

/** Load an external script tag into the page (returns when loaded) */
function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(s);
  });
}
