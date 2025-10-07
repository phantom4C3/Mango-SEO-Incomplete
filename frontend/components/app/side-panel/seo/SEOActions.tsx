"use client";
 import {
  useConversationStore,
  useConversationIsLoading,
  useConversationLogs,
} from "@/stores/use-conversation-store";
import { useState } from "react";
import { useWebsites, useUserSettings } from "@/stores/use-user-store";
import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/custom-ui/extras/card";
import { Button } from "@/components/custom-ui/extras/button";
import { Search, Zap, Shield } from "lucide-react";

export const SEOActions: React.FC = () => {


  
  const runSEOAnalysis = useConversationStore((state) => state.runSEOAnalysis);
  const generateSEOPixel = useConversationStore(
    (state) => state.generateSEOPixel
  );
  const rollbackSEOPixel = useConversationStore(
    (state) => state.rollbackSEOPixel
  );
  const batchSEOAnalysis = useConversationStore(
    (state) => state.batchSEOAnalysis
  );
  const websites = useWebsites();

  const [selectedWebsiteId, setSelectedWebsiteId] = useState<string | null>(
  websites[0]?.id || null
);
const currentWebsite = websites.find(w => w.id === selectedWebsiteId) || null;
const currentUrl = currentWebsite?.domain;
const currentPixelId = currentWebsite?.seo_pixel_id;

  const isLoading = useConversationIsLoading();
  const taskLogs = useConversationLogs();

  if (!currentWebsite) {
    return (
      <div className="text-gray-400 p-4">
        No website selected for SEO actions
      </div>
    );
  }

  const [isModalOpen, setIsModalOpen] = useState(false);
  const handleAuditClick = async () => {
    if (!currentUrl) return;
    await runSEOAnalysis({ url: currentUrl });
  };

  const handleGeneratePixel = async () => {
    if (!currentUrl) return;
    await generateSEOPixel({ website_id: currentWebsite.id });
  };

const handleRollbackPixel = async () => {
  if (!currentUrl) return; // guard
  await rollbackSEOPixel({ website_id: currentWebsite.id, url: currentUrl });
};


   return (
    <>
    
{websites.length > 1 && (
  <div className="mb-3">
    <label className="block text-gray-400 mb-1">Select Website:</label>
    <select
      className="w-full p-2 rounded bg-gray-800 text-white border border-gray-700"
      value={selectedWebsiteId || ''}
      onChange={(e) => setSelectedWebsiteId(e.target.value)}
    >
      {websites.map((w) => (
        <option key={w.id} value={w.id}>
          {w.domain}
        </option>
      ))}
    </select>
  </div>
)}

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader className="pb-4">
          <CardTitle className="text-white text-lg flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            SEO Actions
          </CardTitle>
          <CardDescription className="text-gray-400">
            Quick actions to improve your SEO
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            className="w-full bg-yellow-500 text-gray-900 hover:bg-yellow-400"
            onClick={handleAuditClick}
            disabled={isLoading}
          >
            <Search className="w-4 h-4 mr-2" />
            Run SEO Audit
          </Button>

          <Button
            variant="outline"
            className="w-full border-gray-700 text-white hover:bg-gray-800"
            onClick={handleGeneratePixel}
            disabled={isLoading}
          >
            <Shield className="w-4 h-4 mr-2" />
            Generate SEO Pixel
          </Button>

          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700 text-white hover:bg-gray-800"
              onClick={() => setIsModalOpen(true)}
            >
              Keyword Research
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700 text-white hover:bg-gray-800"
              onClick={handleRollbackPixel}
              disabled={isLoading}
            >
              Competitor Analysis
            </Button>
          </div>
        </CardContent>
      </Card>





      {isModalOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="bg-gray-900 rounded-lg w-full max-w-3xl max-h-[80vh] overflow-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl text-white font-bold mb-4">SEO Task Logs</h2>
            <div className="space-y-2">
              {Object.entries(taskLogs).map(([taskId, logs]) => (
                <div key={taskId} className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-yellow-400 font-medium mb-1">
                    {taskId}
                  </div>
                  {logs.map((log, index) => (
                    <div key={index} className="text-gray-300 text-sm">
                      [{log.timestamp}] {log.message}
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                className="px-4 py-2 bg-yellow-500 text-black rounded hover:bg-yellow-400"
                onClick={() => setIsModalOpen(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
