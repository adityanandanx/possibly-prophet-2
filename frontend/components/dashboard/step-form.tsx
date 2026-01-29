"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import {
  FiArrowLeft,
  FiArrowRight,
  FiUpload,
  FiFile,
  FiX,
  FiPlus,
  FiTrash2,
} from "react-icons/fi";
import { DifficultyLevel, TargetAudience, DIFFICULTY_LABELS, AUDIENCE_LABELS } from "@/types";

interface StepFormProps {
  type: "text" | "file" | "url";
  onSubmit: (data: FormData) => void;
  isLoading?: boolean;
}

interface FormData {
  content?: string;
  file?: File;
  url?: string;
  topic: string;
  difficultyLevel: DifficultyLevel;
  targetAudience: TargetAudience;
  learningGoals: string[];
}

export function StepForm({ type, onSubmit, isLoading }: StepFormProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<FormData>({
    content: "",
    file: undefined,
    url: "",
    topic: "",
    difficultyLevel: "intermediate",
    targetAudience: "high_school",
    learningGoals: [],
  });
  const [newGoal, setNewGoal] = useState("");

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFormData((prev) => ({ ...prev, file: acceptedFiles[0] }));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleAddGoal = () => {
    if (newGoal.trim()) {
      setFormData((prev) => ({
        ...prev,
        learningGoals: [...prev.learningGoals, newGoal.trim()],
      }));
      setNewGoal("");
    }
  };

  const handleRemoveGoal = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      learningGoals: prev.learningGoals.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const canProceed = () => {
    if (step === 1) {
      switch (type) {
        case "text":
          return (formData.content?.trim().length ?? 0) > 50;
        case "file":
          return !!formData.file;
        case "url":
          return formData.url?.startsWith("http");
        default:
          return false;
      }
    }
    return true;
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Step Indicator */}
      <div className="flex items-center justify-center mb-12">
        <div className="flex items-center gap-4">
          <motion.div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
              step >= 1
                ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white"
                : "bg-zinc-200 text-zinc-500"
            }`}
            animate={{ scale: step === 1 ? 1.1 : 1 }}
          >
            1
          </motion.div>
          <div
            className={`w-24 h-1 rounded-full transition-colors ${
              step >= 2 ? "bg-gradient-to-r from-blue-500 to-indigo-600" : "bg-zinc-200"
            }`}
          />
          <motion.div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
              step >= 2
                ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white"
                : "bg-zinc-200 text-zinc-500"
            }`}
            animate={{ scale: step === 2 ? 1.1 : 1 }}
          >
            2
          </motion.div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardContent className="p-8">
                {type === "text" && (
                  <div className="space-y-4">
                    <Label className="text-lg font-semibold">Enter your content</Label>
                    <p className="text-sm text-zinc-500 mb-4">
                      Paste or type the educational content you want to transform into a video lesson.
                    </p>
                    <Textarea
                      placeholder="Enter your educational content here... (minimum 50 characters)"
                      className="min-h-[300px] text-base"
                      value={formData.content}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, content: e.target.value }))
                      }
                    />
                    <p className="text-sm text-zinc-400">
                      {formData.content?.length || 0} characters
                    </p>
                  </div>
                )}

                {type === "file" && (
                  <div className="space-y-4">
                    <Label className="text-lg font-semibold">Upload your file</Label>
                    <p className="text-sm text-zinc-500 mb-4">
                      Upload a PDF, DOC, DOCX, or TXT file (max 10MB)
                    </p>
                    
                    {!formData.file ? (
                      <div
                        {...getRootProps()}
                        className={`drop-zone ${isDragActive ? "dragover" : ""}`}
                      >
                        <input {...getInputProps()} />
                        <motion.div
                          className="flex flex-col items-center gap-4"
                          animate={{ y: isDragActive ? -5 : 0 }}
                        >
                          <div className="w-16 h-16 rounded-2xl bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center">
                            <FiUpload className="w-8 h-8 text-white" />
                          </div>
                          <div className="text-center">
                            <p className="font-medium text-zinc-700 dark:text-zinc-300">
                              {isDragActive
                                ? "Drop your file here"
                                : "Drag & drop your file here"}
                            </p>
                            <p className="text-sm text-zinc-500 mt-1">
                              or click to browse
                            </p>
                          </div>
                        </motion.div>
                      </div>
                    ) : (
                      <motion.div
                        className="flex items-center justify-between p-4 rounded-2xl bg-zinc-100 dark:bg-zinc-800"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center">
                            <FiFile className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <p className="font-medium text-zinc-700 dark:text-zinc-300">
                              {formData.file.name}
                            </p>
                            <p className="text-sm text-zinc-500">
                              {(formData.file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            setFormData((prev) => ({ ...prev, file: undefined }))
                          }
                        >
                          <FiX className="w-5 h-5" />
                        </Button>
                      </motion.div>
                    )}
                  </div>
                )}

                {type === "url" && (
                  <div className="space-y-4">
                    <Label className="text-lg font-semibold">Enter web URL</Label>
                    <p className="text-sm text-zinc-500 mb-4">
                      Provide a URL to a webpage containing educational content.
                    </p>
                    <Input
                      type="url"
                      placeholder="https://example.com/article"
                      value={formData.url}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, url: e.target.value }))
                      }
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardContent className="p-8 space-y-6">
                <div className="space-y-3">
                  <Label className="text-lg font-semibold">Topic (Optional)</Label>
                  <Input
                    placeholder="e.g., Introduction to Quantum Physics"
                    value={formData.topic}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, topic: e.target.value }))
                    }
                  />
                </div>

                <div className="space-y-3">
                  <Label className="text-lg font-semibold">Difficulty Level</Label>
                  <Select
                    value={formData.difficultyLevel}
                    onValueChange={(value: DifficultyLevel) =>
                      setFormData((prev) => ({ ...prev, difficultyLevel: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select difficulty" />
                    </SelectTrigger>
                    <SelectContent>
                      {(Object.entries(DIFFICULTY_LABELS) as [DifficultyLevel, string][]).map(
                        ([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        )
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label className="text-lg font-semibold">Target Audience</Label>
                  <Select
                    value={formData.targetAudience}
                    onValueChange={(value: TargetAudience) =>
                      setFormData((prev) => ({ ...prev, targetAudience: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select audience" />
                    </SelectTrigger>
                    <SelectContent>
                      {(Object.entries(AUDIENCE_LABELS) as [TargetAudience, string][]).map(
                        ([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        )
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label className="text-lg font-semibold">Learning Goals (Optional)</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a learning goal..."
                      value={newGoal}
                      onChange={(e) => setNewGoal(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddGoal();
                        }
                      }}
                    />
                    <Button type="button" onClick={handleAddGoal} size="icon">
                      <FiPlus className="w-5 h-5" />
                    </Button>
                  </div>
                  <AnimatePresence>
                    {formData.learningGoals.length > 0 && (
                      <motion.div
                        className="space-y-2 mt-4"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                      >
                        {formData.learningGoals.map((goal, index) => (
                          <motion.div
                            key={index}
                            className="flex items-center justify-between p-3 rounded-xl bg-zinc-100 dark:bg-zinc-800"
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                          >
                            <span className="text-sm">{goal}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleRemoveGoal(index)}
                              className="h-8 w-8"
                            >
                              <FiTrash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </motion.div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation buttons */}
      <div className="flex justify-between mt-8">
        <Button
          variant="outline"
          onClick={() => setStep((prev) => prev - 1)}
          disabled={step === 1}
          className="gap-2"
        >
          <FiArrowLeft /> Back
        </Button>
        
        {step === 1 ? (
          <Button
            onClick={() => setStep(2)}
            disabled={!canProceed()}
            className="gap-2"
          >
            Next <FiArrowRight />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={isLoading}
            className="gap-2 min-w-[150px]"
          >
            {isLoading ? (
              <motion.div
                className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
            ) : (
              "Generate Lesson"
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
