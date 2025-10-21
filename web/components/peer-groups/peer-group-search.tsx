'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { GroupSearchParams } from '@/types/peer-groups';

interface PeerGroupSearchProps {
  onSearch: (params: GroupSearchParams) => void;
  loading?: boolean;
  placeholder?: string;
  className?: string;
}

const PeerGroupSearch: React.FC<PeerGroupSearchProps> = ({
  onSearch,
  loading = false,
  placeholder = "Search peer groups...",
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Trigger search when debounced query changes
  useEffect(() => {
    if (debouncedQuery !== undefined) {
      onSearch({ q: debouncedQuery });
    }
  }, [debouncedQuery, onSearch]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({ q: query });
  };

  const handleClear = () => {
    setQuery('');
    onSearch({ q: '' });
  };

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="pl-10 pr-20"
          disabled={loading}
        />

        <div className="absolute inset-y-0 right-0 flex items-center">
          {loading && (
            <div className="pr-3">
              <LoadingSpinner size="sm" />
            </div>
          )}
          
          {query && !loading && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="mr-1 h-8 w-8 p-0"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </Button>
          )}
        </div>
      </div>

      {/* Search suggestions or recent searches could go here */}
      {query && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
          <div className="p-2">
            <div className="text-sm text-gray-500 mb-2">Search suggestions:</div>
            <div className="space-y-1">
              <button
                type="button"
                onClick={() => {
                  setQuery(`${query} industry`);
                  onSearch({ q: `${query} industry` });
                }}
                className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 rounded"
              >
                {query} <span className="text-gray-400">industry</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setQuery(`${query} skills`);
                  onSearch({ q: `${query} skills` });
                }}
                className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 rounded"
              >
                {query} <span className="text-gray-400">skills</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setQuery(`${query} location`);
                  onSearch({ q: `${query} location` });
                }}
                className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 rounded"
              >
                {query} <span className="text-gray-400">location</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </form>
  );
};

export default PeerGroupSearch;