"use client";

import { motion } from "framer-motion";
import { LessonsList } from "@/components/dashboard/lessons-list";
import { FiList } from "react-icons/fi";

export default function LessonsPage() {
  return (
    <div className="p-8">
      {/* Header */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center">
            <FiList className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1
              className="text-3xl font-bold text-zinc-900 dark:text-white"
              style={{ fontFamily: "var(--font-playfair)" }}
            >
              Your Lessons
            </h1>
            <p className="text-zinc-500">
              View and manage all your created lessons
            </p>
          </div>
        </div>
      </motion.div>

      <LessonsList />
    </div>
  );
}
