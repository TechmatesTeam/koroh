/**
 * Health check endpoint for Next.js application
 *
 * Provides basic health status for load balancers and monitoring systems.
 * Requirements: 1.1, 7.2
 */

import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Basic health check - verify the application is running
    const healthData = {
      status: "healthy",
      timestamp: new Date().toISOString(),
      service: "koroh-web",
      version: process.env.npm_package_version || "1.0.0",
      environment: process.env.NODE_ENV || "development",
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
        external: Math.round(process.memoryUsage().external / 1024 / 1024),
      },
      checks: {
        server: "healthy",
        nextjs: "healthy",
      },
    };

    // Verify Next.js is working properly
    if (typeof window === "undefined") {
      healthData.checks.nextjs = "healthy";
    }

    return NextResponse.json(healthData, {
      status: 200,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
      },
    });
  } catch (error) {
    const errorData = {
      status: "unhealthy",
      timestamp: new Date().toISOString(),
      service: "koroh-web",
      error: error instanceof Error ? error.message : "Unknown error",
      checks: {
        server: "unhealthy",
        nextjs: "unhealthy",
      },
    };

    return NextResponse.json(errorData, {
      status: 503,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
      },
    });
  }
}

// Support HEAD requests for simple health checks
export async function HEAD(request: NextRequest) {
  try {
    return new NextResponse(null, { status: 200 });
  } catch (error) {
    return new NextResponse(null, { status: 503 });
  }
}
