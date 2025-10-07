'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/custom-ui/extras/card';
import { Progress } from '@/components/custom-ui/extras/progress';
import { Badge } from '@/components/custom-ui/extras/badge';
import { SEOAudit } from '@/types';
import { CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react';

interface SEOAnalysisPanelProps {
  auditData: SEOAudit;
}

export const SEOAnalysisPanel: React.FC<SEOAnalysisPanelProps> = ({ auditData }) => {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'high': return <AlertTriangle className="w-4 h-4 text-orange-400" />;
      case 'medium': return <Info className="w-4 h-4 text-yellow-400" />;
      default: return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="pb-4">
        <CardTitle className="text-white text-lg">SEO Analysis</CardTitle>
        <CardDescription className="text-gray-400">
          Current website performance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Score */}
        <div className="flex items-center justify-between">
          <span className="text-gray-300">Overall Score</span>
          <Badge variant="success" className={getScoreColor(auditData.overall_score)}>
            {auditData.overall_score}/100
          </Badge>
        </div>
        
        {/* Progress Bars */}
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Technical SEO</span>
            <span className="text-white">85%</span>
          </div>
          <Progress value={85} className="h-2" />
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Content Quality</span>
            <span className="text-white">72%</span>
          </div>
          <Progress value={72} className="h-2" />
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Backlinks</span>
            <span className="text-white">64%</span>
          </div>
          <Progress value={64} className="h-2" />
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="text-center p-3 bg-gray-800 rounded-lg">
            <div className="text-white font-bold">{auditData.issues.length}</div>
            <div className="text-gray-400 text-xs">Issues Found</div>
          </div>
          <div className="text-center p-3 bg-gray-800 rounded-lg">
            <div className="text-white font-bold">{auditData.recommendations.length}</div>
            <div className="text-gray-400 text-xs">Recommendations</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};