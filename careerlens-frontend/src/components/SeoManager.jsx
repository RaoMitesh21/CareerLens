import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const SITE_NAME = 'CareerLens';
const SITE_URL = 'https://www.careerlens.in';
const DEFAULT_IMAGE = 'https://careerlens-api-imy1.onrender.com/static/careerlens-logo.png';

const SEO_CONFIG = {
  '/': {
    title: 'CareerLens - AI Skill-Gap Analyzer',
    description:
      'Analyze resume fit, identify missing skills, and get personalized AI learning roadmaps for career growth.',
    allowIndex: true,
  },
  '/demo': {
    title: 'CareerLens Demo - Try Resume Analysis',
    description:
      'Explore the CareerLens demo to see resume-to-role skill-gap analysis and roadmap generation in action.',
    allowIndex: true,
  },
  '/signin': {
    title: 'Sign In - CareerLens',
    description: 'Sign in to CareerLens to continue your career analysis and roadmap journey.',
    allowIndex: false,
  },
  '/signup': {
    title: 'Sign Up - CareerLens',
    description: 'Create a CareerLens account to start AI-powered resume and skill-gap analysis.',
    allowIndex: true,
  },
};

function getSeoForPath(pathname) {
  return SEO_CONFIG[pathname] || {
    title: `${SITE_NAME}`,
    description:
      'CareerLens is an AI-powered platform for resume analysis, skill-gap insights, and career roadmaps.',
    allowIndex: false,
  };
}

function setMeta(selector, attribute, value) {
  let element = document.querySelector(selector);

  if (!element) {
    element = document.createElement('meta');
    element.setAttribute(attribute, selector.replace(/^meta\[(name|property)="|"\]$/g, ''));
    document.head.appendChild(element);
  }

  element.setAttribute('content', value);
}

export default function SeoManager() {
  const location = useLocation();

  useEffect(() => {
    const { pathname } = location;
    const pageSeo = getSeoForPath(pathname);
    const canonicalUrl = `${SITE_URL}${pathname}`;

    document.title = pageSeo.title;

    setMeta('meta[name="description"]', 'name', pageSeo.description);
    setMeta('meta[property="og:title"]', 'property', pageSeo.title);
    setMeta('meta[property="og:description"]', 'property', pageSeo.description);
    setMeta('meta[property="og:url"]', 'property', canonicalUrl);
    setMeta('meta[property="og:image"]', 'property', DEFAULT_IMAGE);
    setMeta('meta[name="twitter:title"]', 'name', pageSeo.title);
    setMeta('meta[name="twitter:description"]', 'name', pageSeo.description);
    setMeta('meta[name="twitter:image"]', 'name', DEFAULT_IMAGE);

    const robotsValue = pageSeo.allowIndex ? 'index, follow' : 'noindex, nofollow';
    setMeta('meta[name="robots"]', 'name', robotsValue);

    let canonicalLink = document.querySelector('link[rel="canonical"]');
    if (!canonicalLink) {
      canonicalLink = document.createElement('link');
      canonicalLink.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalLink);
    }
    canonicalLink.setAttribute('href', canonicalUrl);
  }, [location]);

  return null;
}
