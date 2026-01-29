"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FiCheck,
  FiLoader,
  FiFileText,
  FiCpu,
  FiVideo,
  FiUploadCloud,
  FiAlertCircle,
} from "react-icons/fi";
import {
  getGenerationStatus,
  getGenerationDetails,
  generateManimCode,
  renderVideo,
  type GenerationStatusResponse,
  type ManimResponse,
  type VideoRenderResponse,
  type ContentResponse,
} from "@/lib/api";

interface ProcessingViewProps {
  generationId: string;
}

type ProcessingStep = {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "pending" | "processing" | "completed" | "failed";
};

const initialSteps: ProcessingStep[] = [
  { id: "content", label: "Processing Content", icon: FiFileText, status: "pending" },
  { id: "script", label: "Generating Educational Script", icon: FiCpu, status: "pending" },
  { id: "manim", label: "Creating Animation Code", icon: FiVideo, status: "pending" },
  { id: "render", label: "Rendering Video", icon: FiLoader, status: "pending" },
  { id: "upload", label: "Uploading to Cloud", icon: FiUploadCloud, status: "pending" },
];

export function ProcessingView({ generationId }: ProcessingViewProps) {
  const router = useRouter();
  const [steps, setSteps] = useState<ProcessingStep[]>(initialSteps);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  const updateStepStatus = useCallback((stepId: string, status: ProcessingStep["status"]) => {
    setSteps((prev) =>
      prev.map((step) => (step.id === stepId ? { ...step, status } : step))
    );
  }, []);

  const pollStatus = useCallback(async () => {
    try {
      const status: GenerationStatusResponse = await getGenerationStatus(generationId);
      
      if (status.status === "completed") {
        // Check if the new pipeline already generated the video
        try {
          const details: ContentResponse = await getGenerationDetails(generationId);
          
          // New pipeline: video_url is already available
          if (details.video_url) {
            updateStepStatus("content", "completed");
            updateStepStatus("script", "completed");
            updateStepStatus("manim", "completed");
            updateStepStatus("render", "completed");
            updateStepStatus("upload", "completed");
            setProgress(100);
            setVideoUrl(details.video_url);
            setIsPolling(false);
            return;
          }
          
          // Legacy flow: manim_code available but need to render
          if (details.manim_code) {
            updateStepStatus("content", "completed");
            updateStepStatus("script", "completed");
            updateStepStatus("manim", "completed");
            setCurrentStepIndex(3);
            setProgress(60);
            
            // Render video
            updateStepStatus("render", "processing");
            const videoResponse: VideoRenderResponse = await renderVideo(
              generationId,
              "medium_quality",
              30
            );
            
            updateStepStatus("render", "completed");
            updateStepStatus("upload", "completed");
            setProgress(100);
            setVideoUrl(videoResponse.s3_url || videoResponse.video_url);
            setIsPolling(false);
            return;
          }
        } catch (detailsErr) {
          console.error("Error fetching generation details:", detailsErr);
        }
        
        // Fallback: Legacy step-by-step flow
        updateStepStatus("content", "completed");
        updateStepStatus("script", "completed");
        setCurrentStepIndex(2);
        setProgress(40);

        // Generate Manim code
        updateStepStatus("manim", "processing");
        try {
          const manimResponse: ManimResponse = await generateManimCode(generationId);
          
          if (manimResponse.validation_passed) {
            updateStepStatus("manim", "completed");
            setCurrentStepIndex(3);
            setProgress(60);

            // Render video
            updateStepStatus("render", "processing");
            const videoResponse: VideoRenderResponse = await renderVideo(
              generationId,
              "medium_quality",
              30
            );
            
            updateStepStatus("render", "completed");
            setCurrentStepIndex(4);
            setProgress(80);

            // Upload complete (done by render endpoint)
            updateStepStatus("upload", "completed");
            setProgress(100);
            setVideoUrl(videoResponse.s3_url || videoResponse.video_url);
            setIsPolling(false);
          } else {
            setError(`Manim validation failed: ${manimResponse.validation_errors?.join(", ")}`);
            updateStepStatus("manim", "failed");
            setIsPolling(false);
          }
        } catch (manimErr) {
          console.error("Manim generation error:", manimErr);
          setError("Failed to generate animation code");
          updateStepStatus("manim", "failed");
          setIsPolling(false);
        }
      } else if (status.status === "processing") {
        updateStepStatus("content", "completed");
        updateStepStatus("script", "processing");
        setCurrentStepIndex(1);
        setProgress(Math.min(status.progress_percentage || 20, 35));
      } else if (status.status === "pending") {
        updateStepStatus("content", "processing");
        setProgress(10);
      } else if (status.status === "failed") {
        setError(status.error_message || "Generation failed");
        updateStepStatus(steps[currentStepIndex].id, "failed");
        setIsPolling(false);
      }
    } catch (err) {
      console.error("Polling error:", err);
      // Continue polling despite errors
    }
  }, [generationId, currentStepIndex, steps, updateStepStatus]);

  useEffect(() => {
    if (!isPolling) return;

    // Start initial content processing steps
    updateStepStatus("content", "processing");
    
    const interval = setInterval(pollStatus, 3000);
    pollStatus(); // Initial poll

    return () => clearInterval(interval);
  }, [isPolling, pollStatus, updateStepStatus]);

  const handleViewLesson = () => {
    router.push(`/dashboard/lessons/${generationId}?video=${encodeURIComponent(videoUrl || "")}`);
  };

  return (
    <div className="max-w-2xl mx-auto py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <h1
          className="text-3xl font-bold text-zinc-900 dark:text-white mb-4"
          style={{ fontFamily: "var(--font-playfair)" }}
        >
          {videoUrl ? "Your Lesson is Ready!" : "Creating Your Lesson"}
        </h1>
        <p className="text-zinc-500">
          {videoUrl
            ? "Your video lesson has been generated successfully."
            : "Please wait while we transform your content into an engaging video lesson."}
        </p>
      </motion.div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between text-sm text-zinc-500 mb-2">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} />
      </div>

      {/* Steps */}
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            {steps.map((step, index) => (
              <motion.div
                key={step.id}
                className={`flex items-center gap-4 p-4 rounded-2xl transition-colors ${
                  step.status === "processing"
                    ? "bg-blue-50 dark:bg-blue-950/30"
                    : step.status === "completed"
                    ? "bg-green-50 dark:bg-green-950/30"
                    : step.status === "failed"
                    ? "bg-red-50 dark:bg-red-950/30"
                    : "bg-zinc-50 dark:bg-zinc-800/50"
                }`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    step.status === "processing"
                      ? "bg-blue-500"
                      : step.status === "completed"
                      ? "bg-green-500"
                      : step.status === "failed"
                      ? "bg-red-500"
                      : "bg-zinc-300 dark:bg-zinc-700"
                  }`}
                >
                  <AnimatePresence mode="wait">
                    {step.status === "processing" ? (
                      <motion.div
                        key="loader"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <FiLoader className="w-5 h-5 text-white" />
                      </motion.div>
                    ) : step.status === "completed" ? (
                      <motion.div
                        key="check"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 500 }}
                      >
                        <FiCheck className="w-5 h-5 text-white" />
                      </motion.div>
                    ) : step.status === "failed" ? (
                      <FiAlertCircle className="w-5 h-5 text-white" />
                    ) : (
                      <step.icon className="w-5 h-5 text-zinc-500" />
                    )}
                  </AnimatePresence>
                </div>
                <div className="flex-1">
                  <p
                    className={`font-medium ${
                      step.status === "processing"
                        ? "text-blue-700 dark:text-blue-300"
                        : step.status === "completed"
                        ? "text-green-700 dark:text-green-300"
                        : step.status === "failed"
                        ? "text-red-700 dark:text-red-300"
                        : "text-zinc-500"
                    }`}
                  >
                    {step.label}
                  </p>
                  {step.status === "processing" && (
                    <motion.p
                      className="text-sm text-blue-500"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      In progress...
                    </motion.p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800"
        >
          <div className="flex items-center gap-3">
            <FiAlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-red-700 dark:text-red-300">{error}</p>
          </div>
        </motion.div>
      )}

      {/* Success actions */}
      {videoUrl && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 flex justify-center gap-4"
        >
          <Button onClick={handleViewLesson} size="lg">
            View Your Lesson
          </Button>
          <Button variant="outline" size="lg" onClick={() => router.push("/dashboard")}>
            Back to Dashboard
          </Button>
        </motion.div>
      )}
    </div>
  );
}
