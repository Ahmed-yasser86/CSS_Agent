"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type {
  CollectionSpec,
  ResearchEntity,
  ResearchQuery,
  RunType,
  SamplingSpec,
  VideoFilter,
} from "@/lib/types";
import * as api from "@/services/api";

export const queryKeys = {
  runs: (runType?: RunType) => ["runs", runType ?? "all"] as const,
  run: (runId: string) => ["runs", runId] as const,
  runErrors: (runId: string) => ["runs", runId, "errors"] as const,
  channelOverview: (channelId: string) => ["channels", channelId, "overview"] as const,
  channelVideos: (channelId: string, filter?: VideoFilter) =>
    ["channels", channelId, "videos", JSON.stringify(filter ?? {})] as const,
  channelVideoCount: (channelId: string) =>
    ["channels", channelId, "videos", "count"] as const,
  video: (videoId: string) => ["videos", videoId] as const,
  videoEngagement: (videoId: string) => ["videos", videoId, "engagement"] as const,
  commentPercentiles: (videoId: string) =>
    ["videos", videoId, "comments", "percentiles"] as const,
  commentVelocity: (videoId: string, bucket: "day" | "hour") =>
    ["videos", videoId, "comments", "velocity", bucket] as const,
  videoComments: (videoId: string) => ["videos", videoId, "comments"] as const,
  videoRecommendations: (videoId: string) =>
    ["videos", videoId, "recommendations"] as const,
  networkSummary: (runId?: string, topN = 10) =>
    ["network", "summary", runId ?? "all", topN] as const,
  networkVideoContext: (videoId: string, runId?: string) =>
    ["network", "videos", videoId, runId ?? "all"] as const,
  jobs: () => ["jobs"] as const,
  job: (jobId: string) => ["jobs", jobId] as const,
  coverage: () => ["coverage"] as const,
  datasetSummary: () => ["dataset", "summary"] as const,
  researchVariables: (entity?: ResearchEntity) =>
    ["research", "variables", entity ?? "all"] as const,
  researchOperators: () => ["research", "operators"] as const,
  search: (q: string, entity?: string) =>
    ["search", q, entity ?? "all"] as const,
};

export function useRuns(runType?: RunType) {
  return useQuery({
    queryKey: queryKeys.runs(runType),
    queryFn: () => api.getRuns(runType),
  });
}

export function useRun(runId: string) {
  return useQuery({
    queryKey: queryKeys.run(runId),
    queryFn: () => api.getRun(runId),
    enabled: !!runId,
  });
}

export function useRunErrors(runId: string) {
  return useQuery({
    queryKey: queryKeys.runErrors(runId),
    queryFn: () => api.getRunErrors(runId),
    enabled: !!runId,
  });
}

export function useChannelOverview(channelId: string) {
  return useQuery({
    queryKey: queryKeys.channelOverview(channelId),
    queryFn: () => api.getChannelOverview(channelId),
    enabled: !!channelId,
  });
}

export function useChannelVideos(channelId: string, filter?: VideoFilter) {
  return useQuery({
    queryKey: queryKeys.channelVideos(channelId, filter),
    queryFn: () => api.getChannelVideos(channelId, filter),
    enabled: !!channelId,
  });
}

export function useChannelVideoCount(channelId: string) {
  return useQuery({
    queryKey: queryKeys.channelVideoCount(channelId),
    queryFn: () => api.getChannelVideoCount(channelId),
    enabled: !!channelId,
  });
}

export function useVideo(videoId: string) {
  return useQuery({
    queryKey: queryKeys.video(videoId),
    queryFn: () => api.getVideo(videoId),
    enabled: !!videoId,
  });
}

export function useVideoEngagement(videoId: string) {
  return useQuery({
    queryKey: queryKeys.videoEngagement(videoId),
    queryFn: () => api.getVideoEngagement(videoId),
    enabled: !!videoId,
  });
}

export function useCommentPercentiles(videoId: string) {
  return useQuery({
    queryKey: queryKeys.commentPercentiles(videoId),
    queryFn: () => api.getCommentPercentiles(videoId),
    enabled: !!videoId,
  });
}

export function useCommentVelocity(videoId: string, bucket: "day" | "hour") {
  return useQuery({
    queryKey: queryKeys.commentVelocity(videoId, bucket),
    queryFn: () => api.getCommentVelocity(videoId, bucket),
    enabled: !!videoId,
  });
}

export function useVideoComments(videoId: string) {
  return useQuery({
    queryKey: queryKeys.videoComments(videoId),
    queryFn: () => api.getVideoComments(videoId),
    enabled: !!videoId,
  });
}

export function useVideoRecommendations(videoId: string) {
  return useQuery({
    queryKey: queryKeys.videoRecommendations(videoId),
    queryFn: () => api.getVideoRecommendations(videoId),
    enabled: !!videoId,
  });
}

export function useNetworkSummary(runId?: string, topN = 10) {
  return useQuery({
    queryKey: queryKeys.networkSummary(runId, topN),
    queryFn: () => api.getNetworkSummary(runId, topN),
  });
}

export function useNetworkVideoContext(videoId: string, runId?: string) {
  return useQuery({
    queryKey: queryKeys.networkVideoContext(videoId, runId),
    queryFn: () => api.getNetworkVideoContext(videoId, runId),
    enabled: !!videoId,
  });
}

export type CollectKind = "channel" | "video" | "recommendations";

export function useCollect() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ kind, url }: { kind: CollectKind; url: string }) => {
      if (kind === "channel") return api.collectChannel(url);
      if (kind === "video") return api.collectVideo(url);
      return api.collectRecommendations(url);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
    },
  });
}

export function useSubmitCollect() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (spec: CollectionSpec) => api.submitCollect(spec),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs() });
    },
  });
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: queryKeys.job(jobId ?? ""),
    queryFn: () => api.getJob(jobId as string),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "pending" || status === "running") return 1500;
      return false;
    },
  });
}

export function useJobs() {
  return useQuery({
    queryKey: queryKeys.jobs(),
    queryFn: () => api.getJobs(),
    refetchInterval: 5000,
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => api.cancelJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.jobs() });
    },
  });
}

export function useCoverage() {
  return useQuery({
    queryKey: queryKeys.coverage(),
    queryFn: () => api.getCoverage(),
    refetchInterval: 15000,
  });
}

export function useDatasetSummary() {
  return useQuery({
    queryKey: queryKeys.datasetSummary(),
    queryFn: () => api.getDatasetSummary(),
  });
}

export function useSampleVideos(channelId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (spec: SamplingSpec) => api.sampleVideos(channelId, spec),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.channelVideos(channelId),
      });
    },
  });
}

export function useSampleComments(videoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (spec: SamplingSpec) => api.sampleComments(videoId, spec),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.videoComments(videoId),
      });
    },
  });
}

export function useResearchVariables(entity?: ResearchEntity) {
  return useQuery({
    queryKey: queryKeys.researchVariables(entity),
    queryFn: () => api.getResearchVariables(entity),
  });
}

export function useResearchOperators() {
  return useQuery({
    queryKey: ["research", "operators"] as const,
    queryFn: () => api.getResearchOperators(),
  });
}

export function usePreviewResearchQuery() {
  return useMutation({
    mutationFn: (query: ResearchQuery) => api.previewResearchQuery(query),
  });
}

export function useResolveResearchQuery() {
  return useMutation({
    mutationFn: (query: ResearchQuery) => api.resolveResearchQuery(query),
  });
}

export function useGlobalSearch(q: string, entity?: string) {
  return useQuery({
    queryKey: queryKeys.search(q, entity),
    queryFn: () => api.searchGlobal(q, entity),
    enabled: q.trim().length > 0,
    placeholderData: keepPreviousData,
  });
}
