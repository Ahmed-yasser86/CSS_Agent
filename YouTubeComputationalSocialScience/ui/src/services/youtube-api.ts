// YouTube Computational Social Science API Service
// Connects to the actual backend API at http://localhost:8000

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChannelAnalysis {
  channel_id: string;
  title: string;
  description: string;
  subscriber_count: number;
  video_count: number;
  view_count: number;
  videos: Video[];
  collection_run_id: string;
  status: string;
}

export interface Video {
  video_id: string;
  title: string;
  description: string;
  channel_id: string;
  channel_title: string;
  published_at: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  duration: number;
  tags: string[];
  thumbnail_url?: string;
  script?: string;
  chapters?: Array<{title: string; start_time: number; end_time: number}>;
}

export interface VideoAnalytics {
  video_id: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  engagement_rate: number;
  like_rate: number;
  comment_rate: number;
  comment_velocity: Record<string, number>;
  engagement_decay: Record<string, number>;
}

export interface ChannelAnalytics {
  channel_id: string;
  total_videos: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  subscriber_count: number;
  engagement_rate: number;
  upload_frequency: number;
  avg_views_per_video: number;
  avg_likes_per_video: number;
  avg_comments_per_video: number;
  top_videos_by_views: Video[];
  top_videos_by_likes: Video[];
  top_videos_by_comments: Video[];
}

export interface RecommendationNetwork {
  network_id: string;
  source_video_id: string;
  nodes: string[];
  edges: Array<{source: string; target: string; rank?: number}>;
  network_size: number;
  network_density?: number;
  average_degree?: number;
}

export interface CommentSample {
  comment_id: string;
  author: string;
  text: string;
  like_count: number;
  reply_count: number;
  published_at: string;
  sentiment?: number;
}

// API Response types
interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: "success" | "failed" | "not_found" | "no_data";
}

// Channel API
export async function analyzeChannel(
  channelUrl: string,
  videoLimit: number = 100,
  commentLimit: number = 1000,
  samplingStrategy: string = "stratified"
): Promise<ApiResponse<ChannelAnalysis>> {
  try {
    const params = new URLSearchParams({
      channel_url: channelUrl,
      video_limit: videoLimit.toString(),
      comment_limit: commentLimit.toString(),
      sampling_strategy: samplingStrategy,
    });

    const response = await fetch(`${API_BASE_URL}/channels/analyze?${params}`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      return { status: "failed", error: error.detail || "Analysis failed" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getChannelAnalytics(channelId: string): Promise<ApiResponse<ChannelAnalytics>> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelId}/analytics`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "Channel not found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function compareChannels(
  channelIds: string[],
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<any>> {
  try {
    const params = new URLSearchParams();
    channelIds.forEach(id => params.append("channel_ids", id));
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const response = await fetch(`${API_BASE_URL}/channels/compare?${params}`, {
      method: "POST",
    });

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getChannelUploadPattern(channelId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelId}/upload-pattern`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getChannelEngagementAnalysis(channelId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelId}/engagement-analysis`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getChannelPerformanceDistribution(channelId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelId}/performance-distribution`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

// Video API
export async function analyzeVideo(
  videoUrl: string,
  commentLimit: number = 1000,
  collectRecommendations: boolean = false
): Promise<ApiResponse<Video>> {
  try {
    const params = new URLSearchParams({
      video_url: videoUrl,
      comment_limit: commentLimit.toString(),
      collect_recommendations: collectRecommendations.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/videos/analyze?${params}`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      return { status: "failed", error: error.detail || "Analysis failed" };
    }

    const data = await response.json();
    // API returns {status, collection_run_id, video} - extract video to data
    return { status: data.status, data: data.video };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getVideoAnalytics(videoId: string): Promise<ApiResponse<VideoAnalytics>> {
  try {
    const response = await fetch(`${API_BASE_URL}/videos/${videoId}/analytics`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "Video not found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getVideoCommentSamples(
  videoId: string,
  sampleStrategy: string = "top_likes",
  sampleSize: number = 20
): Promise<ApiResponse<CommentSample[]>> {
  try {
    const params = new URLSearchParams({
      sample_strategy: sampleStrategy,
      sample_size: sampleSize.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/videos/${videoId}/comments/sample?${params}`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getVideoCommentAnalysis(videoId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/videos/${videoId}/comment-analysis`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getVideoCommentDistribution(videoId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/videos/${videoId}/comment-distribution`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getVideoCommentConcentration(videoId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/videos/${videoId}/comment-concentration`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getVideoEngagementTemporal(videoId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/videos/${videoId}/engagement/temporal`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "not_found", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function compareVideos(videoIds: string[]): Promise<ApiResponse<any>> {
  try {
    const params = new URLSearchParams();
    videoIds.forEach(id => params.append("video_ids", id));

    const response = await fetch(`${API_BASE_URL}/videos/compare?${params}`, {
      method: "POST",
    });

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

// Recommendation API
export async function analyzeVideoRecommendations(
  videoUrl: string,
  depth: number = 1
): Promise<ApiResponse<RecommendationNetwork>> {
  try {
    const params = new URLSearchParams({
      video_url: videoUrl,
      depth: depth.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/recommendations/analyze?${params}`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      return { status: "failed", error: error.detail || "Analysis failed" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getRecommendationNetwork(videoId: string): Promise<ApiResponse<RecommendationNetwork>> {
  try {
    const response = await fetch(`${API_BASE_URL}/recommendations/${videoId}/network`);
    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getRecommendationPatterns(videoId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/recommendations/${videoId}/patterns`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "no_data", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}

export async function getRecommendationTemporalAnalysis(videoId: string): Promise<ApiResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/recommendations/${videoId}/temporal`);
    
    if (!response.ok) {
      const error = await response.json();
      return { status: "no_data", error: error.detail || "No data found" };
    }

    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "failed", error: (error as Error).message };
  }
}
