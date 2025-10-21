'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

interface CompanySearchParams {
  query?: string;
  industry?: string;
  size?: string;
  location?: string;
}

interface CompanyFiltersProps {
  searchParams: CompanySearchParams;
  onFiltersChange: (params: Partial<CompanySearchParams>) => void;
}

export function CompanyFilters({ searchParams, onFiltersChange }: CompanyFiltersProps) {
  const [localFilters, setLocalFilters] = useState({
    industry: searchParams.industry || '',
    size: searchParams.size || '',
  });

  const industries = [
    { value: '', label: 'All Industries' },
    { value: 'technology', label: 'Technology' },
    { value: 'finance', label: 'Finance' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'retail', label: 'Retail' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'consulting', label: 'Consulting' },
    { value: 'media', label: 'Media & Entertainment' },
  ];

  const companySizes = [
    { value: '', label: 'All Sizes' },
    { value: 'startup', label: 'Startup (1-50)' },
    { value: 'small', label: 'Small (51-200)' },
    { value: 'medium', label: 'Medium (201-1000)' },
    { value: 'large', label: 'Large (1001-5000)' },
    { value: 'enterprise', label: 'Enterprise (5000+)' },
  ];

  const handleFilterChange = (key: string, value: string) => {
    const updatedFilters = { ...localFilters, [key]: value };
    setLocalFilters(updatedFilters);
    onFiltersChange(updatedFilters);
  };

  const clearFilters = () => {
    const clearedFilters = {
      industry: '',
      size: '',
    };
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const hasActiveFilters = Object.values(localFilters).some(value => value !== '');

  return (
    <div className="space-y-6">
      {/* Industry */}
      <div>
        <Label className="text-sm font-medium text-gray-900 mb-3 block">
          Industry
        </Label>
        <div className="space-y-2">
          {industries.map((industry) => (
            <label key={industry.value} className="flex items-center">
              <input
                type="radio"
                name="industry"
                value={industry.value}
                checked={localFilters.industry === industry.value}
                onChange={(e) => handleFilterChange('industry', e.target.value)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">{industry.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Company Size */}
      <div>
        <Label className="text-sm font-medium text-gray-900 mb-3 block">
          Company Size
        </Label>
        <div className="space-y-2">
          {companySizes.map((size) => (
            <label key={size.value} className="flex items-center">
              <input
                type="radio"
                name="size"
                value={size.value}
                checked={localFilters.size === size.value}
                onChange={(e) => handleFilterChange('size', e.target.value)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">{size.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <div className="pt-4 border-t border-gray-200">
          <Button
            variant="outline"
            onClick={clearFilters}
            className="w-full"
          >
            Clear All Filters
          </Button>
        </div>
      )}
    </div>
  );
}