/* ═══════════════════════════════════════════════════════════════════
   Resume Parser — Extracts structured candidate data from raw text
   ═══════════════════════════════════════════════════════════════════
   Handles PDF-extracted text (often 1 giant line with NO newlines)
   as well as well-formatted DOCX/TXT resumes.
   Key: normaliseText() injects newlines before section headers so
   every extractor can rely on line-based logic.
   ═══════════════════════════════════════════════════════════════════ */

/* ── Section headers we split on ─────────────────────────────────── */
const SECTION_HEADERS = [
  'Professional Summary', 'Summary', 'Objective', 'About Me', 'About',
  'Education', 'Academic Background', 'Qualifications',
  'Work Experience', 'Experience', 'Employment History', 'Work History',
  'Technical Skills', 'Skills', 'Core Competencies', 'Technologies', 'Tech Stack',
  'Projects', 'Personal Projects', 'Key Projects', 'Academic Projects',
  'Certifications', 'Certificates', 'Achievements & Certifications',
  'Certifications & Achievements', 'Achievements', 'Awards', 'Honors',
  'Extracurricular Activities', 'Extracurricular', 'Activities',
  'Interests', 'Hobbies', 'References', 'Languages',
  'Soft Skills', 'Publications', 'Volunteer',
];

/**
 * Parse raw resume text and return structured candidate object.
 * @param {string} rawText - Raw resume text (from parseFileToText)
 * @returns {{ name, title, education, location, contact, certifications, projects, skills } | null}
 */
export function parseResumeText(rawText) {
  if (!rawText || rawText.trim().length < 20) return null;

  // Step 1 — normalise: inject newlines so extractors work
  const text = normaliseText(rawText);
  const lines = text.split(/\n/).map(l => l.trim()).filter(Boolean);

  const candidate = {
    name: extractName(lines, text),
    title: extractTitle(lines, text),
    education: extractEducation(text),
    location: extractLocation(text),
    contact: extractContact(text),
    certifications: extractCertifications(text),
    projects: extractProjects(text),
    skills: extractSkills(text),
  };

  // Only return if we got at least a name, skills, or contact
  const hasUseful = candidate.name || candidate.skills || candidate.contact;
  return hasUseful ? candidate : null;
}

/* ═══════════════════════════════════════════════════════════════════
   NORMALISE — turn single-line PDF blob into sectioned text
   ═══════════════════════════════════════════════════════════════════ */
function normaliseText(raw) {
  let text = raw.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  // If already well-formatted (> 10 lines), keep as-is
  const lineCount = (text.match(/\n/g) || []).length;
  if (lineCount > 10) return text;

  // ── 1. Split contact header from first section ──
  // PDF header is often: "Name Phone Email URLs Location Summary ..."
  // Insert \n before email, phone, linkedin, github patterns
  text = text.replace(/\s+(\+?\d[\d\s\-()]{7,})/g, '\n$1');                       // phone
  text = text.replace(/\s+([a-zA-Z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,})/gi, '\n$1'); // email
  text = text.replace(/\s+((?:https?:\/\/)?(?:www\.)?(?:linkedin|github)\.[a-z]+[^\s]*)/gi, '\n$1'); // URLs

  // ── 2. Insert \n before known section headers ──
  // Sort longest-first so "Technical Skills" matches before "Skills"
  const sorted = [...SECTION_HEADERS].sort((a, b) => b.length - a.length);
  for (const header of sorted) {
    const escaped = header.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // Match header preceded by space (not already at start of line)
    const re = new RegExp(`(?<![\\n])\\s+(${escaped})\\s*(?=[:\\n–—\\-]|[A-Z])`, 'gi');
    text = text.replace(re, '\n$1');
  }

  // ── 3. Insert \n before "Category : value" patterns ──
  // e.g. "Programming Languages : Python, ..."
  text = text.replace(/\s+([A-Z][A-Za-z\s&/]{2,35}?)\s*:\s*/g, '\n$1 : ');

  // ── 4. Insert \n before bullet points ──
  text = text.replace(/\s+([–•▸▹►➤✓✔])\s*/g, '\n$1 ');

  // ── 5. Insert \n before date patterns (Jan 2025, July 2024 –) ──
  text = text.replace(/\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})/gi, '\n$1');

  return text;
}

/* ─── NAME ─────────────────────────────────────────────────────────── */
function extractName(lines, text) {
  const skipPatterns = /^(resume|curriculum|cv|portfolio|profile|summary|objective|contact|phone|email|http|www\.|linkedin|github|professional|education|experience|technical|skills|projects?|certif|achieve|interest|extracur)/i;

  for (const line of lines.slice(0, 15)) {
    // Aggressively clean the line: strip phones, emails, URLs, punctuation
    const clean = line
      .replace(/[|•·§ï#]+/g, ' ')
      .replace(/\+?\d[\d\s\-()]{6,}/g, ' ')                                   // phones
      .replace(/[a-zA-Z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}/gi, ' ')           // emails
      .replace(/(?:https?:\/\/)?(?:www\.)?[a-z0-9\-]+\.[a-z]{2,}[^\s]*/gi, ' ') // URLs
      .replace(/[,\-—–:]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

    if (!clean || clean.length < 2 || clean.length > 50) continue;
    if (skipPatterns.test(clean)) continue;
    if (/^[+\d(]/.test(clean)) continue;

    const words = clean.split(/\s+/).filter(w => w.length > 0);
    if (words.length < 1 || words.length > 5) continue;

    // At least 60 % of words must be alphabetic
    const alphaWords = words.filter(w => /^[A-Za-z.]+$/.test(w));
    if (alphaWords.length >= Math.ceil(words.length * 0.6)) {
      return alphaWords
        .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
        .join(' ');
    }
  }

  // Fallback: "Name: ..."
  const m = text.match(/(?:name|full\s*name)\s*[:\-]\s*([A-Za-z\s.]{2,40})/i);
  return m ? m[1].trim() : null;
}

/* ─── TITLE / HEADLINE ────────────────────────────────────────────── */
function extractTitle(lines, text) {
  const titleKW = /\b(developer|engineer|analyst|scientist|designer|manager|intern|architect|consultant|student|specialist|lead|director|officer|coordinator|full[- ]?stack)\b/i;

  // Check lines near the top (after name)
  for (const line of lines.slice(1, 14)) {
    const clean = line.replace(/[|•·§ï#]/g, ' ').replace(/\s+/g, ' ').trim();
    if (clean.length > 10 && clean.length < 120 && titleKW.test(clean)) {
      return clean;
    }
  }

  // Fallback: first sentence of Professional Summary
  const sm = text.match(/(?:professional\s*summary|summary|objective|about)\s*[:\n–—\-]\s*([^.\n]{15,150})/i);
  if (sm) {
    let t = sm[1].replace(/\s+/g, ' ').trim();
    if (t.length > 100) t = t.slice(0, 100) + '…';
    return t;
  }

  return null;
}

/* ─── EDUCATION ───────────────────────────────────────────────────── */
function extractEducation(text) {
  const patterns = [
    /\b(B\.?(?:Tech|Sc|E|A|Com|S)|M\.?(?:Tech|Sc|E|A|BA|S)|Ph\.?D|MBA|Bachelor|Master|Diploma)[^\n]*?(?:university|college|institute|school)[^\n]*/i,
    /(?:university|college|institute)[^\n]*?(?:B\.?(?:Tech|Sc|E|A|Com|S)|M\.?(?:Tech|Sc|E|A|BA|S)|Bachelor|Master|CGPA|GPA)[^\n]*/i,
    /\b(Bachelor|Master|Doctor)\s+of\s+[^\n]{5,100}/i,
    /(?:university|college|institute)[^\n]*(?:cgpa|gpa|\d+\.\d+)[^\n]*/i,
  ];

  for (const p of patterns) {
    const m = text.match(p);
    if (m) {
      let edu = m[0].replace(/\s+/g, ' ').trim();
      if (edu.length > 130) edu = edu.slice(0, 130) + '…';
      return edu;
    }
  }
  return null;
}

/* ─── LOCATION ────────────────────────────────────────────────────── */
function extractLocation(text) {
  const cities = 'Ahmedabad|Mumbai|Bangalore|Bengaluru|Delhi|Hyderabad|Chennai|Pune|Kolkata|Jaipur|Lucknow|Chandigarh|Noida|Gurgaon|Gurugram|Kochi|Indore|Bhopal|Nagpur|Surat|Vadodara|Visakhapatnam|Thiruvananthapuram|Coimbatore|Patna|New York|San Francisco|London|Berlin|Toronto|Sydney|Dubai|Amsterdam|Singapore|Tokyo';

  // "City, State, Country"
  const m1 = text.match(new RegExp(`(${cities})[,\\s]+([A-Z][a-z]+(?:\\s[A-Z][a-z]+)*)[,\\s]+(India|USA|UK|Canada|Australia|Germany|Singapore|UAE|Netherlands|Ireland|Japan)`, 'i'));
  if (m1) return m1[0].trim();

  // "City, State"
  const m2 = text.match(new RegExp(`(${cities})[,\\s]+([A-Z][a-z]+(?:\\s[A-Z][a-z]+)*)`, 'i'));
  if (m2) return m2[0].replace(/\s+/g, ' ').trim();

  // Generic "Location: ..." or "Address: ..."
  const m3 = text.match(/(?:location|address|city)\s*[:\-]\s*([^\n]{5,60})/i);
  if (m3) return m3[1].trim();

  return null;
}

/* ─── CONTACT ─────────────────────────────────────────────────────── */
function extractContact(text) {
  const email = text.match(/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/);
  const phone = text.match(/(?:\+?\d{1,3}[\s\-]?)?\(?\d{3,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5}/);
  const linkedin = text.match(/linkedin\.com\/in\/[a-zA-Z0-9\-._]+/i);
  const github = text.match(/github\.com\/[a-zA-Z0-9\-._]+/i);

  if (!email && !phone) return null;

  return {
    ...(email && { email: email[0] }),
    ...(phone && { phone: phone[0].trim() }),
    ...(linkedin && { linkedin: linkedin[0] }),
    ...(github && { github: github[0] }),
  };
}

/* ─── CERTIFICATIONS ──────────────────────────────────────────────── */
function extractCertifications(text) {
  const certs = [];

  // Section-based extraction (now works because normaliseText injected \n)
  const sec = text.match(/(?:certification|certificates|achievements?\s*(?:&|and)?\s*certification|awards|honors)[s\s]*[:\n\-–—]*\s*([\s\S]{10,1000}?)(?=\n\s*(?:experience|education|projects?|skills|technical|extracur|hobby|interest|reference|$))/i);
  if (sec) {
    const items = sec[1]
      .split(/\n/)
      .map(l => l.replace(/^[\s\-•–·▸▹►➤✓✔]+/, '').trim())
      .filter(l => l.length > 5 && l.length < 120 && !/^\d{4}$/.test(l));
    certs.push(...items.slice(0, 8));
  }

  // Fallback: detect known patterns anywhere in text
  if (certs.length === 0) {
    const patterns = [
      /(?:AWS|Amazon)\s+[A-Za-z\s]+?(?:Practitioner|Associate|Professional|Specialty)/gi,
      /Google\s+(?:Data|Cloud|IT|UX|Project|Digital)\s*[A-Za-z\s]*/gi,
      /(?:Deep\s+Learning|Machine\s+Learning|AI)\s+(?:Specialization|Certificate|Certification)/gi,
      /freeCodeCamp[^\n|,]{0,60}/gi,
      /(?:Coursera|Udemy|edX|HackerRank|Udacity)\s*[^\n|,]{5,60}/gi,
      /(?:Certified|Certification)\s+[A-Za-z\s]{5,50}/gi,
    ];
    for (const p of patterns) {
      const ms = text.match(p);
      if (ms) ms.forEach(m => {
        const c = m.trim();
        if (c.length > 5 && !certs.includes(c)) certs.push(c);
      });
    }
  }

  return certs.length > 0 ? certs.slice(0, 8) : null;
}

/* ─── PROJECTS ────────────────────────────────────────────────────── */
function extractProjects(text) {
  const projects = [];

  // Find the projects section (after normalisation there should be \n boundaries)
  const projSection = text.match(/(?:projects?|personal\s+projects?|key\s+projects?|academic\s+projects?)\s*[:\n\-–—]*\s*([\s\S]{10,2000}?)(?=\n\s*(?:experience|education|certification|achievement|skills|technical|extra|hobby|interest|reference|\n\n\n))/i);

  if (projSection) {
    const sectionText = projSection[1];
    const projLines = sectionText.split(/\n/);
    const skipRe = /^(projects?|experience|education|skills|technical|professional|certification|achievement)/i;
    const verbRe = /^(Developed|Built|Implemented|Created|Designed|Used|Utilized|Integrated|Worked|Led|Managed|Achieved|Increased|Reduced|Collaborated|Presented|Trained|Deployed|Automated)/i;

    for (const line of projLines) {
      const clean = line.replace(/^[\s\-•–·▸▹►➤]+/, '').trim();
      if (!clean || clean.length < 3) continue;

      // "Title | Tech" or "Title – Description | Tech" or "Title - Description"
      const titleMatch = clean.match(/^([A-Z][A-Za-z0-9\s\-_&.]+?)(?:\s*[|—–\-:]\s*(.+?))?(?:\s+(?:Semester|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}|Ongoing|Present|Current|Completed).*)?$/);

      if (titleMatch && clean.length < 150) {
        const name = titleMatch[1].trim();
        const tech = titleMatch[2]?.trim() || '';

        if (verbRe.test(name)) continue;
        if (skipRe.test(name)) continue;
        if (name.length < 2 || name.length > 50) continue;

        const statusRaw = clean.toLowerCase();
        const status = /ongoing|present|current|in\s*progress|live/i.test(statusRaw) ? 'Ongoing' : 'Completed';
        projects.push({ name, tech, status });
      }
    }
  }

  // Fallback: "Title | Tech" pattern anywhere in the text
  if (projects.length === 0) {
    const re = /(?:^|\n)\s*([A-Z][A-Za-z0-9\s\-]{2,35}?)\s*\|\s*([A-Za-z0-9,.\s()#+]+?)(?=\s+(?:Semester|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}|Ongoing|–|\n|$))/gi;
    let m;
    while ((m = re.exec(text)) !== null) {
      const name = m[1].trim();
      const tech = m[2].trim();
      if (/^(projects?|experience|education|skills|technical|professional|certification|achievement)/i.test(name)) continue;
      if (name.length < 3 || name.length > 40) continue;
      const ctx = text.slice(m.index, m.index + 200).toLowerCase();
      const status = /ongoing|present|current/i.test(ctx) ? 'Ongoing' : 'Completed';
      projects.push({ name, tech, status });
    }
  }

  return projects.length > 0 ? projects.slice(0, 6) : null;
}

/* ─── SKILLS ──────────────────────────────────────────────────────── */
function extractSkills(text) {
  const skills = {};

  // Strategy 1: section-based "Category : skill1, skill2, ..." inside a skill section
  const skillSection = text.match(/(?:technical\s+skills?|skills?|competencies|technologies|tech\s+stack)\s*[:\n\-–—]*\s*([\s\S]{10,2000}?)(?=\n\s*(?:experience|education|projects?|certification|achievement|extra|hobby|interest|reference|professional\s+summary|\n\n\n))/i);

  if (skillSection) {
    const sectionText = skillSection[1];
    const lines = sectionText.split(/\n/).map(l => l.trim()).filter(Boolean);

    for (const line of lines) {
      const catMatch = line.match(/^([A-Za-z\s&/]+?)\s*[:\-]\s*(.+)/);
      if (catMatch) {
        const category = catMatch[1].trim();
        const skillList = catMatch[2]
          .split(/[,;|•·]/)
          .map(s => s.replace(/^[\s\-•–]+/, '').trim())
          .filter(s => s.length > 0 && s.length < 60);

        if (skillList.length > 0 && category.length > 2 && category.length < 50) {
          // Skip non-skill categories
          if (/^(professional|summary|objective|education|experience|name|semester|duration|location|address|cgpa|gpa)/i.test(category)) continue;
          skills[category] = skillList;
        }
      }
    }
  }

  // Strategy 2: "Category : ..." patterns ANYWHERE in text (works on single-line PDF)
  if (Object.keys(skills).length === 0) {
    const catPattern = /\b([A-Z][A-Za-z\s&/]{2,35}?)\s*:\s*([A-Za-z0-9,.\s()#+\-/]+?)(?=\s+[A-Z][A-Za-z\s&/]{2,35}?\s*:|$|\n\s*(?:Projects?|Experience|Education|Certification|Achievement|Extracur))/gi;
    let match;
    while ((match = catPattern.exec(text)) !== null) {
      const category = match[1].trim();
      const rawSkills = match[2].trim();

      if (/^(professional|summary|objective|education|experience|name|semester|duration|location|address|cgpa|gpa)/i.test(category)) continue;

      const skillList = rawSkills
        .split(/[,;|•·]/)
        .map(s => s.replace(/^[\s\-•–]+/, '').trim())
        .filter(s => s.length > 0 && s.length < 60);

      if (skillList.length > 0 && category.length > 2 && category.length < 50) {
        skills[category] = skillList;
      }
    }
  }

  if (Object.keys(skills).length > 0) return skills;

  // Strategy 3: fallback — detect known technologies from full text
  return extractSkillsFallback(text);
}

/* Fallback: detect known technologies from the full text */
function extractSkillsFallback(text) {
  const categories = {
    'Programming Languages': ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'C', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'SQL', 'Dart', 'Lua'],
    'Web & Frontend': ['React', 'React.js', 'Angular', 'Vue.js', 'Next.js', 'Svelte', 'HTML', 'CSS', 'Tailwind', 'Bootstrap', 'SASS', 'jQuery', 'Redux', 'Webpack', 'Vite'],
    'Backend & APIs': ['Node.js', 'Express', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Rails', 'Laravel', 'ASP.NET', 'GraphQL', 'REST API'],
    'Data Science & ML': ['Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'Keras', 'XGBoost', 'NLP', 'Computer Vision', 'Data Analysis', 'Predictive Modeling'],
    'Database': ['MySQL', 'PostgreSQL', 'MongoDB', 'SQLite', 'Redis', 'DynamoDB', 'Firebase', 'Cassandra', 'Oracle', 'SQL Server'],
    'Cloud & DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Terraform', 'Linux', 'Nginx', 'Heroku', 'Vercel', 'Netlify'],
    'Tools': ['Git', 'GitHub', 'VS Code', 'Jupyter', 'Postman', 'Figma', 'Jira', 'Slack', 'Notion'],
  };

  const result = {};
  for (const [cat, techs] of Object.entries(categories)) {
    const found = techs.filter(t => {
      const escaped = t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp(`\\b${escaped}\\b`, 'i').test(text);
    });
    if (found.length > 0) result[cat] = found;
  }

  return Object.keys(result).length > 0 ? result : null;
}
