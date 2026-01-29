"use client";

import { use, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { VideoPlayer } from "@/components/dashboard/video-player";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FiDownload,
  FiShare2,
  FiBook,
  FiClock,
  FiUsers,
  FiTarget,
  FiCheckCircle,
} from "react-icons/fi";
import { getGenerationDetails, type EducationalScript, type ContentResponse } from "@/lib/api";
import Link from "next/link";

interface LessonDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function LessonDetailPage({ params }: LessonDetailPageProps) {
  const resolvedParams = use(params);
  const searchParams = useSearchParams();
  const videoUrlFromQuery = searchParams.get("video");
  
  const [lesson, setLesson] = useState<ContentResponse | null>(null);
  const [resolvedVideoUrl, setResolvedVideoUrl] = useState<string | null>(videoUrlFromQuery);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLesson = async () => {
      try {
        const data = await getGenerationDetails(resolvedParams.id);
        setLesson(data);
        // Use video_url from API response if available, fallback to query param
        if (data.video_url) {
          setResolvedVideoUrl(data.video_url);
        }
      } catch (error) {
        console.error("Failed to fetch lesson:", error);
        // Set mock data for demo with proper ContentResponse structure
        setLesson({
          generation_id: resolvedParams.id,
          status: "completed",
          created_at: new Date().toISOString(),
          educational_script: {
            title: "Introduction to Quantum Physics",
            topic: "Quantum Mechanics",
            difficulty_level: "intermediate",
            target_audience: "High School Students",
            duration_minutes: 8,
            summary: "This lesson introduces the fundamental concepts of quantum physics, including wave-particle duality, the uncertainty principle, and quantum superposition.",
            key_takeaways: [
              "Quantum particles exhibit both wave and particle properties",
              "The uncertainty principle limits our knowledge of position and momentum",
              "Quantum superposition allows particles to exist in multiple states",
              "Observation affects quantum systems",
            ],
            learning_objectives: [
              {
                objective: "Understand wave-particle duality",
                bloom_level: "Understanding",
                success_criteria: ["Can explain the double-slit experiment", "Can describe photon behavior"],
              },
              {
                objective: "Apply the uncertainty principle",
                bloom_level: "Applying",
                success_criteria: ["Can calculate uncertainty limits", "Can explain measurement effects"],
              },
            ],
            sections: [
              {
                section_number: 1,
                title: "Introduction to Quantum World",
                content: "The quantum world operates by rules that seem bizarre compared to our everyday experience...",
                key_points: ["Quantum mechanics describes the very small", "Classical physics breaks down at atomic scales"],
                visual_suggestions: ["Atom animation", "Scale comparison"],
                duration_seconds: 120,
                narration_script: "Welcome to the fascinating world of quantum physics...",
              },
            ],
            assessments: [
              {
                title: "Quantum Basics Quiz",
                assessment_type: "multiple_choice",
                questions: [
                  {
                    question: "What is wave-particle duality?",
                    question_type: "multiple_choice",
                    options: ["A quantum phenomenon", "A classical concept", "A mathematical error", "None of the above"],
                    correct_answer: "A quantum phenomenon",
                    explanation: "Wave-particle duality is a fundamental concept in quantum mechanics...",
                    difficulty: "intermediate",
                  },
                ],
              },
            ],
          },
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchLesson();
  }, [resolvedParams.id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <motion.div
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
    );
  }

  // Get the script from either new or legacy field
  const script = lesson?.educational_script || lesson?.script;

  if (!script) {
    return (
      <div className="p-8 text-center">
        <h1 className="text-2xl font-bold mb-4">Lesson not found</h1>
        <Link href="/dashboard/lessons">
          <Button>Back to Lessons</Button>
        </Link>
      </div>
    );
  }

  // Extract data from either FDA or script
  const title = script.title || lesson?.fda?.title || "Untitled Lesson";
  const topic = script.topic || lesson?.fda?.topic || "General";
  const durationMinutes = script.duration_minutes || 
    (lesson?.fda?.total_duration_seconds ? Math.ceil(lesson.fda.total_duration_seconds / 60) : 10);
  const targetAudience = script.target_audience || lesson?.fda?.target_audience || "General";
  const difficultyLevel = script.difficulty_level || lesson?.fda?.difficulty_level || "intermediate";

  return (
    <div className="p-8">
      {/* Header */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-start justify-between">
          <div>
            <h1
              className="text-3xl font-bold text-zinc-900 dark:text-white mb-2"
              style={{ fontFamily: "var(--font-playfair)" }}
            >
              {title}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-500">
              <span className="flex items-center gap-1">
                <FiBook className="w-4 h-4" />
                {topic}
              </span>
              <span className="flex items-center gap-1">
                <FiClock className="w-4 h-4" />
                {durationMinutes} minutes
              </span>
              <span className="flex items-center gap-1">
                <FiUsers className="w-4 h-4" />
                {targetAudience}
              </span>
              <span className="badge badge-completed">
                {difficultyLevel}
              </span>
            </div>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="gap-2">
              <FiShare2 className="w-4 h-4" />
              Share
            </Button>
            <Button variant="outline" className="gap-2">
              <FiDownload className="w-4 h-4" />
              Download
            </Button>
          </div>
        </div>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Video Player */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <VideoPlayer
            src={resolvedVideoUrl || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"}
            title={title}
          />
        </motion.div>

        {/* Sidebar */}
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          {/* Learning Objectives */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <FiTarget className="w-5 h-5 text-blue-500" />
                Learning Objectives
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(script.learning_objectives || []).map((obj, index) => (
                <div
                  key={index}
                  className="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800"
                >
                  <p className="font-medium text-sm">{obj.objective}</p>
                  <span className="text-xs text-blue-500">{obj.bloom_level}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Key Takeaways */}
          {script.key_takeaways && script.key_takeaways.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <FiCheckCircle className="w-5 h-5 text-green-500" />
                Key Takeaways
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {script.key_takeaways.map((takeaway, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                    {takeaway}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
          )}
        </motion.div>
      </div>

      {/* Summary Section */}
      {script.summary && (
      <motion.div
        className="mt-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed">
              {script.summary}
            </p>
          </CardContent>
        </Card>
      </motion.div>
      )}

      {/* Content Sections */}
      {script.sections && script.sections.length > 0 && (
      <motion.div
        className="mt-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <h2
          className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white"
          style={{ fontFamily: "var(--font-playfair)" }}
        >
          Lesson Sections
        </h2>
        <div className="space-y-4">
          {script.sections.map((section, idx) => (
            <Card key={section.section_number || idx}>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                    {section.section_number || idx + 1}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-2">{section.title}</h3>
                    <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                      {section.content}
                    </p>
                    {section.key_points && section.key_points.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {section.key_points.map((point, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs"
                        >
                          {point}
                        </span>
                      ))}
                    </div>
                    )}
                  </div>
                  {section.duration_seconds && (
                  <div className="text-sm text-zinc-500 flex-shrink-0">
                    {Math.floor(section.duration_seconds / 60)}:{(section.duration_seconds % 60).toString().padStart(2, "0")}
                  </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </motion.div>
      )}
    </div>
  );
}
