'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useNotifications } from '@/contexts/notification-context';
import { useDashboardRealtime } from '@/lib/hooks/use-realtime';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Bell, X, Briefcase, Building2, MapPin, Clock } from 'lucide-react';

interface JobUpdate {
  id: string;
  title: string;
  company: {
    name: string;
    logo?: string;
  };
  location: string;
  job_type: string;
  match_score?: number;
  posted_date: string;
  salary_range?: string;
  notification_type?: string;
}

interface RealtimeJobUpdatesProps {
  onJobUpdate?: (jobs: JobUpdate[]) => void;
  showNotifications?: boolean;
  className?: string;
}

export function RealtimeJobUpdates({ 
  onJobUpdate, 
  showNotifications = true,
  className = '' 
}: RealtimeJobUpdatesProps) {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  const [pendingUpdates, setPendingUpdates] = useState<JobUpdate[]>([]);
  const [showUpdateBanner, setShowUpdateBanner] = useState(false);

  const dashboardRealtime = useDashboardRealtime({
    autoConnect: !!user,
    onConnect: () => {
      console.log('Job updates WebSocket connected');
    }
  });

  useEffect(() => {
    if (!dashboardRealtime.connection) return;

    const handleJobRecommendationUpdate = (data: any) => {
      if (data.recommendations && data.recommendations.length > 0) {
        const newJobs = data.recommendations.map((job: any) => ({
          ...job,
          notification_type: 'recommendation'
        }));
        
        setPendingUpdates(prev => [...prev, ...newJobs]);
        setShowUpdateBanner(true);

        if (showNotifications) {
          addNotification({
            type: 'info',
            title: 'New Job Recommendations',
            message: `${newJobs.length} new job recommendations available!`,
            duration: 5000
          });
        }

        // Auto-apply updates after 10 seconds if user doesn't interact
        setTimeout(() => {
          applyUpdates();
        }, 10000);
      }
    };

    const handleCompanyUpdate = (data: any) => {
      if (data.type === 'new_job' && data.job) {
        const newJob = {
          ...data.job,
          notification_type: 'company_job'
        };
        
        setPendingUpdates(prev => [...prev, newJob]);
        setShowUpdateBanner(true);

        if (showNotifications) {
          addNotification({
            type: 'info',
            title: 'New Job Alert',
            message: `${data.job.company.name} posted: ${data.job.title}`,
            duration: 8000
          });
        }
      }
    };

    dashboardRealtime.on('job_recommendation_update', handleJobRecommendationUpdate);
    dashboardRealtime.on('company_update', handleCompanyUpdate);

    return () => {
      dashboardRealtime.off('job_recommendation_update', handleJobRecommendationUpdate);
      dashboardRealtime.off('company_update', handleCompanyUpdate);
    };
  }, [dashboardRealtime, addNotification, showNotifications]);

  const applyUpdates = () => {
    if (pendingUpdates.length > 0) {
      onJobUpdate?.(pendingUpdates);
      setPendingUpdates([]);
      setShowUpdateBanner(false);
    }
  };

  const dismissUpdates = () => {
    setPendingUpdates([]);
    setShowUpdateBanner(false);
  };

  if (!showUpdateBanner || pendingUpdates.length === 0) {
    return null;
  }

  return (
    <div className={`fixed top-20 right-4 z-50 max-w-md ${className}`}>
      <Card className="border-blue-200 bg-blue-50 shadow-lg">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-blue-600" />
              <h3 className="font-medium text-blue-900">
                New Job Updates
              </h3>
              <Badge className="bg-blue-600 text-white">
                {pendingUpdates.length}
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={dismissUpdates}
              className="h-6 w-6 p-0 text-blue-600 hover:text-blue-800"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-2 mb-4 max-h-60 overflow-y-auto">
            {pendingUpdates.slice(0, 3).map((job, index) => (
              <div key={`${job.id}-${index}`} className="bg-white rounded-lg p-3 border border-blue-200">
                <div className="flex items-start space-x-2">
                  <div className="flex-shrink-0">
                    {job.notification_type === 'recommendation' ? (
                      <Briefcase className="w-4 h-4 text-green-600 mt-0.5" />
                    ) : (
                      <Building2 className="w-4 h-4 text-blue-600 mt-0.5" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {job.title}
                    </p>
                    <p className="text-xs text-gray-600">
                      {job.company.name}
                    </p>
                    <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                      <span className="flex items-center">
                        <MapPin className="w-3 h-3 mr-1" />
                        {job.location}
                      </span>
                      {job.match_score && (
                        <span className="text-green-600 font-medium">
                          {Math.round(job.match_score)}% match
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {pendingUpdates.length > 3 && (
              <div className="text-center text-sm text-blue-600">
                +{pendingUpdates.length - 3} more updates
              </div>
            )}
          </div>

          <div className="flex space-x-2">
            <Button
              onClick={applyUpdates}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              size="sm"
            >
              View Updates
            </Button>
            <Button
              onClick={dismissUpdates}
              variant="outline"
              size="sm"
              className="border-blue-300 text-blue-700 hover:bg-blue-100"
            >
              Dismiss
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface JobUpdateBadgeProps {
  count: number;
  onClick?: () => void;
  className?: string;
}

export function JobUpdateBadge({ count, onClick, className = '' }: JobUpdateBadgeProps) {
  if (count === 0) return null;

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      className={`relative ${className}`}
    >
      <Bell className="w-4 h-4 mr-2" />
      Job Updates
      <Badge className="ml-2 bg-red-500 text-white">
        {count > 99 ? '99+' : count}
      </Badge>
    </Button>
  );
}