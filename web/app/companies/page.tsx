'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AppLayout } from '@/components/layout/app-layout';
import { CompanySearch } from '@/components/companies/company-search';
import { CompanyFilters } from '@/components/companies/company-filters';
import { CompanyList } from '@/components/companies/company-list';
import { CompanyInsights } from '@/components/companies/company-insights';
import { useCompanies } from '@/lib/hooks/use-companies';
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
  const [activeTab, setActiveTab] = useState('discover');
  
  const {
    companies,
    followedCompanies,
    companyInsights,
    searchParams,
    pagination,
    isLoading,
    error,
    search,
    setPage,
    followCompany,
  } = useCompanies();

  return (
    <ProtectedRoute>
      <AppLayout>
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
                      onFiltersChange={search}
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
                            <>Showing {companies.length} of {pagination.totalCount} companies</>
                          ) : (
                            'No companies found'
                          )}
                        </p>
                      </div>

                      {/* Company List */}
                      <CompanyList
                        companies={companies}
                        onCompanyFollow={followCompany}
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
          </TabsContent>

          <TabsContent value="following" className="space-y-6">
            <div className="max-w-4xl">
              <CompanyList
                companies={followedCompanies}
                onCompanyFollow={followCompany}
                onPageChange={() => {}}
                currentPage={1}
                totalCount={followedCompanies.length}
                pageSize={followedCompanies.length}
                showPagination={false}
              />
            </div>
          </TabsContent>

          <TabsContent value="insights" className="space-y-6">
            <CompanyInsights followedCompanies={followedCompanies} insights={companyInsights} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
      </AppLayout>
    </ProtectedRoute>
  );
}