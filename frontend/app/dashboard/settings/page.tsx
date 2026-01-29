"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FiSettings, FiUser, FiBell, FiShield, FiSave } from "react-icons/fi";

export default function SettingsPage() {
  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-r from-zinc-500 to-zinc-700 flex items-center justify-center">
            <FiSettings className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1
              className="text-3xl font-bold text-zinc-900 dark:text-white"
              style={{ fontFamily: "var(--font-playfair)" }}
            >
              Settings
            </h1>
            <p className="text-zinc-500">
              Manage your account and preferences
            </p>
          </div>
        </div>
      </motion.div>

      <div className="space-y-6">
        {/* Profile Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiUser className="w-5 h-5" />
                Profile Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input placeholder="John Doe" />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" placeholder="john@example.com" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Institution</Label>
                <Input placeholder="Your school or organization" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Preferences */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiBell className="w-5 h-5" />
                Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Default Difficulty Level</Label>
                  <Select defaultValue="intermediate">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Default Target Audience</Label>
                  <Select defaultValue="high_school">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="primary_school">Primary School</SelectItem>
                      <SelectItem value="high_school">High School</SelectItem>
                      <SelectItem value="university">University</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Video Quality</Label>
                <Select defaultValue="medium_quality">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low_quality">Low (480p)</SelectItem>
                    <SelectItem value="medium_quality">Medium (720p)</SelectItem>
                    <SelectItem value="high_quality">High (1080p)</SelectItem>
                    <SelectItem value="production_quality">Production (4K)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* API Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiShield className="w-5 h-5" />
                API Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Backend API URL</Label>
                <Input 
                  placeholder="http://localhost:8000" 
                  defaultValue={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                />
              </div>
              <p className="text-sm text-zinc-500">
                Configure the backend API URL for content generation. 
                Leave empty to use the default local development server.
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Save Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex justify-end"
        >
          <Button className="gap-2">
            <FiSave className="w-4 h-4" />
            Save Changes
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
