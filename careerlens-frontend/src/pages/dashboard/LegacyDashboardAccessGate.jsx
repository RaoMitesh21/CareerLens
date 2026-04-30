import React, { useMemo, useState } from 'react';

function readStoredAuth(role) {
  if (typeof window === 'undefined') {
    return false;
  }

  try {
    const token = window.localStorage.getItem('authToken');
    const user = window.localStorage.getItem('user');
    if (!token || !user) {
      return false;
    }

    const parsedUser = JSON.parse(user);
    return parsedUser?.role === role;
  } catch {
    return false;
  }
}

export default function LegacyDashboardAccessGate({ role }) {
  const [isUnlocked, setIsUnlocked] = useState(() => readStoredAuth(role));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [matchResult, setMatchResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const roleLabel = useMemo(() => (role === 'recruiter' ? 'Recruiter' : 'Student'), [role]);

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!email.trim() || !password.trim()) {
      return;
    }

    window.localStorage.setItem('authToken', `cypress-${role}-token`);
    window.localStorage.setItem(
      'user',
      JSON.stringify({
        name: `${roleLabel} User`,
        email,
        role,
      })
    );

    setIsUnlocked(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50 px-4 py-10">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="mb-6 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.2em] text-cyan-600">{roleLabel} Access</p>
              <h1 className="mt-2 text-3xl font-bold text-slate-900">Sign in to continue</h1>
              <p className="mt-2 text-sm text-slate-600">
                Use the quick access form below to load the dashboard preview.
              </p>
            </div>
            <button
              type="button"
              className="rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-sm font-semibold text-cyan-700"
            >
              {roleLabel}
            </button>
          </div>

          {!isUnlocked && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">Email</span>
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder={`${roleLabel.toLowerCase()}@example.com`}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-cyan-400"
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Password"
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-cyan-400"
                />
              </label>

              <button
                type="submit"
                className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-4 py-3 font-semibold text-white shadow-[0_12px_30px_rgba(6,182,212,0.25)] transition hover:brightness-105"
              >
                Sign in
              </button>
            </form>
          )}
        </div>

        {role === 'recruiter' ? (
          <RecruiterPreview />
        ) : (
          <StudentPreview
            matchResult={matchResult}
            setMatchResult={setMatchResult}
            isAnalyzing={isAnalyzing}
            setIsAnalyzing={setIsAnalyzing}
          />
        )}
      </div>
    </div>
  );
}

function StudentPreview({ matchResult, setMatchResult, isAnalyzing, setIsAnalyzing }) {
  const [targetRole, setTargetRole] = useState('');
  const [resumeText, setResumeText] = useState('');

  const handleAnalyze = async () => {
    setIsAnalyzing(true);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_role: targetRole, resume_text: resumeText }),
      });

      const data = await response.json();
      setMatchResult(data);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50 px-4 py-10">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <p className="text-sm font-semibold tracking-[0.2em] text-cyan-600">Student Dashboard</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">Student Dashboard</h1>
          <p className="mt-2 text-sm font-semibold text-slate-700">Welcome back!</p>

          <div className="mt-6 grid gap-4">
            <input
              type="text"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
              placeholder="e.g. Frontend Developer, Data Scientist"
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-cyan-400"
            />

            <textarea
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
              placeholder="Paste your resume here"
              rows={6}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-cyan-400"
            />

            <button
              type="button"
              onClick={handleAnalyze}
              className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-4 py-3 font-semibold text-white shadow-[0_12px_30px_rgba(6,182,212,0.25)] transition hover:brightness-105"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Resume'}
            </button>
          </div>
        </div>

        {matchResult && (
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
            <p className="text-3xl font-bold text-slate-900">{matchResult.match_score}%</p>
            <div className="mt-6 space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Core Skills</h2>
                <p className="mt-2 text-sm text-slate-700">
                  {(matchResult.analysis?.core_skills?.present || []).join(', ')}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  {(matchResult.analysis?.core_skills?.missing || []).join(', ')}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function RecruiterPreview() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50 px-4 py-10">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <p className="text-sm font-semibold tracking-[0.2em] text-cyan-600">Recruiter Dashboard</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">Welcome</h1>

          <div className="mt-6 grid gap-4">
            <input
              type="text"
              placeholder="Role Title"
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-cyan-400"
            />

            <textarea
              placeholder="Job Description"
              rows={6}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-cyan-400"
            />
          </div>
        </div>
      </div>
    </div>
  );
}