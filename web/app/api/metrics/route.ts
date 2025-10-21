/**
 * Prometheus metrics endpoint for Next.js
 * 
 * This endpoint exposes Prometheus metrics for the frontend application
 * and handles client-side metric tracking.
 */

import { NextRequest, NextResponse } from 'next/server';
import { register } from 'prom-client';
import {
  trackPageView,
  trackUserInteraction,
  trackFeatureUsage,
  trackClientError
} from '@/lib/metrics';

export async function GET() {
  try {
    // Return Prometheus metrics
    const metrics = await register.metrics();
    
    return new NextResponse(metrics, {
      headers: {
        'Content-Type': register.contentType,
      },
    });
  } catch (error) {
    console.error('Error generating metrics:', error);
    return NextResponse.json(
      { error: 'Failed to generate metrics' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { type, data } = body;

    // Handle different metric types from client
    switch (type) {
      case 'page_view':
        trackPageView(data.page, data.userType);
        break;
        
      case 'user_interaction':
        trackUserInteraction(data.interactionType, data.component);
        break;
        
      case 'feature_usage':
        trackFeatureUsage(data.featureName, data.userType);
        break;
        
      case 'client_error':
        trackClientError(data.errorType, data.component);
        break;
        
      default:
        return NextResponse.json(
          { error: 'Unknown metric type' },
          { status: 400 }
        );
    }

    return NextResponse.json({ success: true });
    
  } catch (error) {
    console.error('Error tracking metric:', error);
    return NextResponse.json(
      { error: 'Failed to track metric' },
      { status: 500 }
    );
  }
}