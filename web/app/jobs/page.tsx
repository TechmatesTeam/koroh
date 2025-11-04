'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { JobSearch } from '@/components/jobs/job-search';
import { JobFilters } from '@/components/jobs/job-filters';
import { JobList } from '@/components/jobs/job-list';
import { JobRecommendations } from '@/components/jobs/job-recommendations';
import { useJobs } from '@/lib/hooks/use-jobs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export default function JobsPage() {
  const {
    jobs,
    recommendations,
    searchParams,
    pagination,
    isLoading,
    error,
    search,
    setPage,
    applyToJob,
  } = useJobs();

  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Find Your Next Opportunity</h1>
          <p className="mt-2 text-gray-600">
            Discover jobs tailored to your skills and preferences with AI-powered recommendations
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Filters</CardTitle>
              </CardHeader>
              <CardContent>
                <JobFilters
                  searchParams={searchParams}
                  onFiltersChange={search}
                />
              </CardContent>
            </Card>

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <div className="mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Recommended for You</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <JobRecommendations
                      jobs={recommendations}
                      onJobApply={applyToJob}
                    />
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {/* Search Bar */}
            <div className="mb-6">
              <JobSearch
                searchParams={searchParams}
                onSearch={search}
              />
            </div>

            {/* Results */}
            <div className="space-y-6">
              {isLoading ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                <>
                  {/* Results Header */}
                  <div className="flex justify-between items-center">
                    <p className="text-gray-600">
                      {pagination.totalCount > 0 ? (
                        <>Showing {jobs.length} of {pagination.totalCount} jobs</>
                      ) : (
                        'No jobs found'
                      )}
                    </p>
                  </div>

                  {/* Job List */}
                  <JobList
                    jobs={jobs}
                    onJobApply={applyToJob}
                    onPageChange={setPage}
                    currentPage={pagination.page}
                    totalCount={pagination.totalCount}
                    pageSize={pagination.limit}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
      </AppLayout>
    </ProtectedRoute>
  );
}