// frontend\app\app\layout.tsx 
import React, { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "../globals.css";
 

// Fonts
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Metadata for Next.js 13+
export const metadata = {
  title: "MangoSEO",
  description:
    "AI-powered SEO content generation, auditing, and optimization platform.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body
        className={`bg-black text-[#ffb600] antialiased ${geistSans.variable} ${geistMono.variable}`}
      >
        {children}
      </body>
    </html>
  );
}
