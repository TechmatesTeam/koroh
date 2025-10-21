'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GroupSearchFilters } from '@/types/peer-groups';

interface PeerGroupFiltersProps {
  filters: GroupSearchFilters;
  onFiltersChange: (filters: GroupSearchFilters) => void;
  className?: string;
}

const PeerGroupFilters: React.FC<PeerGroupFiltersProps> = ({
  filters,
  onFiltersChange,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const groupTypes = [
    { value: 'industry', label: 'Industry' },
    { value: 'skill', label: 'Skill-based' },
    { value: 'location', label: 'Location' },
    { value: 'experience', label: 'Experience Level' },
    { value: 'interest', label: 'Interest' },
    { value: 'company', label: 'Company Alumni' },
    { value: 'education', label: 'Educational' },
    { value: 'general', label: 'General' },
  ];

  const privacyLevels = [
    { value: 'public', label: 'Public' },
    { value: 'restricted', label: 'Restricted' },
    { value: 'private', label: 'Private' },
  ];

  const industries = [
    'Technology',
    'Healthcare',
    'Finance',
    'Education',
    'Marketing',
    'Design',
    'Engineering',
    'Sales',
    'Consulting',
    'Startup',
    'Non-profit',
    'Government',
  ];

  const memberRanges = [
    { min: 1, max: 10, label: '1-10 members' },
    { min: 11, max: 50, label: '11-50 members' },
    { min: 51, max: 200, label: '51-200 members' },
    { min: 201, max: 1000, label: '201-1000 members' },
    { min: 1001, max: undefined, label: '1000+ members' },
  ];

  const handleFilterChange = (key: keyof GroupSearchFilters, value: any) => {
    const newFilters = { ...filters };
    if (value === '' || value === null || value === undefined) {
      delete newFilters[key];
    } else {
      newFilters[key] = value;
    }
    onFiltersChange(newFilters);
  };

  const handleMemberRangeChange = (min: number, max?: number) => {
    const newFilters = { ...filters };
    if (min === 1 && max === undefined) {
      delete newFilters.min_members;
      delete newFilters.max_members;
    } else {
      newFilters.min_members = min;
      if (max !== undefined) {
        newFilters.max_members = max;
      } else {
        delete newFilters.max_members;
      }
    }
    onFiltersChange(newFilters);
  };

  const clearAllFilters = () => {
    onFiltersChange({});
  };

  const getActiveFiltersCount = () => {
    return Object.keys(filters).length;
  };

  const isFilterActive = (key: keyof GroupSearchFilters, value: any) => {
    return filters[key] === value;
  };

  const isMemberRangeActive = (min: number, max?: number) => {
    return filters.min_members === min && filters.max_members === max;
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        <div className="flex items-center space-x-2">
          {getActiveFiltersCount() > 0 && (
            <Badge variant="secondary">
              {getActiveFiltersCount()} active
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
      </div>

      {/* Active Filters Summary */}
      {getActiveFiltersCount() > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-2 mb-2">
            {filters.group_type && (
              <Badge variant="outline" className="flex items-center gap-1">
                Type: {groupTypes.find(t => t.value === filters.group_type)?.label}
                <button
                  onClick={() => handleFilterChange('group_type', null)}
                  className="ml-1 hover:text-red-600"
                >
                  ×
                </button>
              </Badge>
            )}
            {filters.industry && (
              <Badge variant="outline" className="flex items-center gap-1">
                Industry: {filters.industry}
                <button
                  onClick={() => handleFilterChange('industry', null)}
                  className="ml-1 hover:text-red-600"
                >
                  ×
                </button>
              </Badge>
            )}
            {filters.privacy && (
              <Badge variant="outline" className="flex items-center gap-1">
                Privacy: {privacyLevels.find(p => p.value === filters.privacy)?.label}
                <button
                  onClick={() => handleFilterChange('privacy', null)}
                  className="ml-1 hover:text-red-600"
                >
                  ×
                </button>
              </Badge>
            )}
            {(filters.min_members || filters.max_members) && (
              <Badge variant="outline" className="flex items-center gap-1">
                Members: {filters.min_members || 0}-{filters.max_members || '∞'}
                <button
                  onClick={() => {
                    handleFilterChange('min_members', null);
                    handleFilterChange('max_members', null);
                  }}
                  className="ml-1 hover:text-red-600"
                >
                  ×
                </button>
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="text-red-600 hover:text-red-700"
          >
            Clear all filters
          </Button>
        </div>
      )}

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="space-y-6">
          {/* Group Type */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Group Type</h4>
            <div className="flex flex-wrap gap-2">
              {groupTypes.map((type) => (
                <Button
                  key={type.value}
                  variant={isFilterActive('group_type', type.value) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleFilterChange('group_type', 
                    isFilterActive('group_type', type.value) ? null : type.value
                  )}
                >
                  {type.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Industry */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Industry</h4>
            <div className="flex flex-wrap gap-2">
              {industries.map((industry) => (
                <Button
                  key={industry}
                  variant={isFilterActive('industry', industry) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleFilterChange('industry', 
                    isFilterActive('industry', industry) ? null : industry
                  )}
                >
                  {industry}
                </Button>
              ))}
            </div>
          </div>

          {/* Privacy Level */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Privacy Level</h4>
            <div className="flex flex-wrap gap-2">
              {privacyLevels.map((privacy) => (
                <Button
                  key={privacy.value}
                  variant={isFilterActive('privacy', privacy.value) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleFilterChange('privacy', 
                    isFilterActive('privacy', privacy.value) ? null : privacy.value
                  )}
                >
                  {privacy.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Member Count */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Group Size</h4>
            <div className="flex flex-wrap gap-2">
              {memberRanges.map((range) => (
                <Button
                  key={`${range.min}-${range.max || 'max'}`}
                  variant={isMemberRangeActive(range.min, range.max) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleMemberRangeChange(range.min, range.max)}
                >
                  {range.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PeerGroupFilters;