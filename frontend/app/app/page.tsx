'use client';

import React from 'react';
import { Editor } from '@/components/app/main-editor/editor';

const AppPage = () => {
  const currentSite = 'montessorifund.com';

  return (
    <div className="min-h-screen bg-black text-white">
      <Editor currentSite={currentSite} />
    </div>
  );
};

export default AppPage;