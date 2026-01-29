"use client";

import { motion } from "framer-motion";
import {
  StatsCards,
  ActivityChart,
  TopicsChart,
  AudienceChart,
} from "@/components/dashboard/stats";
import { FiPlus } from "react-icons/fi";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h1
            className="text-3xl font-bold text-zinc-900 dark:text-white"
            style={{ fontFamily: "var(--font-playfair)" }}
          >
            Dashboard
          </h1>
          <p className="text-zinc-500 mt-1">
            Welcome back! Here&apos;s an overview of your lessons.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Link href="/dashboard/text">
            <Button className="gap-2">
              <FiPlus className="w-4 h-4" />
              Create New Lesson
            </Button>
          </Link>
        </motion.div>
      </div>

      {/* Stats Cards */}
      <div className="mb-8">
        <StatsCards />
      </div>

      {/* Charts Grid */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <ActivityChart />
        <TopicsChart />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <AudienceChart />
        </div>
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.7 }}
            className="h-full"
          >
            <div className="h-full rounded-3xl bg-gradient-to-br from-blue-600 to-indigo-700 p-8 text-white flex flex-col justify-between">
              <div>
                <h3 className="text-2xl font-bold mb-2" style={{ fontFamily: "var(--font-playfair)" }}>
                  Ready to create your next lesson?
                </h3>
                <p className="text-blue-100 max-w-md">
                  Transform any content into engaging video lessons in minutes. 
                  Choose from text input, file upload, or web URL.
                </p>
              </div>
              <div className="flex gap-3 mt-6">
                <Link href="/dashboard/text">
                  <Button variant="secondary" className="bg-white text-blue-600 hover:bg-blue-50">
                    Text Input
                  </Button>
                </Link>
                <Link href="/dashboard/upload">
                  <Button variant="outline" className="border-white/50 text-white hover:bg-white/10">
                    Upload File
                  </Button>
                </Link>
                <Link href="/dashboard/url">
                  <Button variant="outline" className="border-white/50 text-white hover:bg-white/10">
                    Web URL
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
