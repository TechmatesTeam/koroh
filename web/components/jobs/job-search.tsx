'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { JobSearchParams } from '@/types';
import { MagnifyingGlassIcon, MapPinIcon } from '@heroicons/react/24/outline';

interface JobSearchProps {
  searchParams: JobSearchParams;
  onSearch: (params: Partial<JobSearchParams>) => void;
}

export function JobSearch({ searchParams, onSearch }: JobSearchProps) {
  const [localQuery, setLocalQuery] = useState(searchParams.query || '');
  const [localLocation, setLocalLocation] = useState(searchParams.location || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      query: localQuery,
      location: localLocation,
    });
  };

  const handleQuickSearch = (query: string) => {
    setLocalQuery(query);
    onSearch({ query, location: localLocation });
  };

  const popularSearches = [
    'Software Engineer',
    'Product Manager',
    'Data Scientist',
    'UX Designer',
    'Marketing Manager',
    'Sales Representative',
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Job Title/Keywords */}
          <div className="md:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Job title, keywords, or company"
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Location */}
          <div>
            <div className="relative">
              <MapPinIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="City, state, or remote"
                value={localLocation}
                onChange={(e) => setLocalLocation(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-center">
          <Button type="submit" size="lg" className="px-8">
            Search Jobs
          </Button>
        </div>
      </form>

      {/* Popular Searches */}
      <div className="mt-6">
        <p className="text-sm text-gray-600 mb-3">Popular searches:</p>
        <div className="flex flex-wrap gap-2">
          {popularSearches.map((search) => (
            <button
              key={search}
              onClick={() => handleQuickSearch(search)}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
            >
              {search}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}