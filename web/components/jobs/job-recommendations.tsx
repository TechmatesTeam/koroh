'use client';

import { Job } from '@/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPinIcon,
  BuildingOfficeIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface JobRecommendationsProps {
  jobs: Job[];
  onJobApply: (jobId: string) => void;
}

export function JobRecommendations({ jobs, onJobApply }: JobRecommendationsProps) {
  if (jobs.length === 0) {
    return (
      <div className="text-center py-8">
        <SparklesIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No recommendations yet</h3>
        <p className="mt-1 text-sm text-gray-500">
          Complete your profile to get personalized job recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <SparklesIcon className="h-5 w-5 text-indigo-600" />
        <span className="text-sm font-medium text-gray-900">AI Recommendations</span>
      </div>

      {jobs.slice(0, 5).map((job) => (
        <div
          key={job.id}
          className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors"
        >
          <div className="flex items-start gap-3">
            {job.company.logo && (
              <img
                src={job.company.logo}
                alt={job.company.name}
                className="w-8 h-8 rounded object-cover flex-shrink-0"
              />
            )}
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {job.title}
              </h4>
              <div className="flex items-center text-xs text-gray-600 mt-1">
                <BuildingOfficeIcon className="h-3 w-3 mr-1" />
                <span className="truncate">{job.company.name}</span>
              </div>
              <div className="flex items-center text-xs text-gray-600 mt-1">
                <MapPinIcon className="h-3 w-3 mr-1" />
                <span className="truncate">{job.location}</span>
              </div>
              
              {/* Match Score */}
              <div className="mt-2">
                <Badge className="bg-green-100 text-green-800 text-xs">
                  95% Match
                </Badge>
              </div>

              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs px-2 py-1 h-auto"
                >
                  View
                </Button>
                <Button
                  size="sm"
                  onClick={() => onJobApply(job.id)}
                  className="text-xs px-2 py-1 h-auto"
                >
                  Apply
                </Button>
              </div>
            </div>
          </div>
        </div>
      ))}

      {jobs.length > 5 && (
        <div className="text-center pt-4">
          <Button variant="outline" size="sm" className="w-full">
            View All Recommendations ({jobs.length})
          </Button>
        </div>
      )}
    </div>
  );
}