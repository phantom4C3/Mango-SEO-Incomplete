"use client";

import React from "react";
import { motion } from "framer-motion";

const Loading = () => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black text-[#ffb600] z-50">
      <motion.div
        className="w-16 h-16 border-4 border-t-[#ffb600] border-gray-800 rounded-full"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
      />
    </div>
  );
};

export default Loading;
