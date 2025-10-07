// frontend/components/marketing/hero-section.tsx

import React from 'react';
import { Button } from '../custom-ui/extras/button';
import Image from 'next/image';

interface HeroSectionProps {
  headline?: string;
  subtext?: string;
  ctaText?: string;
  ctaAction?: () => void;
  heroImageSrc?: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  headline = 'AI Blog Writer',
  subtext = 'Generate high-quality, SEO-optimized blog content with AI in minutes.',
  ctaText = 'Get Started',
  ctaAction,
  heroImageSrc = '/images/hero-illustration.png',
}) => {
  return (
    <section className="relative bg-black text-white py-20 px-6 md:px-20 flex flex-col-reverse md:flex-row items-center justify-between gap-8">
      <div className="flex-1 flex flex-col gap-6">
        <h1 className="text-5xl md:text-6xl font-bold text-yellow-500">
          {headline}
        </h1>
        <p className="text-gray-300 text-lg md:text-xl max-w-xl">
          {subtext}
        </p>
        <div className="flex gap-4">
          <Button
            className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold px-6 py-3"
            onClick={ctaAction}
          >
            {ctaText}
          </Button>
          <Button
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-6 py-3"
            onClick={() => window.scrollTo({ top: 600, behavior: 'smooth' })}
          >
            Learn More
          </Button>
        </div>
      </div>
      <div className="flex-1 relative w-full h-80 md:h-96">
        <Image
          src={heroImageSrc}
          alt="Hero Illustration"
          fill
          className="object-contain"
          priority
        />
      </div>
    </section>
  );
};
