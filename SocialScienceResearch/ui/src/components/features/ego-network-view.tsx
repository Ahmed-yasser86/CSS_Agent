"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowDownToLine, ArrowUpFromLine, Loader2, Sparkles } from "lucide-react";
import { useRuns, useNetworkVideoContext } from "@/services/queries";
import {
  LoadingState,
  ErrorState,
  EmptyState,
  Toast,
} from "@/components/features/state";
import { NetworkGraph, type GraphLink, type GraphNode } from "@/components/features/network-graph";
import { JobProgressCard } from "@/components/features/job-progress-card";
import { DataTable, type Column } from "@/components/features/data-table";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ScrapeFiltersDialog } from "@/components/features/network-expansion/scrape-filters-dialog";
import {
  useExpansionJob,
  scrapeExpansionVideo,
  scrapeExpansionAll,
} from "@/services/networkExpansion";
import type { ScrapeFilters } from "@/lib/network-expansion-types";
import { formatNumber } from "@/lib/format";

interface RecommendationEdge {
  source_video_id?: string;
  recommended_video_id?: string;
  title?: string | null;
  position?: number | null;
  run_id?: string | null;
  run_type?: string | null;
}

export function EgoNetworkView({ videoId }: { videoId: string }) {
  const router = useRouter();
  const [runId, setRunId] = useState<string>("all");
  const runsQuery = useRuns("recommendation");
  const recommendationRuns =
    runsQuery.data?.filter((r) => r.status !== "pending" && r.status !== "running") ?? [];
  const runNames = new Map(
    recommendationRuns.map((r) => [r.run_id, r.name ?? r.run_id]),
  );

  const contextQuery = useNetworkVideoContext(
    videoId,
    runId === "all" ? undefined : runId,
  );

  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const [scrapeVideoTarget, setScrapeVideoTarget] = useState<string | null>(null);
  const [scrapeAllOpen, setScrapeAllOpen] = useState(false);
  const expansionJob = useExpansionJob();

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), type === "success" ? 3000 : 5000);
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

  const handleScrapeVideo = async (filters: ScrapeFilters) => {
    const target = scrapeVideoTarget;
    setScrapeVideoTarget(null);
    if (!target) return;
    await startExpansionJob(
      () => scrapeExpansionVideo(target, filters),
      `Expansion queued for video ${target}`,
    );
  };

  const handleScrapeAll = async (filters: ScrapeFilters) => {
    const context = contextQuery.data;
    const videoIds = new Set<string>([videoId]);
    for (const e of context?.recommended_by ?? []) if (e.source_video_id) videoIds.add(e.source_video_id);
    for (const e of context?.recommends ?? []) if (e.recommended_video_id) videoIds.add(e.recommended_video_id);
    setScrapeAllOpen(false);
    await startExpansionJob(
      () =>
        scrapeExpansionAll({
          run_id: runId === "all" ? null : runId,
          video_ids: [...videoIds],
          filters,
        }),
      "Scrape-all expansion queued",
    );
  };

  const handleNodeClick = (id: string) => {
    router.push(`/network/videos/${id}`);
  };

  const graph = useMemo(() => {
    const context = contextQuery.data;
    if (!context) return { nodes: [] as GraphNode[], links: [] as GraphLink[] };

    const nodes = new Map<string, GraphNode>();
    nodes.set(videoId, {
      id: videoId,
      kind: "source",
      in_degree: context.in_degree,
      out_degree: context.out_degree,
    });

    for (const e of context.recommended_by) {
      const existing = nodes.get(e.source_video_id);
      if (existing) {
        existing.kind = "both";
      } else {
        nodes.set(e.source_video_id, {
          id: e.source_video_id,
          title: e.title ?? undefined,
          kind: "other",
          in_degree: 0,
          out_degree: 1,
        });
      }
    }

    for (const e of context.recommends) {
      const existing = nodes.get(e.recommended_video_id);
      if (existing) {
        existing.kind = "both";
      } else {
        nodes.set(e.recommended_video_id, {
          id: e.recommended_video_id,
          title: e.title ?? undefined,
          kind: "target",
          in_degree: 1,
          out_degree: 0,
        });
      }
    }

    const links: GraphLink[] = [
      ...context.recommended_by.map((e) => ({
        source: e.source_video_id,
        target: videoId,
        run_id: e.run_id,
        run_type: e.run_type,
      })),
      ...context.recommends.map((e) => ({
        source: videoId,
        target: e.recommended_video_id,
        run_id: e.run_id,
        run_type: e.run_type,
      })),
    ];

    return { nodes: [...nodes.values()], links };
  }, [contextQuery.data, videoId]);

  const recommendedByColumns: Column<RecommendationEdge>[] = [
    {
      key: "source_video_id",
      header: "Source video",
      sortable: true,
      sortValue: (e) => e.source_video_id,
      cell: (e) => (
        <Link
          href={`/network/videos/${e.source_video_id}`}
          className="font-mono text-xs text-primary underline-offset-2 hover:underline"
        >
          {e.source_video_id}
        </Link>
      ),
    },
    {
      key: "title",
      header: "Title",
      cell: (e) => <span className="line-clamp-1 max-w-md">{e.title ?? "—"}</span>,
    },
    {
      key: "position",
      header: "Position",
      sortable: true,
      sortValue: (e) => e.position ?? -1,
      cell: (e) => (e.position == null ? "—" : `#${e.position + 1}`),
      className: "text-right tabular-nums",
    },
    {
      key: "run_id",
      header: "Run",
      sortable: true,
      sortValue: (e) => e.run_id ?? "",
      cell: (e) => (
        <code className="text-xs text-muted-foreground">
          {e.run_id ? runNames.get(e.run_id) ?? e.run_id : "—"}
        </code>
      ),
    },
    {
      key: "run_type",
      header: "Run Type",
      sortable: true,
      sortValue: (e) => e.run_type ?? "",
      cell: (e) => <code className="text-xs text-muted-foreground">{e.run_type ?? "—"}</code>,
    },
  ];

  const recommendsColumns: Column<RecommendationEdge>[] = [
    {
      key: "recommended_video_id",
      header: "Recommended video",
      sortable: true,
      sortValue: (e) => e.recommended_video_id,
      cell: (e) => (
        <Link
          href={`/network/videos/${e.recommended_video_id}`}
          className="font-mono text-xs text-primary underline-offset-2 hover:underline"
        >
          {e.recommended_video_id}
        </Link>
      ),
    },
    {
      key: "title",
      header: "Title",
      cell: (e) => <span className="line-clamp-1 max-w-md">{e.title ?? "—"}</span>,
    },
    {
      key: "position",
      header: "Position",
      sortable: true,
      sortValue: (e) => e.position ?? -1,
      cell: (e) => (e.position == null ? "—" : `#${e.position + 1}`),
      className: "text-right tabular-nums",
    },
    {
      key: "run_id",
      header: "Run",
      sortable: true,
      sortValue: (e) => e.run_id ?? "",
      cell: (e) => (
        <code className="text-xs text-muted-foreground">
          {e.run_id ? runNames.get(e.run_id) ?? e.run_id : "—"}
        </code>
      ),
    },
    {
      key: "run_type",
      header: "Run Type",
      sortable: true,
      sortValue: (e) => e.run_type ?? "",
      cell: (e) => <code className="text-xs text-muted-foreground">{e.run_type ?? "—"}</code>,
    },
  ];

  if (contextQuery.isLoading) return <LoadingState label="Loading ego-network…" />;
  if (contextQuery.isError)
    return <ErrorState message={(contextQuery.error as Error).message} />;
  const context = contextQuery.data!;

  if (context.in_degree === 0 && context.out_degree === 0) {
    return (
      <EmptyState
        title="No network context for this video"
        description="This video has no observed recommendation edges in the selected slice."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          Ego-network: who recommends this video (in-edges) and whom it
          recommends (out-edges), attributed to collection runs.
        </p>
        <Select
          value={runId}
          onValueChange={(v) => setRunId(v ?? "all")}
          items={[
            { value: "all", label: "All runs" },
            ...recommendationRuns.map((r) => ({ value: r.run_id, label: r.name ?? r.run_id })),
          ]}
        >
          <SelectTrigger size="sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="w-[--anchor-width]">
            <SelectItem value="all">All runs</SelectItem>
            {recommendationRuns.map((r) => (
              <SelectItem key={r.run_id} value={r.run_id}>
                {r.name ?? r.run_id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Card className="p-3">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">In-degree</p>
          <p className="text-2xl font-semibold tabular-nums">{formatNumber(context.in_degree)}</p>
        </Card>
        <Card className="p-3">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Out-degree</p>
          <p className="text-2xl font-semibold tabular-nums">{formatNumber(context.out_degree)}</p>
        </Card>
        <Card className="p-3">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">PageRank</p>
          <p className="text-2xl font-semibold tabular-nums">
            {context.pagerank === null ? "—" : context.pagerank.toFixed(6)}
          </p>
        </Card>
      </div>

      <Card className="p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-medium">Graph</h2>
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
        </div>
        <NetworkGraph 
          nodes={graph.nodes} 
          links={graph.links} 
          onNavigate={handleNodeClick}
          onScrapeClick={async (id) => {
            setScrapeVideoTarget(id);
          }}
        />
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

      <div className="grid gap-4 lg:grid-cols-2">
        <section aria-label="Who recommends this video">
          <h2 className="mb-2 flex items-center gap-2 text-sm font-medium">
            <ArrowDownToLine className="size-4 text-muted-foreground" aria-hidden />
            Recommended by ({context.recommended_by.length})
          </h2>
          <DataTable columns={recommendedByColumns} rows={context.recommended_by} getRowKey={(e) => `${e.source_video_id}-${e.run_id ?? ""}`} initialSortKey="position" ariaLabel="Videos recommending this video" />
        </section>
        <section aria-label="Who this video recommends">
          <h2 className="mb-2 flex items-center gap-2 text-sm font-medium">
            <ArrowUpFromLine className="size-4 text-muted-foreground" aria-hidden />
            Recommends ({context.recommends.length})
          </h2>
          <DataTable columns={recommendsColumns} rows={context.recommends} getRowKey={(e) => `${e.recommended_video_id}-${e.run_id ?? ""}`} initialSortKey="position" ariaLabel="Videos recommended by this video" />
        </section>
      </div>

      <ScrapeFiltersDialog
        open={scrapeAllOpen}
        onOpenChange={setScrapeAllOpen}
        title="Scrape all recommendations"
        description={`Expand the ego network (${videoId} and its neighbors) one hop. A new auto-Project organizes this action's runs and datasets.`}
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
        onConfirm={handleScrapeVideo}
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