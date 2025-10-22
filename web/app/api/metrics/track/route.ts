import { NextRequest, NextResponse } from "next/server";

/**
 * API endpoint for tracking frontend metrics
 * Receives metrics from the frontend and processes them
 */
export async function POST(request: NextRequest) {
  try {
    const data = await request.json();

    // Validate required fields
    if (!data.type || !data.timestamp) {
      return NextResponse.json(
        { error: "Missing required fields: type, timestamp" },
        { status: 400 }
      );
    }

    // Add server-side context
    const enrichedData = {
      ...data,
      serverTimestamp: Date.now(),
      userAgent: request.headers.get("user-agent"),
      ip:
        request.headers.get("x-forwarded-for") ||
        request.headers.get("x-real-ip"),
      referer: request.headers.get("referer"),
    };

    // In a real implementation, you would:
    // 1. Send to CloudWatch via AWS SDK
    // 2. Store in a metrics database
    // 3. Send to analytics service

    // For now, we'll log the metrics (in production, send to CloudWatch)
    if (process.env.NODE_ENV === "production") {
      // Send to backend API for CloudWatch processing
      try {
        const backendUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        await fetch(`${backendUrl}/api/v1/metrics/frontend/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(enrichedData),
        });
      } catch (error) {
        console.error("Failed to send metrics to backend:", error);
      }
    } else {
      // In development, just log
      console.log("Frontend Metric:", enrichedData);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error processing metrics:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
