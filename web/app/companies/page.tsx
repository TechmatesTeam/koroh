'use client';

import { useState, useEffect } from 'react';
import { CompanySearch } from '@/components/companies/company-search';
import { CompanyFilters } from '@/components/companies/company-filters';
import { CompanyList } from '@/components/companies/company-list';
import { CompanyInsights } from '@/components/companies/company-insights';
import { api } from '@/lib/api';
import { Company, PaginatedResponse } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface CompanySearchParams {
  query?: string;
  industry?: string;
  size?: string;
  location?: string;
  page?: number;
  limit?: number;
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [followedCompanies, setFollowedCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState<CompanySearchParams>({
    query: '',
    industry: '',
    size: '',
    location: '',
    page: 1,
    limit: 20,
  });
  const [totalCount, setTotalCount] = useState(0);
  const [activeTab, setActiveTab] = useState('discover');

  // Load initial data
  useEffect(() => {
    loadCompanies();
    loadFollowedCompanies();
  }, []);

  // Load companies when search params change
  useEffect(() => {
    if (searchParams.query || searchParams.industry || searchParams.size || searchParams.location) {
      loadCompanies();
    }
  }, [searchParams]);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const response = await api.companies.search(searchParams);
      const data: PaginatedResponse<Company> = response.data;
      setCompanies(data.results);
      setTotalCount(data.count);
    } catch (error) {
      console.error('Error loading companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFollowedCompanies = async () => {
    try {
      // This would be a separate endpoint for followed companies
      const response = await api.companies.search({ following: true });
      setFollowedCompanies(response.data.results || []);
    } catch (error) {
      console.error('Error loading followed companies:', error);
    }
  };

  const handleSearch = (params: Partial<CompanySearchParams>) => {
    setSearchParams(prev => ({
      ...prev,
      ...params,
      page: 1, // Reset to first page on new search
    }));
  };

  const handlePageChange = (page: number) => {
    setSearchParams(prev => ({ ...prev, page }));
  };

  const handleCompanyFollow = async (companyId: string, isFollowing: boolean) => {
    try {
      if (isFollowing) {
        await api.companies.unfollow(companyId);
      } else {
        await api.companies.follow(companyId);
      }
      
      // Update the company in the list
      setCompanies(prev => prev.map(company => 
        company.id === companyId 
          ? { ...company, is_following: !isFollowing }
          : company
      ));
      
      // Reload followed companies if we're on that tab
      if (activeTab === 'following') {
        loadFollowedCompanies();
      }
    } catch (error) {
      console.error('Error updating company follow status:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Discover Companies</h1>
          <p className="mt-2 text-gray-600">
            Find and follow companies that align with your career goals and interests
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="discover">Discover</TabsTrigger>
            <TabsTrigger value="following">Following ({followedCompanies.length})</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="discover" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Filters Sidebar */}
              <div className="lg:col-span-1">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Filters</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CompanyFilters
                      searchParams={searchParams}
                      onFiltersChange={handleSearch}
                    />
                  </CardContent>
                </Card>
              </div>

              {/* Main Content */}
              <div className="lg:col-span-3">
                {/* Search Bar */}
                <div className="mb-6">
                  <CompanySearch
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
                            <>Showing {companies.length} of {totalCount} companies</>
                          ) : (
                            'No companies found'
                          )}
                        </p>
                      </div>

                      {/* Company List */}
                      <CompanyList
                        companies={companies}
                        onCompanyFollow={handleCompanyFollow}
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
          </TabsContent>

          <TabsContent value="following" className="space-y-6">
            <div className="max-w-4xl">
              <CompanyList
                companies={followedCompanies}
                onCompanyFollow={handleCompanyFollow}
                onPageChange={() => {}}
                currentPage={1}
                totalCount={followedCompanies.length}
                pageSize={followedCompanies.length}
                showPagination={false}
              />
            </div>
          </TabsContent>

          <TabsContent value="insights" className="space-y-6">
            <CompanyInsights followedCompanies={followedCompanies} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}