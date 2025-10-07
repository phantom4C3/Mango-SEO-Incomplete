"use client";

import React from "react";
import { motion } from "framer-motion";

// Components
import {HeroSection} from "@/components/marketing/hero-section"
import CTASection from "@/components/marketing/cta-section";
import {Card} from "@/components/custom-ui/extras/card";

// Local array with all 14 features
const FEATURES = [
  {
    title: "AI-Powered Content Generation",
    description: `
Automatic research of website, audience, and keywords.
SEO-optimized article generation (Listicles, How-to Guides, Checklists, Q&A, Versus, Roundups, Ultimate Guides).
Article length: ~3000–4000 words (long-form).
Supports 50+ languages.
Rich media insertion: Images (Google Images- prefer nano banana model), YouTube video embeds, Tables & lists.
Automatic internal & external linking.
Backlinks (volume depends on plan, e.g., Enterprise).
Google scraping & research for top-performing competitor analysis.
Facts checking system with source citations.
Anti-hallucination reflection (reduces AI factual errors).
Anti-typo and grammar correction.
    `,
  },
  {
    title: "SEO Content Analysis & Blueprinting",
    description: `
Analyze top 10–30 Google results for a target keyword.
Generate a blueprint report including:
- Recommended headings (H2/H3 structure)
- Semantic keywords (LSI terms) to include
- Recommended optimal content length
- Questions to Answer (from Google PAA, forums, etc.)
- Sentiment analysis of top content
    `,
  },
  {
    title: "Content Planning & Scheduling",
    description: `
Create weekly content plans based on site analysis.
Users can approve, decline, or moderate AI-suggested articles.
Content scheduling tied to subscription tier (3–300 articles/month).
    `,
  },
  {
    title: "Content Lifecycle Management",
    description: `
Regular article updates to keep content fresh.
Monthly article re-linking for SEO (refreshes internal links).
    `,
  },
  {
    title: "SEO Auditing",
    description: `
Website crawling to detect issues such as missing meta tags, slow page speed, broken links, image optimization problems.
    `,
  },
  {
    title: "Keyword Research & Clustering",
    description: `
Find new keyword opportunities.
Keyword clustering: group related terms (e.g., “best coffee maker,” “coffee machine,” “coffee brewer”).
    `,
  },
  {
    title: "Rank Tracking",
    description: `
Track daily Google search rankings for target keywords.
Monitor impressions, clicks, CTR over time.
    `,
  },
  {
    title: "Internal Linking Engine",
    description: `
Automatically links new articles to relevant site pages.
Improves navigation and SEO structure.
    `,
  },
  {
    title: "CMS Integration & Auto-Sync",
    description: `
Auto-sync publishing directly to CMS.
Supported CMS: WordPress, Webflow, Ghost, Shopify, Wix, Notion, HubSpot, Framer, Bits & Bytes.
Developer Integrations: Next.js, REST API, Webhooks.
    `,
  },
  {
    title: "Analytics Dashboard",
    description: `
Usage stats: Articles generated, Impressions, Clicks, CTR.
Subscription details (plan, limits, renewals).
Notifications.
    `,
  },
  {
    title: "Subscription Management",
    description: `
Tiered pricing plans: Starter ($19/mo – 3 articles), Beginner ($49/mo – 9 articles), Pro ($99/mo – 20 articles), Ultimate ($199/mo – 50 articles), Enterprise ($499/mo – 100 articles + 20 backlinks/mo), Extra ($799/mo – 150 articles), Mega ($1499/mo – 300 articles).
All tiers include: ~3000 words/article, Images + YouTube videos, Backlinks + internal/external linking, Google scraping, fact-checking, anti-hallucination, Regular updates & monthly re-linking, CMS auto-sync + integrations.
Payment & billing handled via Lemon Squeezy, Stripe, or Dodo.
Supports subscription changes, cancellations, renewals.
    `,
  },
  {
    title: "User Profile & Settings",
    description: `
Displays: User information, Uploaded articles, Subscription status, Usage analytics.
Allows: CMS integration setup, Notification preferences.
    `,
  },
  {
    title: "Testing & Security (Platform Reliability)",
    description: `
Unit Tests: Jest + React Testing Library.
API Tests: Postman / Supertest.
Security Tests: OWASP ZAP vulnerability scanning.
Performance Tests: Lighthouse for speed & SEO.
    `,
  },
  {
    title: "Automated Onboarding",
    description: `
One-click onboarding (just URL + Go).
Auto research of site, audience, keywords.
Auto content plan generation.
Agent workflow (100s of tasks/jobs per article).
    `,
  },
];

const Page = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-black text-[#ffb600] font-sans"
    >
      {/* Hero Section */}
      <HeroSection
        data={{
          title: "MangoSEO Features",
          subtitle:
            "Discover all the tools you need to generate, optimize, and manage SEO-friendly content effortlessly.",
        }}
      />

      {/* Features List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-8">
        {FEATURES.map((feature, idx) => (
          <Card key={idx} title={feature.title} description={feature.description} />
        ))}
      </div>

      {/* Footer CTA */}
      <CTASection
        data={{
          title: "Ready to supercharge your SEO?",
          buttonText: "Get Started",
          link: "/signup",
        }}
      />
    </motion.div>
  );
};

export default Page;
