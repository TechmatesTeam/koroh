'use client';

import { Company } from '@/types';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPinIcon,
  UsersIcon,
  GlobeAltIcon,
  HeartIcon,
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { useState } from 'react';

interface CompanyCardProps {
  company: Company;
  onFollow: () => void;
}

export function CompanyCard({ company, onFollow }: CompanyCardProps) {
  const [isFollowing, setIsFollowing] = useState(company.is_following);
  const [isLoading, setIsLoading] = useState(false);

  const handleFollow = async () => {
    setIsLoading(true);
    try {
      await onFollow();
      setIsFollowing(!isFollowing);
    } finally {
      setIsLoading(false);
    }
  };

  const getSizeLabel = (size: string) => {
    const sizeLabels: Record<string, string> = {
      startup: '1-50 employees',
      small: '51-200 employees',
      medium: '201-1000 employees',
      large: '1001-5000 employees',
      enterprise: '5000+ employees',
    };
    return sizeLabels[size] || size;
  };

  const getIndustryColor = (industry: string) => {
    const colors: Record<string, string> = {
      technology: 'bg-blue-100 text-blue-800',
      finance: 'bg-green-100 text-green-800',
      healthcare: 'bg-red-100 text-red-800',
      education: 'bg-purple-100 text-purple-800',
      retail: 'bg-orange-100 text-orange-800',
      manufacturing: 'bg-gray-100 text-gray-800',
      consulting: 'bg-indigo-100 text-indigo-800',
      media: 'bg-pink-100 text-pink-800',
    };
    return colors[industry] || 'bg-gray-100 text-gray-800';
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200 h-full">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            {company.logo ? (
              <img
                src={company.logo}
                alt={company.name}
                className="w-16 h-16 rounded-lg object-cover"
              />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-gray-200 flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-500">
                  {company.name.charAt(0)}
                </span>
              </div>
            )}
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 hover:text-indigo-600 cursor-pointer">
                {company.name}
              </h3>
              <Badge className={getIndustryColor(company.industry)}>
                {company.industry.charAt(0).toUpperCase() + company.industry.slice(1)}
              </Badge>
            </div>
          </div>
          
          <button
            onClick={handleFollow}
            disabled={isLoading}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            {isFollowing ? (
              <HeartSolidIcon className="h-6 w-6 text-red-500" />
            ) : (
              <HeartIcon className="h-6 w-6 text-gray-400" />
            )}
          </button>
        </div>

        {/* Company Details */}
        <div className="space-y-3 mb-4">
          <div className="flex items-center text-sm text-gray-600">
            <MapPinIcon className="h-4 w-4 mr-2" />
            <span>{company.location}</span>
          </div>
          
          <div className="flex items-center text-sm text-gray-600">
            <UsersIcon className="h-4 w-4 mr-2" />
            <span>{getSizeLabel(company.size)}</span>
          </div>
          
          {company.website && (
            <div className="flex items-center text-sm text-gray-600">
              <GlobeAltIcon className="h-4 w-4 mr-2" />
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-800 truncate"
              >
                {company.website.replace(/^https?:\/\//, '')}
              </a>
            </div>
          )}
        </div>

        {/* Company Description */}
        <p className="text-gray-700 text-sm line-clamp-3 mb-4">
          {company.description}
        </p>

        {/* Followers Count */}
        <div className="flex items-center text-sm text-gray-500">
          <HeartIcon className="h-4 w-4 mr-1" />
          <span>{company.followers_count} followers</span>
        </div>
      </CardContent>

      <CardFooter className="px-6 py-4 bg-gray-50 flex justify-between items-center">
        <Button variant="outline" size="sm">
          View Profile
        </Button>
        <Button
          onClick={handleFollow}
          disabled={isLoading}
          variant={isFollowing ? "outline" : "default"}
          size="sm"
        >
          {isLoading ? 'Loading...' : isFollowing ? 'Following' : 'Follow'}
        </Button>
      </CardFooter>
    </Card>
  );
}