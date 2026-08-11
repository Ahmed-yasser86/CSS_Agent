"use client";

import { useQuery } from "@tanstack/react-query";
import { request, toQuery } from "@/services/api";
import type {
  ChannelProjection,
  EdgeRow,
  NetworkExportFormat,
  NetworkMetrics,
  Paginated,
  TemporalResult,
} from "@/lib/network-full-types";

export const networkFullKeys = {
  metrics: (runId?: string, topN = 10) =>
    ["network", "full", "metrics", runId ?? "all", topN] as const,
  temporal: (runs: string[]) =>
    ["network", "full", "temporal", runs.join(",")] as const,
  edges: (runId?: string, cursor?: string) =>
    ["network", "full", "edges", runId ?? "all", cursor ?? "start"] as const,
  channels: (runId?: string) =>
    ["network", "full", "channels", runId ?? "all"] as const,
};

export function getNetworkMetrics(
  runId?: string,
  topN = 10,
): Promise<NetworkMetrics> {
  return request(
    `/network/metrics${toQuery({ run_id: runId, top_n: topN })}`,
  );
}

export function getNetworkTemporal(runs: string[]): Promise<TemporalResult> {
  return request(
    `/network/temporal${toQuery({ runs: runs.join(",") })}`,
  );
}

export function getNetworkEdges(
  runId?: string,
  cursor?: string,
): Promise<Paginated<EdgeRow>> {
  return request(
    `/network/edges${toQuery({ run_id: runId, cursor })}`,
  );
}

export function getChannelProjection(
  runId?: string,
): Promise<ChannelProjection> {
  return request(
    `/network/channels${toQuery({ run_id: runId })}`,
  );
}

export function getNetworkExportUrl(
  format: NetworkExportFormat,
  runId?: string,
): string {
  const base =
    process.env.NEXT_PUBLIC_API_URL ?? "/api/v1/social-science";
  return `${base}/network/export${toQuery({ format, run_id: runId })}`;
}

export function useNetworkMetrics(runId?: string, topN = 10) {
  return useQuery({
    queryKey: networkFullKeys.metrics(runId, topN),
    queryFn: () => getNetworkMetrics(runId, topN),
  });
}

export function useNetworkTemporal(runs: string[]) {
  return useQuery({
    queryKey: networkFullKeys.temporal(runs),
    queryFn: () => getNetworkTemporal(runs),
    enabled: runs.length > 0,
  });
}

export function useNetworkEdges(runId?: string, cursor?: string) {
  return useQuery({
    queryKey: networkFullKeys.edges(runId, cursor),
    queryFn: () => getNetworkEdges(runId, cursor),
    placeholderData: (previous) => previous,
    staleTime: 30_000,
  });
}

export function useChannelProjection(runId?: string) {
  return useQuery({
    queryKey: networkFullKeys.channels(runId),
    queryFn: () => getChannelProjection(runId),
  });
}
