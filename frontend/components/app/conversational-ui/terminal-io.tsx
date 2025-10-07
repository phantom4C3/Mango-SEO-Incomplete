 // terminal-io.tsx
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useCurrentTask } from '@/stores/use-task-store';
import {
  useConversationStore,
  useConversationLogs,
  useRunSEOAnalysis,
} from '@/stores/use-conversation-store';
import { Button } from '../../custom-ui/extras/button';


interface TerminalIOProps {
  output?: string[];
  mode?: 'blog-generation' | 'seo-analysis'; // optional → defaults to blog-generation
}

export const TerminalIO: React.FC<TerminalIOProps> = ({
  mode = 'blog-generation',
}) => {
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [urlSubmitted, setUrlSubmitted] = useState(false);

  // Store hooks
  const taskLogs = useConversationLogs();
  const submitWebsite = useConversationStore((state) => state.submitWebsite);
  const runSEOAnalysis = useRunSEOAnalysis();
  const currentTask = useCurrentTask();
// In TerminalIO.tsx
const [output, setOutput] = useState<string[]>([]);
// Add this ref at the top
const containerRef = useRef<HTMLDivElement>(null);

// Update the useEffect for auto-scrolling
useEffect(() => {
  const unsubscribe = useConversationStore.subscribe((state) => {
    const logs = Object.values(state.taskLogs)
      .flat()
      // sort by timestamp if exists to keep order consistent
.sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp))
      .map((log) => `> ${log.message}`);

    setOutput(logs);

    // auto-scroll to latest
    setTimeout(() => {
      containerRef.current?.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }, 0);
  });

  return () => unsubscribe();
}, []);


  // Flatten logs for display
  const logs: string[] = Object.values(taskLogs)
    .flat()
    .map((log) => log.message);

    const handleUrlSubmit = async () => {
  console.log("handleUrlSubmit triggered"); // Step 1: Button click detected
  console.log("websiteUrl before trim:", websiteUrl);

  if (!websiteUrl.trim()) {
    console.log("No URL entered, exiting");
    return;
  }

  try {
    let normalizedUrl = websiteUrl.trim();
    if (!/^https?:\/\//i.test(normalizedUrl)) {
      normalizedUrl = `https://${normalizedUrl}`;
    }

    console.log("Normalized URL:", normalizedUrl);

    const url = new URL(normalizedUrl);
    if (!url.hostname) throw new Error("Invalid URL");
    console.log("Valid URL:", url.href);

    if (mode === 'blog-generation') {
      console.log("Mode: blog-generation → calling submitWebsite");
      await submitWebsite(url.href);
      console.log("submitWebsite call completed");
    } else if (mode === 'seo-analysis') {
      console.log("Mode: seo-analysis → calling runSEOAnalysis");
      await runSEOAnalysis({
        url: url.href,
        depth: 1,
        analysis_type: 'full',
        include_recommendations: true,
        include_performance: true,
        include_security: true,
        include_mobile: true
      });
      console.log("runSEOAnalysis call completed");
    }

    setUrlSubmitted(true);
    console.log("urlSubmitted set to true");

  } catch (err) {
    console.error("URL validation failed:", err);
    alert('Please enter a valid website URL.');
  }
};



  const buttonStyle = {
    background: 'linear-gradient(90deg, #FFB347, #FFCC33)',
    color: '#000',
  };

  return (
    <div className="bg-black rounded-lg p-4 h-full flex flex-col overflow-hidden font-mono text-sm relative">
      {/* Avatar */}
      <div className="absolute left-4 top-4 w-12 h-12 rounded-full bg-gray-700 border-2 border-yellow-400 overflow-hidden">
        <div className="w-full h-full bg-gradient-to-br from-yellow-400 to-orange-500"></div>
      </div>

      {/* Terminal Content */}
<div ref={containerRef} className="ml-16 flex-1 overflow-y-auto mb-4">
        {(output.length > 0 ? output : logs).map((line, index) => (
          <div key={index} className="text-green-400 mb-1">
            {line.startsWith('> ') ? (
              <span className="text-yellow-400">{line}</span>
            ) : line.startsWith('- ') ? (
              <span className="text-white">{line}</span>
            ) : (
              line
            )}
          </div>
        ))}
      </div>

      {/* Sticky Input */}
      <div className="mt-auto flex space-x-2 ">
        <input
  type="url"
  placeholder={
    mode === 'seo-analysis'
      ? 'Enter URL for SEO analysis...'
      : 'Enter your website URL...'
  }
  value={websiteUrl}
  onChange={(e) => setWebsiteUrl(e.target.value)}
  className="flex-1 p-3 rounded bg-white text-black placeholder-gray-500 border border-gray-400 focus:border-yellow-400 focus:outline-none"
/>

        <Button style={buttonStyle} onClick={handleUrlSubmit} className='hover:scale-105'>
          Submit
        </Button>
      </div>

      {/* Task Status */}
      <div className="mt-2 ml-16 text-yellow-400 text-sm">
        {currentTask ? (
          <>
          
            &gt; Task {currentTask.id} status: {currentTask.status}
            {currentTask.progressMessage
              ? ` — ${currentTask.progressMessage}`
              : ''}
          </>
        ) : (
          <>&gt; Autopilot is currently ENABLED</>
        )}
      </div>
    </div>
  );
};
 