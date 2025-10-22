/**
 * Detailed status endpoint for Next.js application monitoring
 *
 * Provides comprehensive system status information for monitoring systems.
 * Requirements: 1.1, 7.2
 */

import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const startTime = Date.now();

  try {
    // Collect comprehensive status information
    const statusInfo = {
      timestamp: new Date().toISOString(),
      service: "koroh-web",
      version: process.env.npm_package_version || "1.0.0",
      environment: process.env.NODE_ENV || "development",
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
        external: Math.round(process.memoryUsage().external / 1024 / 1024),
        rss: Math.round(process.memoryUsage().rss / 1024 / 1024),
      },
      performance: {
        responseTime: Date.now() - startTime,
        cpuUsage: process.cpuUsage(),
      },
      system: {
        platform: process.platform,
        arch: process.arch,
        nodeVersion: process.version,
        pid: process.pid,
      },
      request: {
        userAgent: request.headers.get("user-agent") || "unknown",
        origin: request.headers.get("origin") || "unknown",
        host: request.headers.get("host") || "unknown",
        method: request.method,
        url: request.url,
      },
      checks: {
        server: "healthy",
        nextjs: "healthy",
        memory:
          process.memoryUsage().heapUsed < 500 * 1024 * 1024
            ? "healthy"
            : "warning",
        uptime: process.uptime() > 30 ? "healthy" : "starting",
      },
      config: {
        port: process.env.PORT || "3000",
        hostname: process.env.HOSTNAME || "0.0.0.0",
        telemetryDisabled: process.env.NEXT_TELEMETRY_DISABLED === "1",
      },
    };

    // Calculate overall health status
    const healthyChecks = Object.values(statusInfo.checks).filter(
      (status) => status === "healthy"
    ).length;
    const totalChecks = Object.keys(statusInfo.checks).length;

    const overallStatus = {
      status:
        healthyChecks === totalChecks
          ? "healthy"
          : healthyChecks >= totalChecks * 0.75
          ? "degraded"
          : "unhealthy",
      healthyChecks,
      totalChecks,
      healthPercentage: Math.round((healthyChecks / totalChecks) * 100),
    };

    const responseData = {
      ...statusInfo,
      overall: overallStatus,
    };

    const httpStatus =
      overallStatus.status === "healthy"
        ? 200
        : overallStatus.status === "degraded"
        ? 206
        : 503;

    return NextResponse.json(responseData, {
      status: httpStatus,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    const errorResponse = {
      timestamp: new Date().toISOString(),
      service: "koroh-web",
      status: "error",
      error: error instanceof Error ? error.message : "Unknown error",
      checks: {
        server: "unhealthy",
        nextjs: "unhealthy",
      },
      overall: {
        status: "unhealthy",
        healthyChecks: 0,
        totalChecks: 2,
        healthPercentage: 0,
      },
    };

    return NextResponse.json(errorResponse, {
      status: 503,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
        "Content-Type": "application/json",
      },
    });
  }
}

// Support HEAD requests for simple status checks
export async function HEAD(request: NextRequest) {
  try {
    // Quick health check without detailed response
    const memoryUsage = process.memoryUsage().heapUsed;
    const isHealthy = memoryUsage < 500 * 1024 * 1024 && process.uptime() > 5;

    return new NextResponse(null, {
      status: isHealthy ? 200 : 503,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
      },
    });
  } catch (error) {
    return new NextResponse(null, { status: 503 });
  }
}
