"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingState } from "@/components/features/state";
import { useRuns } from "@/services/queries";
import {
  NetworkMetricTiles,
  DegreeDistributionPanel,
  RankingPanel,
} from "@/components/features/network-full/network-metrics-tiles";
import { TemporalOverlay } from "@/components/features/network-full/temporal-overlay";
import { EdgeTable } from "@/components/features/network-full/edge-table";
import { useNetworkMetrics, getNetworkExportUrl, useNetworkGraph, useScrapeNetwork } from "@/services/networkFull";
import { EXPORT_FORMATS } from "@/lib/network-full-types";
import { NetworkGraph, type GraphLink, type GraphNode } from "@/components/features/network-graph";
import { LayerPanel } from "@/components/features/network-layer/layer-panel";
import { CommenterOverlapView } from "@/components/features/commenters/commenter-overlap-view";
import { ExpansionPanel } from "@/components/features/network-expansion/expansion-panel";
import { ScrapeFiltersDialog } from "@/components/features/network-expansion/scrape-filters-dialog";
import { useExpansionJob, scrapeExpansionAll, scrapeExpansionVideo } from "@/services/networkExpansion";
import type { ScrapeFilters as ExpansionFilters } from "@/lib/network-expansion-types";
import type { ChannelGraphPayload, GraphProjection, NetworkGraphPayload } from "@/lib/network-full-types";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles } from "lucide-react";
import { Toast } from "@/components/features/state";
import { JobProgressCard } from "@/components/features/job-progress-card";

function mapGraphPayload(payload: {
  nodes: {
    video_id: string;
    title?: string | null;
    channel_id?: string | null;
    channel_name?: string | null;
    thumbnail_url?: string | null;
    views?: number | null;
    likes?: number | null;
    duration?: number | null;
    kind: GraphNode["kind"];
    in_degree: number;
    out_degree: number;
    run_ids?: string[];
    run_types?: string[];
    community_id?: number | null;
  }[];
  edges: {
    source: string;
    target: string;
    position?: number | null;
    run_id?: string | null;
    run_type?: string | null;
    run_name?: string | null;
    title?: string | null;
  }[];
}) {
  return {
    nodes: payload.nodes.map((n): GraphNode => ({
      id: n.video_id,
      title: n.title,
      channel: n.channel_name ?? n.channel_id,
      channel_id: n.channel_id,
      thumbnail: n.thumbnail_url,
      views: n.views,
      likes: n.likes,
      duration: n.duration,
      kind: n.kind,
      in_degree: n.in_degree,
      out_degree: n.out_degree,
      run_ids: n.run_ids,
      run_types: n.run_types,
      community_id: n.community_id,
    })),
    links: payload.edges.map((e): GraphLink => ({
      source: e.source,
      target: e.target,
      position: e.position,
      run_id: e.run_id,
      run_type: e.run_type,
      run_name: e.run_name,
      title: e.title,
    })),
  };
}

function mapChannelGraphPayload(payload: ChannelGraphPayload): {
  nodes: GraphNode[];
  links: GraphLink[];
} {
  return {
    nodes: payload.nodes.map((n): GraphNode => {
      const kind: GraphNode["kind"] =
        n.out_degree > 0 && n.in_degree > 0
          ? "both"
          : n.out_degree > 0
            ? "source"
            : n.in_degree > 0
              ? "target"
              : "other";
      return {
        id: n.channel_id,
        title: n.channel_name,
        channel: n.channel_name,
        channel_id: n.channel_id,
        thumbnail: n.avatar_url,
        views: n.subscriber_count,
        likes: null,
        duration: null,
        kind,
        in_degree: n.in_degree,
        out_degree: n.out_degree,
        run_ids: n.run_ids,
        run_types: n.run_types,
      };
    }),
    links: payload.edges.map((e): GraphLink => ({
      source: e.source,
      target: e.target,
      run_id: e.run_ids?.[0] ?? null,
      run_type: null,
      run_name: null,
      title: `${e.video_edge_count} video edge${e.video_edge_count === 1 ? "" : "s"}`,
    })),
  };
}

export function FullNetworkView() {
  const runsQuery = useRuns();
  const [runId, setRunId] = useState<string | null>(null);
  const [temporalRuns, setTemporalRuns] = useState<string[]>([]);
  const [tab, setTab] = useState<"metrics" | "temporal" | "edges" | "graph" | "layers" | "commenters" | "expansion">("metrics");
  const [graphRunId, setGraphRunId] = useState<string | null>(null);
  const [graphChannelId, setGraphChannelId] = useState<string | null>(null);
  const [graphProjection, setGraphProjection] = useState<GraphProjection>("video");
  const [graphVideoId, setGraphVideoId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const [scrapeAllOpen, setScrapeAllOpen] = useState(false);
  const [scrapeVideoTarget, setScrapeVideoTarget] = useState<string | null>(null);
  const [selectedExpansionId, setSelectedExpansionId] = useState<string | null>(null);
  const expansionJob = useExpansionJob();

  const runs = useMemo(() => {
    const data = (runsQuery.data ?? []).slice();
    data.sort((a, b) => (b.started_at ?? "").localeCompare(a.started_at ?? ""));
    const ids = data.map((run) => run.run_id);
    return [...new Set(ids)];
  }, [runsQuery.data]);

  const runNames = useMemo(() => {
    const names = new Map<string, string>();
    for (const run of runsQuery.data ?? []) {
      if (run.name && !names.has(run.run_id)) names.set(run.run_id, run.name);
    }
    return names;
  }, [runsQuery.data]);

  const metrics = useNetworkMetrics(runId ?? undefined, 10, {
    retry: 1,
    onError: (err: Error) => console.error('Failed to load network metrics:', err),
  });

  const graphQuery = useNetworkGraph(
    graphRunId ?? undefined,
    graphChannelId ?? undefined,
    "source",
    graphProjection,
    { retry: 1 },
  );

  const scrapeRunMutation = useScrapeNetwork("run");
  const scrapeChannelMutation = useScrapeNetwork("channel");

  function showToast(message: string, type: "success" | "error") {
    setToast({ message, type });
    setTimeout(() => setToast(null), type === "success" ? 3000 : 5000);
  }

  const handleScrapeRun = async () => {
    if (!graphRunId) return;
    try {
      await scrapeRunMutation.mutateAsync({ run_id: graphRunId, dedupe: true });
      showToast(`Re-scrape queued for run ${graphRunId}`, "success");
    } catch (err) {
      showToast(`Failed to start scrape: ${(err as Error).message}`, "error");
    }
  };

  const handleScrapeChannel = async () => {
    if (!graphChannelId) return;
    try {
      await scrapeChannelMutation.mutateAsync({
        channel_id: graphChannelId,
        dedupe: true,
      });
      showToast(`Scrape queued for channel ${graphChannelId}`, "success");
    } catch (err) {
      showToast(`Failed to start scrape: ${(err as Error).message}`, "error");
    }
  };

  const startExpansionJob = async (
    fn: () => Promise<{ job_id: string }>,
    message: string,
  ) => {
    try {
      await expansionJob.mutateAsync(fn);
      showToast(message, "success");
    } catch (err) {
      showToast(`Failed to start expansion: ${(err as Error).message}`, "error");
    }
  };

  const handleScrapeAll = async (filters: ExpansionFilters) => {
    const scopeRunId = graphRunId ?? runId;
    setScrapeAllOpen(false);
    await startExpansionJob(
      () =>
        scrapeExpansionAll({
          run_id: scopeRunId,
          video_ids: [],
          filters,
        }),
      "Scrape-all expansion queued",
    );
  };

  const handleScrapeVideoExpansion = async (filters: ExpansionFilters) => {
    const target = scrapeVideoTarget;
    setScrapeVideoTarget(null);
    if (!target) return;
    await startExpansionJob(
      () => scrapeExpansionVideo(target, filters),
      `Expansion queued for video ${target}`,
    );
  };

  const openVideoScrapeDialog = async (videoId: string): Promise<void> => {
    setScrapeVideoTarget(videoId);
  };

  function toggleTemporalRun(id: string) {
    setTemporalRuns((prev) => {
      if (prev.includes(id)) return prev.filter((r) => r !== id);
      return [...prev, id];
    });
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Network slice
            </Label>
            <RunPicker
              runs={runs}
              names={runNames}
              value={runId}
              placeholder="All runs"
              onChange={(value) => {
                setRunId(value);
                setTab("metrics");
              }}
            />
          </div>

          <div className="flex items-center gap-1.5">
            {EXPORT_FORMATS.map((format) => (
              <a
                key={format}
                href={getNetworkExportUrl(format, runId ?? undefined)}
                download
                className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium outline-none hover:bg-muted focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <Download className="size-3.5" aria-hidden />
                {format}
              </a>
            ))}
          </div>
        </div>
      </Card>

      <Tabs value={tab} onValueChange={(value) => setTab(value as typeof tab)}>
        <TabsList>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="temporal">Temporal</TabsTrigger>
          <TabsTrigger value="edges">Edges</TabsTrigger>
          <TabsTrigger value="graph">Graph</TabsTrigger>
          <TabsTrigger value="layers">Layers</TabsTrigger>
          <TabsTrigger value="commenters">Commenters</TabsTrigger>
          <TabsTrigger value="expansion">Expansion</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="mt-4 space-y-4">
          {metrics.isError ? (
            <ErrorState
              message={
                metrics.error instanceof Error
                  ? metrics.error.message
                  : "Failed to load network metrics"
              }
              retry={() => metrics.refetch()}
            />
          ) : metrics.data ? (
            <>
              {runId ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">slice</Badge>
                  <code>{runNames.get(runId) ?? runId}</code>
                </div>
              ) : null}
              <NetworkMetricTiles metrics={metrics.data} />
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <DegreeDistributionPanel distribution={metrics.data.degree_distribution} />
                <RankingPanel title="Top hubs" videos={metrics.data.top_hubs} valueLabel="hub" />
                <RankingPanel title="Top authorities" videos={metrics.data.top_authorities} valueLabel="auth" />
                <RankingPanel title="Most recommended" videos={metrics.data.most_recommended} valueLabel="×" />
                <RankingPanel title="Most active sources" videos={metrics.data.most_active_sources} valueLabel="→" />
              </div>
            </>
          ) : (
            <LoadingState label="Loading network metrics…" />
          )}
        </TabsContent>

        <TabsContent value="temporal" className="mt-4 space-y-4">
          <Card className="p-4">
            <h3 className="mb-2 text-sm font-medium">Runs to compare</h3>
            {runs.length === 0 ? (
              <EmptyState
                title="No collection runs yet"
                description="Collect something first, then compare runs over time."
                className="min-h-24 p-4"
              />
            ) : (
              <div className="flex flex-wrap gap-2">
                {runs.map((id) => {
                  const isSelected = temporalRuns.includes(id);
                  return (
                    <button
                      key={id}
                      type="button"
                      aria-pressed={isSelected}
                      onClick={() => toggleTemporalRun(id)}
                      className="rounded-md border border-border px-2.5 py-1 font-mono text-xs outline-none hover:bg-muted focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-pressed:bg-primary aria-pressed:text-primary-foreground"
                    >
                      {runNames.get(id) ?? id}
                    </button>
                  );
                })}
              </div>
            )}
          </Card>
          <TemporalOverlay runIds={temporalRuns} />
        </TabsContent>

        <TabsContent value="edges" className="mt-4">
          <EdgeTable runId={runId ?? undefined} />
        </TabsContent>

        <TabsContent value="graph" className="mt-4 space-y-4">
          <Card className="p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Projection
              </Label>
              <Select
                value={graphProjection}
                onValueChange={(v) => setGraphProjection(v as GraphProjection)}
                items={[
                  { value: "video", label: "Video graph" },
                  { value: "channel", label: "Channel graph" },
                ]}
              >
                <SelectTrigger className="w-48" aria-label="Select graph projection">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="video">Video graph</SelectItem>
                  <SelectItem value="channel">Channel graph</SelectItem>
                </SelectContent>
              </Select>
              {graphProjection === "channel" && graphQuery.data ? (
                <Badge variant="outline">
                  {(graphQuery.data as ChannelGraphPayload).unattributed_edges > 0
                    ? `${(graphQuery.data as ChannelGraphPayload).unattributed_edges} edges without channel attribution`
                    : "All edges attributed"}
                </Badge>
              ) : null}
            </div>
            {graphQuery.isError ? (
              <ErrorState
                message={
                  graphQuery.error instanceof Error
                    ? graphQuery.error.message
                    : "Failed to load network graph"
                }
                retry={() => graphQuery.refetch()}
              />
            ) : graphQuery.data ? (
              graphProjection === "channel" ? (
                <NetworkGraph
                  nodes={mapChannelGraphPayload(graphQuery.data as ChannelGraphPayload).nodes}
                  links={mapChannelGraphPayload(graphQuery.data as ChannelGraphPayload).links}
                  runs={graphQuery.data.runs}
                  channels={graphQuery.data.channels}
                  selectedRun={graphRunId ?? undefined}
                  selectedChannel={graphChannelId ?? undefined}
                  onRunChange={(v) => setGraphRunId(v === "__all" ? null : v)}
                  onChannelChange={(v) => setGraphChannelId(v === "__all" ? null : v)}
                  onClearFilters={() => {
                    setGraphRunId(null);
                    setGraphChannelId(null);
                  }}
                  onScrapeClick={(channelId) => openVideoScrapeDialog(channelId)}
                />
              ) : (
                <NetworkGraph
                  nodes={mapGraphPayload(graphQuery.data as NetworkGraphPayload).nodes}
                  links={mapGraphPayload(graphQuery.data as NetworkGraphPayload).links}
                  runs={graphQuery.data.runs}
                  channels={graphQuery.data.channels}
                  selectedRun={graphRunId ?? undefined}
                  selectedChannel={graphChannelId ?? undefined}
                  onRunChange={(v) => setGraphRunId(v === "__all" ? null : v)}
                  onChannelChange={(v) => setGraphChannelId(v === "__all" ? null : v)}
                  onClearFilters={() => {
                    setGraphRunId(null);
                    setGraphChannelId(null);
                  }}
                  onScrapeClick={(videoId) => openVideoScrapeDialog(videoId)}
                  onOverlapClick={(videoId) => {
                    setGraphVideoId(videoId);
                    setTab("commenters");
                  }}
                />
              )
            ) : (
              <LoadingState label="Loading network graph…" />
            )}

            <div className="mt-3 flex flex-wrap gap-2 border-t pt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setScrapeAllOpen(true)}
                disabled={expansionJob.isRunning}
              >
                {expansionJob.isRunning ? (
                  <Loader2 className="animate-spin" aria-hidden />
                ) : (
                  <Sparkles aria-hidden />
                )}
                Scrape all recommendations
              </Button>
              {graphRunId ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void handleScrapeRun()}
                  disabled={scrapeRunMutation.isPending || scrapeRunMutation.isRunning}
                >
                  {scrapeRunMutation.isRunning ? (
                    <Loader2 className="animate-spin" aria-hidden />
                  ) : (
                    <Sparkles aria-hidden />
                  )}
                  Re-scrape this run
                </Button>
              ) : null}
              {graphChannelId ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void handleScrapeChannel()}
                  disabled={scrapeChannelMutation.isPending || scrapeChannelMutation.isRunning}
                >
                  {scrapeChannelMutation.isRunning ? (
                    <Loader2 className="animate-spin" aria-hidden />
                  ) : (
                    <Sparkles aria-hidden />
                  )}
                  Scrape this channel
                </Button>
              ) : null}
            </div>
            {scrapeRunMutation.jobId ? (
              <div className="mt-3">
                <JobProgressCard
                  key={scrapeRunMutation.jobId}
                  jobId={scrapeRunMutation.jobId}
                  title="Re-scraping run"
                />
              </div>
            ) : null}
            {scrapeChannelMutation.jobId ? (
              <div className="mt-3">
                <JobProgressCard
                  key={scrapeChannelMutation.jobId}
                  jobId={scrapeChannelMutation.jobId}
                  title="Scraping channel"
                />
              </div>
            ) : null}
            {expansionJob.jobId ? (
              <div className="mt-3">
                <JobProgressCard
                  key={expansionJob.jobId}
                  jobId={expansionJob.jobId}
                  title="Scraping recommendations"
                />
              </div>
            ) : null}
          </Card>
        </TabsContent>
        <TabsContent value="layers" className="mt-4">
          <LayerPanel />
        </TabsContent>
        <TabsContent value="commenters" className="mt-4">
          <CommenterOverlapView
            initialVideoIds={graphVideoId ? [graphVideoId] : []}
            initialChannelIds={graphChannelId ? [graphChannelId] : []}
          />
        </TabsContent>
        <TabsContent value="expansion" className="mt-4">
          <ExpansionPanel
            selectedActionId={selectedExpansionId}
            onSelectAction={setSelectedExpansionId}
          />
        </TabsContent>
      </Tabs>

      <ScrapeFiltersDialog
        open={scrapeAllOpen}
        onOpenChange={setScrapeAllOpen}
        title="Scrape all recommendations"
        description={`Expand the current network slice one hop${
          graphRunId ? " (scoped to the selected run)" : ""
        }. A new auto-Project organizes this action's runs and datasets.`}
        onConfirm={handleScrapeAll}
      />

      <ScrapeFiltersDialog
        open={scrapeVideoTarget !== null}
        onOpenChange={(open) => {
          if (!open) setScrapeVideoTarget(null);
        }}
        title="Scrape recommendations"
        description={
          scrapeVideoTarget
            ? `One-hop expansion of video ${scrapeVideoTarget}.`
            : undefined
        }
        onConfirm={handleScrapeVideoExpansion}
      />

      {toast && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-in">
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        </div>
      )}
    </div>
  );
}

function RunPicker({
  runs,
  names,
  value,
  placeholder,
  onChange,
}: {
  runs: string[];
  names: Map<string, string>;
  value: string | null;
  placeholder: string;
  onChange: (value: string | null) => void;
}) {
  return (
    <Select
      value={value ?? ""}
      onValueChange={(next) => onChange(next || null)}
      items={runs.map((id) => ({ value: id, label: names.get(id) ?? id }))}
    >
      <SelectTrigger className="w-72" aria-label="Select network slice run">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="">{placeholder}</SelectItem>
        {runs.map((id) => (
          <SelectItem key={id} value={id}>
            {names.get(id) ?? id}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
