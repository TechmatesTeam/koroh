"use client";

import { useState, useEffect } from "react";
import {
  CheckCircle,
  Loader2,
  AlertCircle,
  FileText,
  Sparkles,
  Globe,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface ProcessingStatus {
  stage: string;
  status: "processing" | "completed" | "failed";
  message: string;
  progress: number;
  updated_at: string;
}

interface CVProcessingProgressProps {
  onComplete?: () => void;
}

export function CVProcessingProgress({
  onComplete,
}: CVProcessingProgressProps) {
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    if (!isPolling) return;

    const pollStatus = async () => {
      try {
        const response = await api.profiles.getProcessingStatus();
        const processingStatus = response.data.processing_status;

        if (processingStatus && Object.keys(processingStatus).length > 0) {
          setStatus(processingStatus);

          // Stop polling if completed or failed
          if (
            processingStatus.status === "completed" ||
            processingStatus.status === "failed"
          ) {
            setIsPolling(false);
            if (processingStatus.status === "completed" && onComplete) {
              onComplete();
            }
          }
        }
      } catch (error) {
        console.error("Error fetching processing status:", error);
      }
    };

    // Poll immediately
    pollStatus();

    // Then poll every 2 seconds
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [isPolling, onComplete]);

  if (!status) {
    return null;
  }

  const stages = [
    {
      key: "cv_analysis",
      label: "CV Analysis",
      icon: FileText,
      description: "Analyzing your CV with AI",
    },
    {
      key: "portfolio_generation",
      label: "Portfolio Generation",
      icon: Globe,
      description: "Creating your portfolio",
    },
  ];

  const currentStageIndex = stages.findIndex((s) => s.key === status.stage);

  return (
    <Card className="w-full border-teal-200 bg-gradient-to-br from-teal-50 to-blue-50">
      <CardHeader>
        <CardTitle className="flex items-center text-teal-700">
          <Sparkles className="w-5 h-5 mr-2 animate-pulse" />
          Processing Your CV
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium text-gray-700">{status.message}</span>
            <span className="text-teal-600 font-semibold">
              {status.progress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-teal-500 to-blue-500 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>

        {/* Stage Indicators */}
        <div className="space-y-4">
          {stages.map((stage, index) => {
            const isActive = stage.key === status.stage;
            const isCompleted =
              index < currentStageIndex ||
              (isActive && status.status === "completed");
            const isFailed = isActive && status.status === "failed";
            const Icon = stage.icon;

            return (
              <div
                key={stage.key}
                className={`flex items-start space-x-3 p-3 rounded-lg transition-all ${
                  isActive
                    ? "bg-white shadow-md border-2 border-teal-300"
                    : isCompleted
                    ? "bg-green-50 border border-green-200"
                    : "bg-gray-50 border border-gray-200 opacity-60"
                }`}
              >
                <div className="flex-shrink-0 mt-1">
                  {isFailed ? (
                    <AlertCircle className="w-6 h-6 text-red-500" />
                  ) : isCompleted ? (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  ) : isActive ? (
                    <Loader2 className="w-6 h-6 text-teal-500 animate-spin" />
                  ) : (
                    <Icon className="w-6 h-6 text-gray-400" />
                  )}
                </div>
                <div className="flex-1">
                  <h4
                    className={`font-semibold ${
                      isActive
                        ? "text-teal-700"
                        : isCompleted
                        ? "text-green-700"
                        : "text-gray-600"
                    }`}
                  >
                    {stage.label}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {isActive ? status.message : stage.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Status Messages */}
        {status.status === "completed" && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              <p className="text-green-800 font-medium">
                All done! Your profile has been updated with insights from your
                CV.
              </p>
            </div>
          </div>
        )}

        {status.status === "failed" && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <div>
                <p className="text-red-800 font-medium">Processing failed</p>
                <p className="text-red-600 text-sm mt-1">{status.message}</p>
              </div>
            </div>
          </div>
        )}

        {/* Estimated Time */}
        {status.status === "processing" && (
          <div className="text-center text-sm text-gray-500">
            <p>This usually takes 30-60 seconds</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
