"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { StepForm } from "@/components/dashboard/step-form";
import { generateFromUrl } from "@/lib/api";
import { FiLink } from "react-icons/fi";
import { AUDIENCE_LABELS, type TargetAudience } from "@/types";

export default function UrlInputPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (data: {
    url?: string;
    topic: string;
    difficultyLevel: string;
    targetAudience: TargetAudience;
    learningGoals: string[];
  }) => {
    if (!data.url) return;

    setIsLoading(true);
    try {
      const response = await generateFromUrl({
        url: data.url,
        topic: data.topic || undefined,
        difficulty_level: data.difficultyLevel as "beginner" | "intermediate" | "advanced",
        target_audience: AUDIENCE_LABELS[data.targetAudience],
        learning_goals: data.learningGoals.join(", ") || undefined,
      });

      router.push(`/dashboard/processing/${response.generation_id}`);
    } catch (error) {
      console.error("Failed to generate from URL:", error);
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <motion.div
        className="mb-12"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-r from-pink-500 to-rose-600 flex items-center justify-center">
            <FiLink className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1
              className="text-3xl font-bold text-zinc-900 dark:text-white"
              style={{ fontFamily: "var(--font-playfair)" }}
            >
              Web URL
            </h1>
            <p className="text-zinc-500">
              Generate lessons from any web page
            </p>
          </div>
        </div>
      </motion.div>

      <StepForm type="url" onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  );
}
