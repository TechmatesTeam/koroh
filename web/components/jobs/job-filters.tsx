'use client';

import { useState } from 'react';
import { JobSearchParams } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface JobFiltersProps {
  searchParams: JobSearchParams;
  onFiltersChange: (params: Partial<JobSearchParams>) => void;
}

export function JobFilters({ searchParams, onFiltersChange }: JobFiltersProps) {
  const [localFilters, setLocalFilters] = useState({
    job_type: searchParams.job_type || '',
    salary_min: searchParams.salary_min || '',
    salary_max: searchParams.salary_max || '',
  });

  const jobTypes = [
    { value: '', label: 'All Types' },
    { value: 'full-time', label: 'Full-time' },
    { value: 'part-time', label: 'Part-time' },
    { value: 'contract', label: 'Contract' },
    { value: 'freelance', label: 'Freelance' },
    { value: 'internship', label: 'Internship' },
    { value: 'remote', label: 'Remote' },
  ];

  const handleFilterChange = (key: string, value: string | number) => {
    const updatedFilters = { ...localFilters, [key]: value };
    setLocalFilters(updatedFilters);
    
    // Convert salary values to numbers for the API
    const apiFilters = {
      ...updatedFilters,
      salary_min: updatedFilters.salary_min ? Number(updatedFilters.salary_min) : undefined,
      salary_max: updatedFilters.salary_max ? Number(updatedFilters.salary_max) : undefined,
    };
    
    onFiltersChange(apiFilters);
  };

  const clearFilters = () => {
    const clearedFilters = {
      job_type: '',
      salary_min: '',
      salary_max: '',
    };
    setLocalFilters(clearedFilters);
    
    const apiFilters = {
      job_type: '',
      salary_min: undefined,
      salary_max: undefined,
    };
    
    onFiltersChange(apiFilters);
  };

  const hasActiveFilters = Object.values(localFilters).some(value => value !== '');

  return (
    <div className="space-y-6">
      {/* Job Type */}
      <div>
        <Label className="text-sm font-medium text-gray-900 mb-3 block">
          Job Type
        </Label>
        <div className="space-y-2">
          {jobTypes.map((type) => (
            <label key={type.value} className="flex items-center">
              <input
                type="radio"
                name="job_type"
                value={type.value}
                checked={localFilters.job_type === type.value}
                onChange={(e) => handleFilterChange('job_type', e.target.value)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">{type.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Salary Range */}
      <div>
        <Label className="text-sm font-medium text-gray-900 mb-3 block">
          Salary Range (USD)
        </Label>
        <div className="space-y-3">
          <div>
            <Label htmlFor="salary_min" className="text-xs text-gray-600">
              Minimum
            </Label>
            <Input
              id="salary_min"
              type="number"
              placeholder="e.g. 50000"
              value={localFilters.salary_min}
              onChange={(e) => handleFilterChange('salary_min', e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="salary_max" className="text-xs text-gray-600">
              Maximum
            </Label>
            <Input
              id="salary_max"
              type="number"
              placeholder="e.g. 100000"
              value={localFilters.salary_max}
              onChange={(e) => handleFilterChange('salary_max', e.target.value)}
              className="mt-1"
            />
          </div>
        </div>
      </div>

      {/* Experience Level */}
      <div>
        <Label className="text-sm font-medium text-gray-900 mb-3 block">
          Experience Level
        </Label>
        <div className="space-y-2">
          {[
            { value: '', label: 'All Levels' },
            { value: 'entry', label: 'Entry Level' },
            { value: 'mid', label: 'Mid Level' },
            { value: 'senior', label: 'Senior Level' },
            { value: 'executive', label: 'Executive' },
          ].map((level) => (
            <label key={level.value} className="flex items-center">
              <input
                type="radio"
                name="experience_level"
                value={level.value}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">{level.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Date Posted */}
      <div>
        <Label className="text-sm font-medium text-gray-900 mb-3 block">
          Date Posted
        </Label>
        <div className="space-y-2">
          {[
            { value: '', label: 'Any time' },
            { value: '1', label: 'Past 24 hours' },
            { value: '7', label: 'Past week' },
            { value: '30', label: 'Past month' },
          ].map((date) => (
            <label key={date.value} className="flex items-center">
              <input
                type="radio"
                name="date_posted"
                value={date.value}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">{date.label}</span>
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