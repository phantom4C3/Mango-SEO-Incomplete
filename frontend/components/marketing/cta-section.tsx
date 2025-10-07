'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface CTASectionProps {
  data: {
    title: string;
    buttonText: string;
    link: string;
  };
}

const CTASection: React.FC<CTASectionProps> = ({ data }) => {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900 py-16 px-6 text-center rounded-lg mx-4 mt-12"
    >
      <h2 className="text-3xl font-bold mb-6 text-yellow-400">{data.title}</h2>
      <a
        href={data.link}
        className="inline-block bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold px-6 py-3 rounded-md text-lg hover:scale-105 transition-transform duration-200"
      >
        {data.buttonText}
      </a>
    </motion.section>
  );
};

export default CTASection;
