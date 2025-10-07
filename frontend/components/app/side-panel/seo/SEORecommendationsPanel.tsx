"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/custom-ui/extras/card";
import { Badge } from "@/components/custom-ui/extras/badge";
import { CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import {
  useWebsites,
  useFetchAIRecommendations,
  useFetchPageSEOData,
} from "@/stores/use-user-store";

export const SEORecommendationsPanel: React.FC = () => {
  const websites = useWebsites();
  const fetchAIRecommendations = useFetchAIRecommendations();
  const fetchPageSEOData = useFetchPageSEOData(); // call the hook once
  const [pages, setPages] = useState<any[]>([]);

  const [recommendations, setRecommendations] = useState<any[]>([]);

const [selectedWebsiteId, setSelectedWebsiteId] = useState<string | null>(
  websites?.[0]?.id ?? null
);
const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
 

useEffect(() => {
  if (!selectedWebsiteId) return;

  const loadPages = async () => {
    const pagesData = await fetchPageSEOData(selectedWebsiteId); // fetch pages for selected website
    setPages(pagesData || []); // update state for page selector
    if (pagesData?.length) setSelectedPageId(pagesData[0].id); // pick first page as default
  };

  loadPages();
}, [selectedWebsiteId, fetchPageSEOData]);


  useEffect(() => {
    if (!selectedPageId) return;

    const loadRecommendations = async () => {
      const data = await fetchAIRecommendations(selectedPageId);
      setRecommendations(data || []);
    };

    loadRecommendations();
  }, [selectedPageId, fetchAIRecommendations]);

  const getPriorityIcon = (priority: string) => {
    return priority === "high" ? (
      <AlertTriangle className="w-4 h-4 text-red-400" />
    ) : (
      <Clock className="w-4 h-4 text-yellow-400" />
    );
  };

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="pb-4">
        <CardTitle className="text-white text-lg">
          Top Recommendations
        </CardTitle>
        <CardDescription className="text-gray-400">
          Priority actions to improve SEO
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
  {/* Website selector */}
  <select
    value={selectedWebsiteId || ""}
    onChange={(e) => setSelectedWebsiteId(e.target.value)}
    className="mb-2 p-2 rounded bg-gray-700 text-white"
  >
    {websites.map((w) => (
      <option key={w.id} value={w.id}>
        {w.domain}
      </option>
    ))}
  </select>

  {/* Page selector */}
  {selectedWebsiteId && (
    <select
      value={selectedPageId || ""}
      onChange={(e) => setSelectedPageId(e.target.value)}
      className="mb-4 p-2 rounded bg-gray-700 text-white"
    >
      {pages.map((p) => (
        <option key={p.id} value={p.id}>
          {p.title}
        </option>
      ))}
    </select>
  )}

  {/* Recommendations list */}
  {recommendations.map((rec) => (
    <div
      key={rec.id}
      className="flex items-center justify-between p-3 bg-gray-800 rounded-lg"
    >
      <div className="flex items-center gap-3">
        {rec.status === "completed" ? (
          <CheckCircle2 className="w-4 h-4 text-green-400" />
        ) : (
          getPriorityIcon(rec.priority)
        )}
        <div>
          <div className="text-white text-sm font-medium">{rec.title}</div>
          <div className="text-gray-400 text-xs">Impact: {rec.impact}</div>
        </div>
      </div>
      <Badge variant={rec.priority === "high" ? "destructive" : "warning"}>
        {rec.priority}
      </Badge>
    </div>
  ))}
</CardContent>
    </Card>
  );
};
