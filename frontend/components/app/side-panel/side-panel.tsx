'use client'; 
import React from 'react';
import { BlogPost } from '@/lib/types';
import { SEOAudit } from '@/lib/types';
import { ContentQueue } from './blog-writer/content-queue'; 
import { AuditResultsPanel } from './blog-writer/audit-results-panel';
import { BlueprintPanel } from './blog-writer/blueprint-panel';
import { SEOAnalysisPanel } from './seo/SEOAnalysisPanel';
import { SEORecommendationsPanel } from './seo/SEORecommendationsPanel';
import { SEOActions } from './seo/SEOActions';
import { PixelStatus } from './seo/PixelStatus';

interface SidePanelProps {
  activePanel: 'content' | 'seo' | 'analytics';
  selectedPost: BlogPost | null;
  auditData?: SEOAudit;
  onPostSelect: (post: BlogPost) => void; 
}

export const SidePanel: React.FC<SidePanelProps> = ({
  activePanel,
  selectedPost,
  auditData,
  onPostSelect, 
}) => {
  const renderPanel = () => {
    switch (activePanel) {
      case 'content':
        return (
          <div className="space-y-6">
            <ContentQueue 
              selectedPost={selectedPost}
              onSelectPost={onPostSelect} 
            /> 
          </div>
        );
      

      case 'seo':
        return (
          <div className="space-y-6">
            <SEOActions />
            {auditData && <SEOAnalysisPanel auditData={auditData} />}
            <SEORecommendationsPanel />
            <PixelStatus />
          </div>
        );
      
      case 'analytics':
        return (
          <div className="space-y-6">
<BlueprintPanel
  urlId="dummy-id"
  isOpen={true}      // optional if you modified panel to always open
  onClose={() => console.log("closed")}
  onSave={(data) => console.log("saved", data)}
/>
            {auditData && <AuditResultsPanel auditData={auditData} />}
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      {renderPanel()}
    </div>
  );
};