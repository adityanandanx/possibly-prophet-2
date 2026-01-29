"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FiBook, FiTrendingUp, FiUsers, FiClock } from "react-icons/fi";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const activityData = [
  { name: "Mon", lessons: 4 },
  { name: "Tue", lessons: 3 },
  { name: "Wed", lessons: 6 },
  { name: "Thu", lessons: 8 },
  { name: "Fri", lessons: 5 },
  { name: "Sat", lessons: 2 },
  { name: "Sun", lessons: 1 },
];

const topicsData = [
  { name: "Mathematics", count: 15 },
  { name: "Physics", count: 12 },
  { name: "Chemistry", count: 8 },
  { name: "Biology", count: 10 },
  { name: "History", count: 5 },
];

const audienceData = [
  { name: "Primary School", value: 20, color: "#3b82f6" },
  { name: "High School", value: 45, color: "#6366f1" },
  { name: "University", value: 35, color: "#8b5cf6" },
];

const stats = [
  {
    title: "Total Lessons",
    value: "47",
    change: "+12%",
    icon: FiBook,
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    title: "This Month",
    value: "12",
    change: "+8%",
    icon: FiTrendingUp,
    gradient: "from-indigo-500 to-purple-500",
  },
  {
    title: "Students Reached",
    value: "1,234",
    change: "+25%",
    icon: FiUsers,
    gradient: "from-pink-500 to-rose-500",
  },
  {
    title: "Avg. Duration",
    value: "8m",
    change: "-2%",
    icon: FiClock,
    gradient: "from-orange-500 to-amber-500",
  },
];

export function StatsCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 mb-1">{stat.title}</p>
                  <h3 className="text-3xl font-bold text-zinc-900 dark:text-white">
                    {stat.value}
                  </h3>
                  <span
                    className={`text-xs font-medium ${
                      stat.change.startsWith("+") ? "text-green-500" : "text-red-500"
                    }`}
                  >
                    {stat.change} from last month
                  </span>
                </div>
                <div
                  className={`w-14 h-14 rounded-2xl bg-gradient-to-r ${stat.gradient} flex items-center justify-center`}
                >
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}

export function ActivityChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.4 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Weekly Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activityData}>
                <defs>
                  <linearGradient id="colorLessons" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="lessons"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#colorLessons)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function TopicsChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.5 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Top Topics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicsData} layout="vertical">
                <defs>
                  <linearGradient id="colorBar" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#6366f1" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" stroke="#9ca3af" />
                <YAxis dataKey="name" type="category" stroke="#9ca3af" width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                  }}
                />
                <Bar dataKey="count" fill="url(#colorBar)" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function AudienceChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.6 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Audience Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={audienceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {audienceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 mt-4">
            {audienceData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                  {item.name}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
