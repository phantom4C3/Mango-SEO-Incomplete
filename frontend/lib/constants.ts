export const appName = 'MangoSEO';
export const appDescription = 'AI-powered content generation & SEO optimization platform';

export const content = {
  maxWordCount: 5000,
  minWordCount: 300,
  defaultStyle: 'Informative',
  defaultSeoTarget: 'High',
};

export const agents = {
  topic: 'topic-agent',
  style: 'style-agent',
  seoAnalysis: 'seo-analysis-agent',
  audit: 'audit-agent',
  customization: 'customization-agent',
  onboarding: 'onboarding-agent',
};

export const cmsStatus = {
  draft: 'draft',
  published: 'published',
  archived: 'archived',
};

export const featureFlags = {
  enableSeoAnalysis: true,
  enableAutoPublish: false,
  enableContentCustomization: true,
};

export const defaultPrompts = {
  topic: 'Generate content topics based on the given input',
  style: 'Apply the selected writing style and tone',
  seo: 'Analyze SEO and suggest improvements',
  audit: 'Check for readability, grammar, and compliance',
  customization: 'Apply user-specific customizations',
};

export const errorMessages = {
  cmsUpsertFailed: 'Failed to save CMS content',
  cmsFetchFailed: 'Failed to fetch CMS content',
  pipelineFailed: 'Content generation pipeline failed',
};

export const apiEndpoints = {
  cms: '/api/cms',
  aiBlogWriter: '/api/ai-worker/generate',
  seoAnalysis: '/api/seo',
  audit: '/api/audit',
};

export const timeouts = {
  defaultApi: 15000,
  longApi: 30000,
};

export const ui = {
  loadingSpinnerDelay: 300,
  toastDuration: 5000,
};


export const SAMPLE_BLOGPOSTS = [
  {
    title: "10 Tips for Boosting Your SEO in 2025",
    author: "MangoSEO AI",
    content: `Search engine optimization is essential for digital success. In this article, we explore 10 actionable strategies to improve your website's ranking, increase traffic, and drive conversions. From keyword research to backlink strategies, this guide covers everything you need to know.`,
    tags: ["SEO", "Digital Marketing", "Content Strategy"],
    status: "published",
  },
  {
    title: "The Ultimate Guide to Writing Engaging Blog Posts",
    author: "MangoSEO AI",
    content: `Writing blog posts that captivate readers requires strategy and creativity. Learn how to structure your posts, choose compelling headlines, and write content that keeps readers coming back for more.`,
    tags: ["Writing", "Content Creation", "Engagement"],
    status: "published",
  },
];
