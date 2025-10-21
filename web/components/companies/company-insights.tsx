'use client';

import { Company } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ArrowTrendingUpIcon,
  BriefcaseIcon,
  UsersIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

interface CompanyInsightsProps {
  followedCompanies: Company[];
}

export function CompanyInsights({ followedCompanies }: CompanyInsightsProps) {
  // Calculate insights from followed companies
  const industryDistribution = followedCompanies.reduce((acc, company) => {
    acc[company.industry] = (acc[company.industry] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sizeDistribution = followedCompanies.reduce((acc, company) => {
    acc[company.size] = (acc[company.size] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topIndustries = Object.entries(industryDistribution)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const topSizes = Object.entries(sizeDistribution)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  if (followedCompanies.length === 0) {
    return (
      <div className="text-center py-12">
        <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No insights available</h3>
        <p className="mt-1 text-sm text-gray-500">
          Follow some companies to see personalized insights and trends.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Overview Stats */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Companies Following</CardTitle>
          <UsersIcon className="h-4 w-4 text-gray-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{followedCompanies.length}</div>
          <p className="text-xs text-gray-600">
            Total companies you're tracking
          </p>
        </CardContent>
      </Card>

      {/* Total Followers */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Reach</CardTitle>
          <ArrowTrendingUpIcon className="h-4 w-4 text-gray-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {followedCompanies.reduce((sum, company) => sum + company.followers_count, 0).toLocaleString()}
          </div>
          <p className="text-xs text-gray-600">
            Combined followers of tracked companies
          </p>
        </CardContent>
      </Card>

      {/* Average Company Size */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg. Company Size</CardTitle>
          <BriefcaseIcon className="h-4 w-4 text-gray-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {topSizes[0]?.[0]?.charAt(0).toUpperCase() + (topSizes[0]?.[0]?.slice(1) || 'N/A')}
          </div>
          <p className="text-xs text-gray-600">
            Most common company size you follow
          </p>
        </CardContent>
      </Card>

      {/* Industry Distribution */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-lg">Industry Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {topIndustries.map(([industry, count]) => (
              <div key={industry} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {industry.charAt(0).toUpperCase() + industry.slice(1)}
                  </Badge>
                  <span className="text-sm text-gray-600">{count} companies</span>
                </div>
                <div className="flex-1 mx-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{
                        width: `${(count / followedCompanies.length) * 100}%`,
                      }}
                    />
                  </div>
                </div>
                <span className="text-sm font-medium">
                  {Math.round((count / followedCompanies.length) * 100)}%
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {followedCompanies.slice(0, 3).map((company) => (
              <div key={company.id} className="flex items-center gap-3">
                {company.logo ? (
                  <img
                    src={company.logo}
                    alt={company.name}
                    className="w-8 h-8 rounded object-cover"
                  />
                ) : (
                  <div className="w-8 h-8 rounded bg-gray-200 flex items-center justify-center">
                    <span className="text-xs font-bold text-gray-500">
                      {company.name.charAt(0)}
                    </span>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {company.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    Recently followed
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}