'use client';

import { Job } from '@/types';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPinIcon,
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  ClockIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import { useState } from 'react';

interface JobCardProps {
  job: Job;
  onApply: () => void;
}

export function JobCard({ job, onApply }: JobCardProps) {
  const [isSaved, setIsSaved] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const handleApply = async () => {
    setIsApplying(true);
    try {
      await onApply();
    } finally {
      setIsApplying(false);
    }
  };

  const toggleSave = () => {
    setIsSaved(!isSaved);
    // TODO: Implement save/unsave job functionality
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
    return `${Math.ceil(diffDays / 30)} months ago`;
  };

  const getJobTypeColor = (jobType: string) => {
    const colors: Record<string, string> = {
      'full-time': 'bg-green-100 text-green-800',
      'part-time': 'bg-blue-100 text-blue-800',
      'contract': 'bg-purple-100 text-purple-800',
      'freelance': 'bg-orange-100 text-orange-800',
      'internship': 'bg-yellow-100 text-yellow-800',
      'remote': 'bg-indigo-100 text-indigo-800',
    };
    return colors[jobType] || 'bg-gray-100 text-gray-800';
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {job.company.logo && (
                <img
                  src={job.company.logo}
                  alt={job.company.name}
                  className="w-12 h-12 rounded-lg object-cover"
                />
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 hover:text-indigo-600 cursor-pointer">
                  {job.title}
                </h3>
                <div className="flex items-center text-gray-600">
                  <BuildingOfficeIcon className="h-4 w-4 mr-1" />
                  <span className="text-sm">{job.company.name}</span>
                </div>
              </div>
            </div>
          </div>
          
          <button
            onClick={toggleSave}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            {isSaved ? (
              <BookmarkSolidIcon className="h-5 w-5 text-indigo-600" />
            ) : (
              <BookmarkIcon className="h-5 w-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* Job Details */}
        <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
          <div className="flex items-center">
            <MapPinIcon className="h-4 w-4 mr-1" />
            <span>{job.location}</span>
          </div>
          
          {job.salary_range && (
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-4 w-4 mr-1" />
              <span>{job.salary_range}</span>
            </div>
          )}
          
          <div className="flex items-center">
            <ClockIcon className="h-4 w-4 mr-1" />
            <span>{formatDate(job.posted_date)}</span>
          </div>
        </div>

        {/* Job Type Badge */}
        <div className="mb-4">
          <Badge className={getJobTypeColor(job.job_type)}>
            {job.job_type.charAt(0).toUpperCase() + job.job_type.slice(1)}
          </Badge>
        </div>

        {/* Job Description */}
        <p className="text-gray-700 text-sm line-clamp-3 mb-4">
          {job.description}
        </p>

        {/* Requirements Preview */}
        {job.requirements && job.requirements.length > 0 && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-900 mb-2">Key Requirements:</p>
            <div className="flex flex-wrap gap-2">
              {job.requirements.slice(0, 3).map((requirement, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {requirement}
                </Badge>
              ))}
              {job.requirements.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{job.requirements.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="px-6 py-4 bg-gray-50 flex justify-between items-center">
        <Button variant="outline" size="sm">
          View Details
        </Button>
        <Button
          onClick={handleApply}
          disabled={isApplying}
          size="sm"
        >
          {isApplying ? 'Applying...' : 'Apply Now'}
        </Button>
      </CardFooter>
    </Card>
  );
}