'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { PeerGroup, GroupSearchParams, GroupRecommendation } from '@/types/peer-groups';
import { api } from '@/lib/api';
import { useNotifications } from '@/contexts/notification-context';
import PeerGroupSearch from './peer-group-search';
import PeerGroupFilters from './peer-group-filters';
import PeerGroupList from './peer-group-list';
import PeerGroupCard from './peer-group-card';
import { Button } from '@/components/ui/button';
import { Tabs } from '@/components/ui/tabs';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

interface PeerGroupDiscoveryProps {
  className?: string;
}

const PeerGroupDiscovery: React.FC<PeerGroupDiscoveryProps> = ({
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'discover' | 'search' | 'trending'>('discover');
  const [groups, setGroups] = useState<PeerGroup[]>([]);
  const [recommendations, setRecommendations] = useState<GroupRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useState<GroupSearchParams>({});
  const [hasSearched, setHasSearched] = useState(false);
  const { addNotification } = useNotifications();

  // Load initial data based on active tab
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      switch (activeTab) {
        case 'discover':
          response = await api.peerGroups.discover({ limit: 20 });
          if (response.data.ai_powered) {
            setRecommendations(response.data.recommendations);
            setGroups(response.data.recommendations.map((r: GroupRecommendation) => r.group));
          } else {
            setGroups(response.data.recommendations.map((r: any) => r.group));
            setRecommendations([]);
          }
          break;
          
        case 'trending':
          response = await api.peerGroups.trending({ limit: 20 });
          setGroups(response.data);
          setRecommendations([]);
          break;
          
        case 'search':
          if (hasSearched) {
            await handleSearch(searchParams);
          } else {
            setGroups([]);
            setRecommendations([]);
          }
          break;
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load groups');
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to load peer groups'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = useCallback(async (params: GroupSearchParams) => {
    if (activeTab !== 'search') return;
    
    setLoading(true);
    setError(null);
    setSearchParams(params);
    setHasSearched(true);
    
    try {
      const response = await api.peerGroups.search({
        ...params,
        limit: 20
      });
      
      setGroups(response.data.results);
      setRecommendations([]);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Search failed');
      addNotification({
        type: 'error',
        title: 'Search Error',
        message: 'Failed to search peer groups'
      });
    } finally {
      setLoading(false);
    }
  }, [activeTab, addNotification]);

  const handleFiltersChange = useCallback((filters: any) => {
    const newParams = { ...searchParams, ...filters };
    setSearchParams(newParams);
    if (activeTab === 'search') {
      handleSearch(newParams);
    }
  }, [searchParams, activeTab, handleSearch]);

  const handleJoinSuccess = (updatedGroup: PeerGroup) => {
    // Update the group in the current list
    setGroups(prevGroups => 
      prevGroups.map(group => 
        group.id === updatedGroup.id ? updatedGroup : group
      )
    );
    
    // Update recommendations if they exist
    setRecommendations(prevRecs => 
      prevRecs.map(rec => 
        rec.group.id === updatedGroup.id 
          ? { ...rec, group: updatedGroup }
          : rec
      )
    );
  };

  const getTabContent = () => {
    switch (activeTab) {
      case 'discover':
        return (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Discover Groups for You
              </h2>
              <p className="text-gray-600">
                AI-powered recommendations based on your profile and interests
              </p>
            </div>
            
            {recommendations.length > 0 ? (
              <div className="space-y-4">
                {recommendations.map((recommendation) => (
                  <div key={recommendation.group.id} className="relative">
                    <PeerGroupCard
                      group={recommendation.group}
                      onJoinSuccess={handleJoinSuccess}
                    />
                    {recommendation.reason && (
                      <div className="mt-2 text-sm text-blue-600 bg-blue-50 p-2 rounded">
                        <strong>Why this group:</strong> {recommendation.reason}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <PeerGroupList
                groups={groups}
                loading={loading}
                error={error || undefined}
                emptyMessage="No personalized recommendations available. Try joining some groups or updating your profile."
                onJoinSuccess={handleJoinSuccess}
              />
            )}
          </div>
        );
        
      case 'search':
        return (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Search Groups
              </h2>
              <p className="text-gray-600">
                Find groups by name, topic, industry, or skills
              </p>
            </div>
            
            <div className="mb-6">
              <PeerGroupSearch
                onSearch={handleSearch}
                loading={loading}
                className="mb-4"
              />
              
              <PeerGroupFilters
                filters={searchParams}
                onFiltersChange={handleFiltersChange}
              />
            </div>
            
            <PeerGroupList
              groups={groups}
              loading={loading}
              error={error || undefined}
              emptyMessage={hasSearched ? "No groups match your search criteria." : "Enter a search term to find groups."}
              onJoinSuccess={handleJoinSuccess}
            />
          </div>
        );
        
      case 'trending':
        return (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Trending Groups
              </h2>
              <p className="text-gray-600">
                Popular and active groups in your network
              </p>
            </div>
            
            <PeerGroupList
              groups={groups}
              loading={loading}
              error={error || undefined}
              emptyMessage="No trending groups available at the moment."
              onJoinSuccess={handleJoinSuccess}
            />
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Tab Navigation */}
      <div className="mb-8">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('discover')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'discover'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Discover
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'search'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Search
          </button>
          <button
            onClick={() => setActiveTab('trending')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'trending'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Trending
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {getTabContent()}
    </div>
  );
};

export default PeerGroupDiscovery;