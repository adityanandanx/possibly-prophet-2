"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FiSearch,
  FiPlay,
  FiCalendar,
  FiClock,
  FiUsers,
  FiBook,
} from "react-icons/fi";
import { listRecentGenerations } from "@/lib/api";

interface LessonItem {
  generation_id: string;
  title: string;
  topic: string;
  status: string;
  created_at: string;
  difficulty_level?: string;
  target_audience?: string;
  duration_minutes?: number;
  video_url?: string;
}

export function LessonsList() {
  const [lessons, setLessons] = useState<LessonItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLessons = async () => {
      try {
        const data = await listRecentGenerations(20);
        setLessons(data.generations || []);
      } catch (error) {
        console.error("Failed to fetch lessons:", error);
        // Set mock data for demo
        setLessons([
          {
            generation_id: "demo-1",
            title: "Introduction to Quantum Physics",
            topic: "Physics",
            status: "completed",
            created_at: "2026-01-28T10:30:00Z",
            difficulty_level: "intermediate",
            target_audience: "High School",
            duration_minutes: 8,
          },
          {
            generation_id: "demo-2",
            title: "Basics of Machine Learning",
            topic: "Computer Science",
            status: "completed",
            created_at: "2026-01-27T14:15:00Z",
            difficulty_level: "advanced",
            target_audience: "University",
            duration_minutes: 12,
          },
          {
            generation_id: "demo-3",
            title: "Understanding Photosynthesis",
            topic: "Biology",
            status: "completed",
            created_at: "2026-01-26T09:00:00Z",
            difficulty_level: "beginner",
            target_audience: "Primary School",
            duration_minutes: 5,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLessons();
  }, []);

  const filteredLessons = lessons.filter(
    (lesson) =>
      lesson.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lesson.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      pending: "badge badge-pending",
      processing: "badge badge-processing",
      completed: "badge badge-completed",
      failed: "badge badge-failed",
    };
    return badges[status] || "badge";
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <motion.div
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search bar */}
      <div className="relative">
        <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400" />
        <Input
          placeholder="Search lessons..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-12"
        />
      </div>

      {/* Lessons grid */}
      {filteredLessons.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
              <FiBook className="w-8 h-8 text-zinc-400" />
            </div>
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">
              No lessons found
            </h3>
            <p className="text-zinc-500 mb-6">
              {searchQuery
                ? "Try a different search term"
                : "Create your first lesson to get started"}
            </p>
            <Link href="/dashboard/text">
              <Button>Create New Lesson</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredLessons.map((lesson, index) => (
            <motion.div
              key={lesson.generation_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Link href={`/dashboard/lessons/${lesson.generation_id}`}>
                <Card className="hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
                            {lesson.title}
                          </h3>
                          <span className={getStatusBadge(lesson.status)}>
                            {lesson.status}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-500">
                          <span className="flex items-center gap-1">
                            <FiBook className="w-4 h-4" />
                            {lesson.topic}
                          </span>
                          <span className="flex items-center gap-1">
                            <FiCalendar className="w-4 h-4" />
                            {formatDate(lesson.created_at)}
                          </span>
                          {lesson.duration_minutes && (
                            <span className="flex items-center gap-1">
                              <FiClock className="w-4 h-4" />
                              {lesson.duration_minutes} min
                            </span>
                          )}
                          {lesson.target_audience && (
                            <span className="flex items-center gap-1">
                              <FiUsers className="w-4 h-4" />
                              {lesson.target_audience}
                            </span>
                          )}
                        </div>
                      </div>
                      {lesson.status === "completed" && (
                        <motion.div
                          className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center"
                          whileHover={{ scale: 1.1 }}
                        >
                          <FiPlay className="w-5 h-5 text-white ml-0.5" />
                        </motion.div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
