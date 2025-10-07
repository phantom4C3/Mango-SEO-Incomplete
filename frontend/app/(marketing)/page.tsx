// frontend\app\(marketing)\page.tsx
'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useRef } from 'react';
import { useInView } from 'framer-motion';

// Trusted company logos (placeholder - replace with actual logos)
const trustedLogos = [
  { name: 'Forbes', logo: '/forbes-logo.svg' },
  { name: 'Semrush', logo: '/semrush-logo.svg' },
  { name: 'Search Engine Journal', logo: '/sej-logo.svg' },
  { name: 'HubSpot', logo: '/hubspot-logo.svg' },
  { name: 'WordPress', logo: '/wordpress-logo.svg' },
];

// Supported languages (sample)
const supportedLanguages = [
  'Arabic', 'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
  'Russian', 'Chinese', 'Japanese', 'Korean', 'Hindi', 'Turkish', 'Dutch',
  'Swedish', 'Polish', 'Ukrainian', 'Vietnamese', 'Thai', 'Indonesian'
];

// Testimonials
const testimonials = [
  {
    name: 'Brianna',
    role: 'Content Creator',
    content: 'SEO Bot AI has transformed how I create content. My traffic increased by 200% in just 3 months!',
    avatar: '/avatar-brianna.jpg'
  },
  {
    name: 'Michael',
    role: 'SEO Specialist',
    content: 'The AI-powered audits have saved me countless hours. I can now focus on strategy instead of manual work.',
    avatar: '/avatar-michael.jpg'
  },
  {
    name: 'Sarah',
    role: 'E-commerce Owner',
    content: 'Finally, an SEO tool that actually understands e-commerce needs. My product pages rank higher than ever.',
    avatar: '/avatar-sarah.jpg'
  },
];

// Pricing plans
const pricingPlans = [
  {
    name: 'Basic',
    price: '$19',
    period: 'month',
    description: 'Perfect for small blogs and personal websites',
    features: [
      '10 AI Articles per month',
      'Basic SEO Audits',
      'Keyword Research (50 queries)',
      'Content Optimization (10 pages)',
      'Email Support'
    ],
    cta: 'Get Started'
  },
  {
    name: 'Pro',
    price: '$49',
    period: 'month',
    description: 'Ideal for growing businesses and content teams',
    features: [
      '50 AI Articles per month',
      'Advanced SEO Audits',
      'Keyword Research (200 queries)',
      'Content Optimization (50 pages)',
      'Priority Support',
      'CMS Integrations'
    ],
    cta: 'Get Started',
    highlighted: true
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations with high-volume needs',
    features: [
      'Unlimited AI Articles',
      'Comprehensive SEO Audits',
      'Unlimited Keyword Research',
      'Content Optimization (Unlimited)',
      'Dedicated Account Manager',
      'API Access',
      'Custom Integrations'
    ],
    cta: 'Contact Sales'
  }
];

// FAQ items
const faqItems = [
  {
    question: 'What is SEO Bot AI?',
    answer: 'SEO Bot AI is the world\'s first AI-powered SEO suite that helps you create optimized content, perform SEO audits, conduct keyword research, and optimize existing content—all powered by advanced artificial intelligence.'
  },
  {
    question: 'How does the AI Content Writer work?',
    answer: 'Our AI Content Writer uses advanced natural language processing to create high-quality, SEO-optimized articles based on your keywords and topics. It researches the web, structures content logically, and ensures proper keyword density for optimal search engine rankings.'
  },
  {
    question: 'Can I integrate with my CMS?',
    answer: 'Yes! SEO Bot AI integrates with popular CMS platforms including WordPress, Webflow, Ghost, HubSpot, and many others. We also provide webhook and API access for custom integrations.'
  },
  {
    question: 'What languages are supported?',
    answer: 'We support over 50 languages including English, Spanish, French, German, Chinese, Japanese, Arabic, and many more. Our AI models are trained on multilingual data to ensure high-quality content in any supported language.'
  },
  {
    question: 'How often is the tool updated?',
    answer: 'We continuously update our AI models and algorithms to keep pace with the latest SEO trends and search engine algorithm changes. All customers receive these updates automatically.'
  }
];

// Animation variants
const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 2 }
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.18
    }
  }
};

// Component for animated sections
function Section({ children, className = '' }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <motion.section
      ref={ref}
      initial="initial"
      animate={isInView ? "animate" : "initial"}
      variants={staggerContainer}
      className={className}
    >
      {children}
    </motion.section>
  );
}

// Component for animated elements
function AnimatedElement({ children, variants = fadeIn, className = '' }) {
  return (
    <motion.div variants={variants} className={className}>
      {children}
    </motion.div>
  );
}

export default function LandingPage() {
  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-gradient-to-b from-black to-gray-900">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10">
          <AnimatedElement className="md:w-1/2">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              The World's First <span className="text-yellow-400">AI-Powered</span> SEO Suite
            </h1>
            <p className="text-xl text-gray-300 mb-8">
              Fully autonomous SEO robot with AI agents that creates content, performs audits, 
              researches keywords, and optimizes your content—all on autopilot.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="bg-yellow-400 text-black font-bold py-3 px-8 rounded-lg text-lg"
              >
                Start Your Journey
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="border border-yellow-400 text-yellow-400 font-bold py-3 px-8 rounded-lg text-lg"
              >
                View Demo
              </motion.button>
            </div>
            <div className="mt-10 flex flex-wrap gap-6 text-gray-400">
              <div className="flex items-center gap-2">
                <span className="text-yellow-400 font-bold text-xl">100k+</span>
                <span>Articles Created</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-yellow-400 font-bold text-xl">0.6B+</span>
                <span>Impressions</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-yellow-400 font-bold text-xl">15M+</span>
                <span>Clicks Generated</span>
              </div>
            </div>
          </AnimatedElement>
          <AnimatedElement className="md:w-1/2 mt-10 md:mt-0">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="bg-gray-800 rounded-xl p-2 border border-gray-700 shadow-2xl"
            >
              <div className="bg-gray-900 rounded-lg overflow-hidden">
                <div className="bg-gray-800 p-3 flex gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <div className="p-6">
                  <div className="animate-pulse flex space-x-4">
                    <div className="flex-1 space-y-4">
                      <div className="h-4 bg-gray-700 rounded w-3/4"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-700 rounded"></div>
                        <div className="h-4 bg-gray-700 rounded w-5/6"></div>
                      </div>
                      <div className="h-4 bg-gray-700 rounded w-2/3"></div>
                    </div>
                  </div>
                  <div className="mt-6 grid grid-cols-2 gap-4">
                    <div className="h-20 bg-gray-700 rounded-lg"></div>
                    <div className="h-20 bg-gray-700 rounded-lg"></div>
                    <div className="h-20 bg-gray-700 rounded-lg"></div>
                    <div className="h-20 bg-gray-700 rounded-lg"></div>
                  </div>
                </div>
              </div>
            </motion.div>
          </AnimatedElement>
        </div>
      </Section>

      {/* Trusted By Section */}
      <Section className="py-16 px-4 md:px-8 lg:px-16 bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">Trusted By Industry Leaders</h2>
            <p className="text-gray-400 max-w-3xl mx-auto">
              Join thousands of marketers, content creators, and SEO professionals who trust SEO Bot AI
            </p>
          </AnimatedElement>
          <AnimatedElement>
            <div className="flex flex-wrap justify-center gap-8 md:gap-16 items-center">
              {trustedLogos.map((company, index) => (
                <motion.div
                  key={index}
                  whileHover={{ scale: 1.1 }}
                  className="h-12 w-32 bg-gray-800 rounded-lg flex items-center justify-center p-2 opacity-70 hover:opacity-100 transition-opacity"
                >
                  <div className="text-gray-400 text-sm">{company.name}</div>
                </motion.div>
              ))}
            </div>
          </AnimatedElement>
        </div>
      </Section>

      {/* Features Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-black">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              AI-Powered SEO Tools To <span className="text-yellow-400">Grow Your Traffic</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Our suite of AI tools works together to automate your entire SEO process
            </p>
          </AnimatedElement>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                title: 'AI Content Writer',
                description: 'Create high-quality, SEO-optimized articles in minutes with our advanced AI writer',
                icon: '📝'
              },
              {
                title: 'AI SEO Audits',
                description: 'Get comprehensive site audits with actionable recommendations powered by AI',
                icon: '🔍'
              },
              {
                title: 'AI Keyword Research',
                description: 'Discover high-value keywords with AI-powered search intent analysis',
                icon: '🔎'
              },
              {
                title: 'AI Content Optimization',
                description: 'Optimize existing content for better rankings with AI recommendations',
                icon: '✨'
              }
            ].map((feature, index) => (
              <AnimatedElement key={index} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-yellow-400 transition-colors">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </AnimatedElement>
            ))}
          </div>
        </div>
      </Section>

      {/* Detailed Features Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">How SEO Bot AI Transforms Your SEO</h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Our AI agents work tirelessly to improve your search engine rankings
            </p>
          </AnimatedElement>

          {[
            {
              title: 'AI Content Writer',
              description: 'Our AI content writer creates engaging, SEO-optimized articles that rank. Simply provide a topic or keyword, and our AI will research, outline, and write a comprehensive article tailored to your audience.',
              features: [
                'Research-based content creation',
                'Automatic SEO optimization',
                'Multiple content tones and styles',
                'Plagiarism-free original content'
              ],
              image: '/ai-content-writer.svg',
              reverse: false
            },
            {
              title: 'AI SEO Audits',
              description: 'Get detailed technical SEO audits that identify issues and provide actionable solutions. Our AI analyzes your site structure, performance, metadata, and more to uncover optimization opportunities.',
              features: [
                'Comprehensive technical analysis',
                'Priority-based issue ranking',
                'Step-by-step fix instructions',
                'Continuous monitoring capabilities'
              ],
              image: '/ai-seo-audits.svg',
              reverse: true
            },
            {
              title: 'AI Keyword Research',
              description: 'Discover high-value keywords with AI-powered search intent analysis. Our tool identifies opportunities your competitors miss and helps you target the right keywords for your business.',
              features: [
                'Search intent classification',
                'Competition difficulty scoring',
                'Volume and trend analysis',
                'Content gap identification'
              ],
              image: '/ai-keyword-research.svg',
              reverse: false
            },
            {
              title: 'AI Content Optimization',
              description: 'Optimize existing content for better rankings with AI recommendations. Our tool analyzes your pages and provides specific suggestions to improve SEO performance and user engagement.',
              features: [
                'On-page SEO recommendations',
                'Content structure improvements',
                'Keyword usage optimization',
                'Readability enhancements'
              ],
              image: '/ai-content-optimization.svg',
              reverse: true
            }
          ].map((feature, index) => (
            <AnimatedElement key={index} className={`mb-20 flex flex-col ${feature.reverse ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-10`}>
              <div className="md:w-1/2">
                <h3 className="text-2xl md:text-3xl font-bold mb-6">{feature.title}</h3>
                <p className="text-gray-400 mb-6">{feature.description}</p>
                <ul className="space-y-3">
                  {feature.features.map((item, i) => (
                    <li key={i} className="flex items-start">
                      <span className="text-yellow-400 mr-2">✓</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="md:w-1/2 bg-gray-800 rounded-xl h-80 flex items-center justify-center border border-gray-700">
                <div className="text-gray-500 text-center">
                  <div className="text-6xl mb-4">📊</div>
                  <p>Visualization of {feature.title}</p>
                </div>
              </div>
            </AnimatedElement>
          ))}
        </div>
      </Section>

      {/* Use Cases Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-black">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">SEO Bot AI Is For Everyone</h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Whether you're a solo creator or part of a large team, our tools adapt to your needs
            </p>
          </AnimatedElement>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: 'Content Creators',
                description: 'Create engaging content faster without sacrificing quality',
                icon: '✍️'
              },
              {
                title: 'SEO Professionals',
                description: 'Scale your SEO efforts and deliver better results for clients',
                icon: '🔍'
              },
              {
                title: 'E-commerce Store Owners',
                description: 'Optimize product pages and category content for higher visibility',
                icon: '🛒'
              },
              {
                title: 'Small Business Owners',
                description: 'Compete with larger businesses through superior SEO',
                icon: '🏢'
              }
            ].map((useCase, index) => (
              <AnimatedElement key={index} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-yellow-400 transition-colors">
                <div className="text-4xl mb-4">{useCase.icon}</div>
                <h3 className="text-xl font-bold mb-3">{useCase.title}</h3>
                <p className="text-gray-400">{useCase.description}</p>
              </AnimatedElement>
            ))}
          </div>
        </div>
      </Section>

      {/* Supported Languages Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Supported Languages</h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Create and optimize content in over 50 languages with our AI-powered platform
            </p>
          </AnimatedElement>

          <AnimatedElement>
            <div className="bg-gray-800 rounded-xl p-8 border border-gray-700">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {supportedLanguages.map((language, index) => (
                  <motion.div 
                    key={index}
                    whileHover={{ scale: 1.05 }}
                    className="bg-gray-900 py-3 px-4 rounded-lg text-center hover:bg-yellow-400 hover:text-black transition-colors cursor-default"
                  >
                    {language}
                  </motion.div>
                ))}
                <div className="bg-black py-3 px-4 rounded-lg text-center text-yellow-400 col-span-full mt-4">
                  +30 more languages supported
                </div>
              </div>
            </div>
          </AnimatedElement>
        </div>
      </Section>

      {/* Pricing Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-black">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Simple, Transparent Pricing</h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Choose the plan that works for you. All plans include full access to our AI-powered SEO tools.
            </p>
          </AnimatedElement>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {pricingPlans.map((plan, index) => (
              <AnimatedElement 
                key={index} 
                className={`bg-gray-900 rounded-xl p-8 border ${plan.highlighted ? 'border-yellow-400 relative' : 'border-gray-800'} flex flex-col`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-yellow-400 text-black px-4 py-1 rounded-full text-sm font-bold">
                    Most Popular
                  </div>
                )}
                <h3 className="text-2xl font-bold mb-4">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.period && <span className="text-gray-400">/{plan.period}</span>}
                </div>
                <p className="text-gray-400 mb-8">{plan.description}</p>
                <ul className="mb-10 space-y-3 flex-grow">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start">
                      <span className="text-yellow-400 mr-2">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`w-full py-3 rounded-lg font-bold ${plan.highlighted ? 'bg-yellow-400 text-black' : 'bg-gray-800 text-white border border-gray-700'}`}
                >
                  {plan.cta}
                </motion.button>
              </AnimatedElement>
            ))}
          </div>
        </div>
      </Section>

      {/* Testimonials Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Wall of Love</h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              See what our customers are saying about SEO Bot AI
            </p>
          </AnimatedElement>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <AnimatedElement key={index} className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center mr-4">
                    {testimonial.avatar ? (
                      <img src={testimonial.avatar} alt={testimonial.name} className="w-12 h-12 rounded-full" />
                    ) : (
                      <span className="text-xl">👤</span>
                    )}
                  </div>
                  <div>
                    <h4 className="font-bold">{testimonial.name}</h4>
                    <p className="text-gray-400 text-sm">{testimonial.role}</p>
                  </div>
                </div>
                <p className="text-gray-300">"{testimonial.content}"</p>
              </AnimatedElement>
            ))}
          </div>
        </div>
      </Section>

      {/* FAQ Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-black">
        <div className="max-w-7xl mx-auto">
          <AnimatedElement className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Frequently Asked Questions</h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Everything you need to know about SEO Bot AI
            </p>
          </AnimatedElement>

          <div className="max-w-4xl mx-auto">
            {faqItems.map((faq, index) => (
              <AnimatedElement key={index} className="mb-6 border-b border-gray-800 pb-6">
                <h3 className="text-xl font-bold mb-3">{faq.question}</h3>
                <p className="text-gray-400">{faq.answer}</p>
              </AnimatedElement>
            ))}
          </div>
        </div>
      </Section>

      {/* Final CTA Section */}
      <Section className="py-20 px-4 md:px-8 lg:px-16 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto text-center">
          <AnimatedElement>
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Transform Your SEO?</h2>
            <p className="text-xl text-gray-400 mb-10">
              Join thousands of marketers and content creators who use SEO Bot AI to save time and boost their rankings
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-yellow-400 text-black font-bold py-4 px-10 rounded-lg text-lg"
            >
              Start Your SEO Journey Now
            </motion.button>
            <p className="text-gray-500 mt-6">No credit card required. Free 7-day trial.</p>
          </AnimatedElement>
        </div>
      </Section>
    </div>
  );
}