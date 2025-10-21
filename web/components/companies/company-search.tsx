'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MagnifyingGlassIcon, MapPinIcon } from '@heroicons/react/24/outline';

interface CompanySearchParams {
  query?: string;
  location?: string;
  industry?: string;
  size?: string;
}

interface CompanySearchProps {
  searchParams: CompanySearchParams;
  onSearch: (params: Partial<CompanySearchParams>) => void;
}

export function CompanySearch({ searchParams, onSearch }: CompanySearchProps) {
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

  const popularCompanies = [
    'Google',
    'Microsoft',
    'Apple',
    'Amazon',
    'Meta',
    'Netflix',
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Company name or industry"
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div>
            <div className="relative">
              <MapPinIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Location"
                value={localLocation}
                onChange={(e) => setLocalLocation(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </div>
        <div className="flex justify-center">
          <Button type="submit" size="lg" className="px-8">
            Search Companies
          </Button>
        </div>
      </form>
    </div>
  );
}