import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health endpoints
export const healthCheck = () => api.get('/api/v1/health/');
export const detailedHealthCheck = () => api.get('/api/v1/health/detailed');

// Content generation endpoints
export interface TextPromptRequest {
  content: string;
  topic?: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  target_audience?: string;
  learning_goals?: string;
}

export interface UrlRequest {
  url: string;
  topic?: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  target_audience?: string;
  learning_goals?: string;
}

export interface ContentResponse {
  generation_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  educational_script?: EducationalScript;
  manim_code?: string;
  html_content?: string;
  // New pipeline fields
  video_url?: string;
  video_path?: string;
  fda?: FDASpecification;
  pipeline_metadata?: PipelineMetadata;
  // Timestamps and errors
  created_at: string;
  completed_at?: string;
  error_message?: string;
  generation_metadata?: GenerationMetadata;
  // Legacy field aliases
  script?: EducationalScript; // Alias for educational_script
  metadata?: GenerationMetadata; // Alias for generation_metadata
}

export interface EducationalScript {
  title: string;
  topic: string;
  difficulty_level: string;
  target_audience: string;
  duration_minutes: number;
  learning_objectives: LearningObjective[];
  sections: ContentSection[];
  summary: string;
  key_takeaways: string[];
  assessments: Assessment[];
}

export interface LearningObjective {
  objective: string;
  bloom_level: string;
  success_criteria: string[];
}

export interface ContentSection {
  section_number: number;
  title: string;
  content: string;
  key_points: string[];
  visual_suggestions: string[];
  duration_seconds: number;
  narration_script: string;
  transition_note?: string;
}

export interface Assessment {
  title: string;
  assessment_type: string;
  questions: AssessmentQuestion[];
}

export interface AssessmentQuestion {
  question: string;
  question_type: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  difficulty: string;
}

export interface GenerationMetadata {
  generation_id?: string;
  status?: string;
  created_at?: string;
  completed_at?: string;
  processing_time_seconds?: number;
  input_type?: string;
  model_used?: string;
  agent_versions?: Record<string, string>;
  input_tokens?: number;
  output_tokens?: number;
  quality_score?: number;
}

// New types for the 3-agent pipeline
export interface FDASpecification {
  title: string;
  topic: string;
  total_duration_seconds: number;
  difficulty_level: string;
  target_audience: string;
  slides: FDASlide[];
  global_settings: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface FDASlide {
  slide_id: string;
  slide_number: number;
  title: string;
  slide_type: string;
  content: Record<string, unknown>;
  animation_rules: FDAAnimationRule[];
  duration_seconds: number;
  transition_in: string;
  transition_out: string;
}

export interface FDAAnimationRule {
  rule_id: string;
  intent: string;
  visual_elements: Record<string, unknown>[];
  animations: Record<string, unknown>[];
  timing: Record<string, unknown>;
  narration: string;
  notes?: string;
}

export interface PipelineMetadata {
  execution_id: string;
  input_type: 'text' | 'file' | 'url';
  start_time: string;
  end_time?: string;
  topic?: string;
  difficulty_level?: string;
  total_slides?: number;
  estimated_duration?: number;
  pipeline_version?: string;
  agents_used?: string[];
}

export interface ManimResponse {
  generation_id: string;
  manim_code: string;
  validation_passed: boolean;
  validation_errors?: string[];
}

export interface VideoRenderResponse {
  generation_id: string;
  video_url: string;
  s3_url?: string;
  local_url?: string;
  render_time_seconds: number;
  quality: string;
  frame_rate: number;
}

export interface GenerationStatusResponse {
  generation_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  current_step?: string;
  progress_percentage?: number;
  error_message?: string;
}

// Content generation functions
export const generateFromText = async (data: TextPromptRequest): Promise<ContentResponse> => {
  const formData = new FormData();
  formData.append('content', data.content);
  if (data.topic) formData.append('topic', data.topic);
  if (data.difficulty_level) formData.append('difficulty_level', data.difficulty_level);
  if (data.target_audience) formData.append('target_audience', data.target_audience);
  if (data.learning_goals) formData.append('learning_goals', data.learning_goals);
  
  const response = await api.post('/api/v1/content/text', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const generateFromUrl = async (data: UrlRequest): Promise<ContentResponse> => {
  const formData = new FormData();
  formData.append('url', data.url);
  if (data.topic) formData.append('topic', data.topic);
  if (data.difficulty_level) formData.append('difficulty_level', data.difficulty_level);
  if (data.target_audience) formData.append('target_audience', data.target_audience);
  if (data.learning_goals) formData.append('learning_goals', data.learning_goals);
  
  const response = await api.post('/api/v1/content/url', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const uploadAndGenerate = async (
  file: File,
  options?: {
    topic?: string;
    difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
    target_audience?: string;
    learning_goals?: string;
  }
): Promise<ContentResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.topic) formData.append('topic', options.topic);
  if (options?.difficulty_level) formData.append('difficulty_level', options.difficulty_level);
  if (options?.target_audience) formData.append('target_audience', options.target_audience);
  if (options?.learning_goals) formData.append('learning_goals', options.learning_goals);
  
  const response = await api.post('/api/v1/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getGenerationStatus = async (generationId: string): Promise<GenerationStatusResponse> => {
  const response = await api.get(`/api/v1/content/status/${generationId}`);
  return response.data;
};

export const getGenerationDetails = async (generationId: string): Promise<ContentResponse> => {
  const response = await api.get(`/api/v1/content/generation/${generationId}`);
  return response.data;
};

export const listRecentGenerations = async (limit?: number) => {
  const response = await api.get('/api/v1/content/generations/recent', {
    params: { limit },
  });
  return response.data;
};

// Manim and video generation
export const generateManimCode = async (generationId: string): Promise<ManimResponse> => {
  const response = await api.post(`/api/v1/content/generate/manim/${generationId}`);
  return response.data;
};

export const renderVideo = async (
  generationId: string,
  quality: 'low_quality' | 'medium_quality' | 'high_quality' | 'production_quality' = 'medium_quality',
  frameRate: number = 30
): Promise<VideoRenderResponse> => {
  const response = await api.post(`/api/v1/content/render/video/${generationId}`, null, {
    params: { quality, frame_rate: frameRate },
  });
  return response.data;
};

// Validation endpoints
export const validateTextContent = async (content: string, contentType?: string) => {
  const formData = new FormData();
  formData.append('content', content);
  if (contentType) formData.append('content_type', contentType);
  
  const response = await api.post('/api/v1/content/validate/text', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const validateUrlContent = async (url: string) => {
  const formData = new FormData();
  formData.append('url', url);
  
  const response = await api.post('/api/v1/content/validate/url', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
