'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/custom-ui/extras/card';
import { Badge } from '@/components/custom-ui/extras/badge';
import { Activity, Zap, Copy } from 'lucide-react';
import { useConversationStore, useFetchPixelStatus } from '@/stores/use-conversation-store';
import type { PixelResponse } from '@/lib/types';

export const PixelStatus: React.FC = () => {
  const taskLogs = useConversationStore((state) => state.taskLogs);

  // 🔹 Get the fetch function directly from the store hook
  const fetchPixelStatus = useFetchPixelStatus();

  // 🔹 Get the latest pixel ID from your logs
  const latestPixelId = Object.keys(taskLogs).slice(-1)[0] || null;

  const [pixel, setPixel] = useState<PixelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!latestPixelId) return;

    const loadPixel = async () => {
      setLoading(true);
      const data = await fetchPixelStatus(latestPixelId);
      setPixel(data);
      setLoading(false);
    };

    loadPixel();
  }, [latestPixelId, fetchPixelStatus]);

  const handleCopy = () => {
    if (!pixel) return;
    navigator.clipboard.writeText(pixel.script_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="text-gray-400 text-center">Loading Pixel...</CardContent>
      </Card>
    );
  }

  if (!pixel) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="text-red-500 text-center">Pixel not found</CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="pb-4">
        <CardTitle className="text-white text-lg flex items-center gap-2">
          <Activity className="w-5 h-5 text-yellow-400" />
          SEO Pixel Status
        </CardTitle>
        <CardDescription className="text-gray-400">Real-time pixel details</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-300">Status</span>
          <Badge variant="success" className="bg-green-500">
            <Zap className="w-3 h-3 mr-1" />
            Active
          </Badge>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Pixel ID</span>
            <span className="text-white">{pixel.pixel_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Installation Instructions</span>
            <span className="text-white">{pixel.installation_instructions}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-gray-400 mb-1">Script Code</span>
            <div className="flex items-start justify-between bg-gray-800 rounded p-2">
              <pre className="text-white text-xs break-all max-h-40 overflow-y-auto w-full">{pixel.script_code}</pre>
              <button
                className="ml-2 p-1 bg-gray-700 hover:bg-gray-600 rounded"
                onClick={handleCopy}
                title="Copy to clipboard"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
            {copied && <span className="text-green-400 text-xs mt-1">Copied!</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
