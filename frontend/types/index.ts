export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';
export type TargetAudience = 'primary_school' | 'high_school' | 'university';
export type InputType = 'text' | 'file' | 'url';

export interface LessonFormData {
  content?: string;
  file?: File;
  url?: string;
  topic?: string;
  difficultyLevel: DifficultyLevel;
  targetAudience: TargetAudience;
  learningGoals: string[];
}

export interface Lesson {
  id: string;
  title: string;
  topic: string;
  difficultyLevel: DifficultyLevel;
  targetAudience: string;
  createdAt: string;
  completedAt?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  videoUrl?: string;
  videoPath?: string;
  thumbnailUrl?: string;
  manimCode?: string;
  fdaSlideCount?: number;
  estimatedDuration?: number;
}

export interface DashboardStats {
  totalLessons: number;
  lessonsThisMonth: number;
  topTopics: { topic: string; count: number }[];
  recentActivity: { date: string; count: number }[];
}

export const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
};

export const AUDIENCE_LABELS: Record<TargetAudience, string> = {
  primary_school: 'Primary School',
  high_school: 'High School',
  university: 'University',
};
