/**
 * Audit Results Panel - Displays comprehensive SEO audit results
 * Shows scores, issues, recommendations, and actionable insights
 * Designed for dark theme with mango yellow accents
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/custom-ui/extras/card';
import { Button } from '@/components/custom-ui/extras/button';
;
import { Badge } from '@/components/custom-ui/extras/badge';
import { Progress } from '@/components/custom-ui/extras/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/custom-ui/extras/tabs';
import { 
  AlertCircle, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  Download, 
  ExternalLink,
  ArrowRight,
  Shield,
  Globe,
  FileText,
  BarChart3
} from 'lucide-react';
import { SEOAudit, SEOIssue, SEORecommendation } from '@/types';
import { cn } from '@/lib/utils';

interface AuditResultsPanelProps {
  auditData: SEOAudit;
  onReaudit?: () => void;
  onExport?: (format: 'pdf' | 'csv') => void;
  className?: string;
}

export const AuditResultsPanel: React.FC<AuditResultsPanelProps> = ({
  auditData,
  onReaudit,
  onExport,
  className
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());

  const toggleIssueExpansion = (issueId: string) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedIssues(newExpanded);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 70) return 'text-yellow-400';
    if (score >= 50) return 'text-orange-400';
    return 'text-red-400';
  };

  const getScoreVariant = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    if (score >= 50) return 'secondary';
    return 'destructive';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'high': return <AlertTriangle className="w-4 h-4 text-orange-400" />;
      case 'medium': return <Info className="w-4 h-4 text-yellow-400" />;
      case 'low': return <Info className="w-4 h-4 text-blue-400" />;
      default: return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const severityCounts = auditData.issues.reduce((acc, issue) => {
    acc[issue.severity] = (acc[issue.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header Section */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-yellow-500/10">
                <BarChart3 className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <CardTitle className="text-white">SEO Audit Results</CardTitle>
                <CardDescription className="text-gray-400">
                  Comprehensive analysis of your website's SEO performance
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white"
                onClick={() => onExport?.('pdf')}
              >
                <Download className="w-4 h-4 mr-2" />
                Export PDF
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white"
                onClick={() => onExport?.('csv')}
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
              {onReaudit && (
                <Button
                  size="sm"
                  className="bg-yellow-500 text-gray-900 hover:bg-yellow-400"
                  onClick={onReaudit}
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Re-run Audit
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Overall Score */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="w-20 h-20">
                    <svg className="w-full h-full" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#333"
                        strokeWidth="3"
                      />
                      <path
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke={auditData.overall_score >= 70 ? '#eab308' : '#ef4444'}
                        strokeWidth="3"
                        strokeDasharray={`${auditData.overall_score}, 100`}
                      />
                    </svg>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className={cn(
                      "text-2xl font-bold",
                      getScoreColor(auditData.overall_score)
                    )}>
                      {auditData.overall_score}
                    </span>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Overall Score</h3>
                  <p className="text-gray-400 text-sm">
                    {auditData.overall_score >= 90 ? 'Excellent' :
                     auditData.overall_score >= 70 ? 'Good' :
                     auditData.overall_score >= 50 ? 'Needs Improvement' : 'Poor'}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Severity Breakdown */}
            <div className="col-span-1 md:col-span-2">
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(severityCounts).map(([severity, count]) => (
                  <div key={severity} className="flex items-center gap-2 p-3 rounded-lg bg-gray-800">
                    {getSeverityIcon(severity)}
                    <div>
                      <div className="text-white font-medium capitalize">{severity}</div>
                      <div className="text-gray-400 text-sm">{count} issues</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-gray-900 border border-gray-800 p-1">
          <TabsTrigger 
            value="overview" 
            className="data-[state=active]:bg-yellow-500 data-[state=active]:text-gray-900"
          >
            <Globe className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger 
            value="issues" 
            className="data-[state=active]:bg-yellow-500 data-[state=active]:text-gray-900"
          >
            <AlertCircle className="w-4 h-4 mr-2" />
            Issues ({auditData.issues.length})
          </TabsTrigger>
          <TabsTrigger 
            value="recommendations" 
            className="data-[state=active]:bg-yellow-500 data-[state=active]:text-gray-900"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Recommendations ({auditData.recommendations.length})
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Critical Issues Summary */}
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-lg flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  Critical Issues
                </CardTitle>
              </CardHeader>
              <CardContent>
                {auditData.issues.filter(issue => issue.severity === 'critical').slice(0, 3).map((issue) => (
                  <div key={issue.type} className="mb-3 last:mb-0">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-4 h-4 text-red-400 mt-1 flex-shrink-0" />
                      <div className="flex-1">
                        <h4 className="text-white text-sm font-medium">{issue.type}</h4>
                        <p className="text-gray-400 text-xs">{issue.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {auditData.issues.filter(issue => issue.severity === 'critical').length === 0 && (
                  <div className="text-center py-4">
                    <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
                    <p className="text-gray-400">No critical issues found</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Top Recommendations */}
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-lg flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  Top Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                {auditData.recommendations.filter(rec => rec.priority === 'high').slice(0, 3).map((rec) => (
                  <div key={rec.description} className="mb-3 last:mb-0">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="w-4 h-4 text-green-400 mt-1 flex-shrink-0" />
                      <div className="flex-1">
                        <h4 className="text-white text-sm font-medium">High Priority</h4>
                        <p className="text-gray-400 text-xs">{rec.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button className="bg-yellow-500 text-gray-900 hover:bg-yellow-400 h-14">
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Fix Plan
                </Button>
                <Button variant="outline" className="border-gray-700 text-white hover:bg-gray-800 h-14">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Detailed Report
                </Button>
                <Button variant="outline" className="border-gray-700 text-white hover:bg-gray-800 h-14">
                  <Download className="w-4 h-4 mr-2" />
                  Export Full Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Issues Tab */}
        <TabsContent value="issues">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">SEO Issues</CardTitle>
              <CardDescription className="text-gray-400">
                {auditData.issues.length} issues found in your website
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {auditData.issues.map((issue) => (
                  <div
                    key={issue.type}
                    className="rounded-lg border border-gray-800 p-4 hover:border-gray-700 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      {getSeverityIcon(issue.severity)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-white font-medium">{issue.type}</h3>
                          <Badge
                            variant={getScoreVariant(
                              issue.severity === 'critical' ? 40 :
                              issue.severity === 'high' ? 60 :
                              issue.severity === 'medium' ? 70 : 80
                            )}
                            className="capitalize"
                          >
                            {issue.severity}
                          </Badge>
                        </div>
                        
                        <p className="text-gray-400 text-sm mb-3">{issue.description}</p>
                        
                        {issue.affected_urls && issue.affected_urls.length > 0 && (
                          <div className="mb-3">
                            <h4 className="text-white text-sm font-medium mb-2">Affected URLs:</h4>
                            <div className="space-y-1">
                              {issue.affected_urls.slice(0, 3).map((url) => (
                                <div key={url} className="flex items-center gap-2">
                                  <ExternalLink className="w-3 h-3 text-gray-500" />
                                  <span className="text-gray-400 text-xs font-mono truncate">
                                    {url}
                                  </span>
                                </div>
                              ))}
                              {issue.affected_urls.length > 3 && (
                                <span className="text-gray-500 text-xs">
                                  +{issue.affected_urls.length - 3} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        <div className="bg-gray-800 rounded-lg p-3">
                          <h4 className="text-white text-sm font-medium mb-2 flex items-center gap-2">
                            <ArrowRight className="w-3 h-3 text-yellow-400" />
                            Recommendation
                          </h4>
                          <p className="text-gray-400 text-sm">{issue.recommendation}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">SEO Recommendations</CardTitle>
              <CardDescription className="text-gray-400">
                {auditData.recommendations.length} recommendations to improve your SEO
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {auditData.recommendations.map((recommendation, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-gray-800 p-4 hover:border-gray-700 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className={cn(
                        "p-2 rounded-lg",
                        recommendation.priority === 'high' ? "bg-red-500/10" :
                        recommendation.priority === 'medium' ? "bg-yellow-500/10" :
                        "bg-blue-500/10"
                      )}>
                        <CheckCircle2 className={cn(
                          "w-4 h-4",
                          recommendation.priority === 'high' ? "text-red-400" :
                          recommendation.priority === 'medium' ? "text-yellow-400" :
                          "text-blue-400"
                        )} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-white font-medium">
                            {recommendation.priority === 'high' ? 'High Priority' :
                             recommendation.priority === 'medium' ? 'Medium Priority' : 'Low Priority'}
                          </h3>
                          <Badge
                            variant={
                              recommendation.priority === 'high' ? 'destructive' :
                              recommendation.priority === 'medium' ? 'warning' : 'secondary'
                            }
                          >
                            {recommendation.priority} priority
                          </Badge>
                        </div>
                        
                        <p className="text-gray-400 text-sm mb-3">{recommendation.description}</p>
                        
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>
                            <span className="text-gray-500">Estimated Impact:</span>
                            <span className="text-white ml-2">{recommendation.estimated_impact}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Implementation:</span>
                            <span className={cn(
                              "ml-2 capitalize",
                              recommendation.implementation_difficulty === 'easy' ? "text-green-400" :
                              recommendation.implementation_difficulty === 'medium' ? "text-yellow-400" :
                              "text-red-400"
                            )}>
                              {recommendation.implementation_difficulty}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};