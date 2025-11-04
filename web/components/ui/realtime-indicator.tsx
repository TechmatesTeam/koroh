'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDashboardRealtime } from '@/lib/hooks/use-realtime';
import { Wifi, WifiOff, Activity } from 'lucide-react';

interface RealtimeIndicatorProps {
  className?: string;
  showStatus?: boolean;
  showActivity?: boolean;
}

export function RealtimeIndicator({ 
  className = '', 
  showStatus = true, 
  showActivity = false 
}: RealtimeIndicatorProps) {
  const [activityCount, setActivityCount] = useState(0);
  const [lastActivity, setLastActivity] = useState<Date | null>(null);
  
  const dashboardRealtime = useDashboardRealtime({
    autoConnect: true,
    onConnect: () => {
      console.log('Real-time connection established');
    },
    onDisconnect: () => {
      console.log('Real-time connection lost');
    }
  });

  // Track real-time activity
  useEffect(() => {
    if (!dashboardRealtime.connection) return;

    const handleActivity = () => {
      setActivityCount(prev => prev + 1);
      setLastActivity(new Date());
      
      // Reset activity indicator after 3 seconds
      setTimeout(() => {
        setActivityCount(prev => Math.max(0, prev - 1));
      }, 3000);
    };

    // Listen to all real-time events
    dashboardRealtime.on('job_recommendation_update', handleActivity);
    dashboardRealtime.on('company_update', handleActivity);
    dashboardRealtime.on('profile_update', handleActivity);
    dashboardRealtime.on('dashboard_refresh', handleActivity);

    return () => {
      dashboardRealtime.off('job_recommendation_update', handleActivity);
      dashboardRealtime.off('company_update', handleActivity);
      dashboardRealtime.off('profile_update', handleActivity);
      dashboardRealtime.off('dashboard_refresh', handleActivity);
    };
  }, [dashboardRealtime]);

  if (!showStatus && !showActivity) {
    return null;
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {showStatus && (
        <div className="flex items-center space-x-1">
          {dashboardRealtime.isConnected ? (
            <>
              <Wifi className="w-4 h-4 text-green-500" />
              <Badge variant="secondary" className="text-xs bg-green-100 text-green-800">
                Live
              </Badge>
            </>
          ) : dashboardRealtime.isConnecting ? (
            <>
              <div className="w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
              <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-800">
                Connecting
              </Badge>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-500" />
              <Badge variant="secondary" className="text-xs bg-red-100 text-red-800">
                Offline
              </Badge>
            </>
          )}
        </div>
      )}

      {showActivity && activityCount > 0 && (
        <div className="flex items-center space-x-1">
          <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
          <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-800">
            {activityCount} update{activityCount !== 1 ? 's' : ''}
          </Badge>
        </div>
      )}
    </div>
  );
}

interface RealtimeStatusProps {
  className?: string;
}

export function RealtimeStatus({ className = '' }: RealtimeStatusProps) {
  return (
    <RealtimeIndicator 
      className={className}
      showStatus={true}
      showActivity={true}
    />
  );
}

interface ActivityIndicatorProps {
  className?: string;
}

export function ActivityIndicator({ className = '' }: ActivityIndicatorProps) {
  return (
    <RealtimeIndicator 
      className={className}
      showStatus={false}
      showActivity={true}
    />
  );
}