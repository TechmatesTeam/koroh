'use client';

import { useState, useEffect } from 'react';
import { JobSearch } from '@/components/jobs/job-search';
import { JobFilters } from '@/components/jobs/job-filters';
import { JobList } from '@/components/jobs/job-list';
import { JobRecommendations } from '@/components/jobs/job-recommendations';
import { api } from '@/lib/api';
import { Job, JobSearchParams, PaginatedResponse } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [recommendations, setRecommendations] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState<JobSearchParams>({
    query: '',
    location: '',
    job_type: '',
    page: 1,
    limit: 20,
  });
  const [totalCount, setTotalCount] = useState(0);

  // Load initial data
  useEffect(() => {
    loadJobs();
    loadRecommendations();
  }, []);

  // Load jobs when search params change
  useEffect(() => {
    if (searchParams.query || searchParams.location || searchParams.job_type) {
      loadJobs();
    }
  }, [searchParams]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await api.jobs.search(searchParams);
      const data: PaginatedResponse<Job> = response.data;
      setJobs(data.results);
      setTotalCount(data.count);
    } catch (error) {
      console.error('Error loading jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async () => {
    try {
      const response = await api.jobs.getRecommendations();
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error loading recommendations:', error);
    }
  };

  const handleSearch = (params: Partial<JobSearchParams>) => {
    setSearchParams(prev => ({
      ...prev,
      ...params,
      page: 1, // Reset to first page on new search
    }));
  };

  const handlePageChange = (page: number) => {
    setSearchParams(prev => ({ ...prev, page }));
  };

  const handleJobApply = async (jobId: string) => {
    try {
      await api.jobs.apply(jobId);
      // Update job status or show success message
      console.log('Application submitted successfully');
    } catch (error) {
      console.error('Error applying to job:', error);
    }
  };

  return (
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
                  onFiltersChange={handleSearch}
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
                      onJobApply={handleJobApply}
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
                onSearch={handleSearch}
              />
            </div>

            {/* Results */}
            <div className="space-y-6">
              {loading ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                <>
                  {/* Results Header */}
                  <div className="flex justify-between items-center">
                    <p className="text-gray-600">
                      {totalCount > 0 ? (
                        <>Showing {jobs.length} of {totalCount} jobs</>
                      ) : (
                        'No jobs found'
                      )}
                    </p>
                  </div>

                  {/* Job List */}
                  <JobList
                    jobs={jobs}
                    onJobApply={handleJobApply}
                    onPageChange={handlePageChange}
                    currentPage={searchParams.page || 1}
                    totalCount={totalCount}
                    pageSize={searchParams.limit || 20}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}