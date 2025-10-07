// frontend/components/blog/search-filter.tsx

import React, { useState } from 'react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { useCmsStore } from '../../stores/use-cms-store';

export const SearchFilter: React.FC = () => {
  const [query, setQuery] = useState('');
  const [keyword, setKeyword] = useState('');
  const [minWords, setMinWords] = useState<number | undefined>();
  const [maxWords, setMaxWords] = useState<number | undefined>();

  const filterArticles = useCmsStore((state) => state.filterArticles); // direct pipeline call

  const handleSearch = () => {
    filterArticles({
      query,
      keyword,
      minWords,
      maxWords,
    });
  };

  return (
    <div className="bg-black text-white p-4 rounded-md border border-gray-800 mb-4">
      <div className="flex flex-col md:flex-row gap-2">
        <Input
          placeholder="Search by title or content..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="bg-gray-900 text-white border-gray-700 focus:border-yellow-500 focus:ring-yellow-500"
        />
        <Input
          placeholder="Filter by keyword..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="bg-gray-900 text-white border-gray-700 focus:border-yellow-500 focus:ring-yellow-500"
        />
        <Input
          type="number"
          placeholder="Min words"
          value={minWords ?? ''}
          onChange={(e) => setMinWords(Number(e.target.value))}
          className="bg-gray-900 text-white border-gray-700 focus:border-yellow-500 focus:ring-yellow-500"
        />
        <Input
          type="number"
          placeholder="Max words"
          value={maxWords ?? ''}
          onChange={(e) => setMaxWords(Number(e.target.value))}
          className="bg-gray-900 text-white border-gray-700 focus:border-yellow-500 focus:ring-yellow-500"
        />
        <Button
          className="bg-yellow-500 hover:bg-yellow-400 text-black"
          onClick={handleSearch}
        >
          Apply
        </Button>
      </div>
    </div>
  );
};
