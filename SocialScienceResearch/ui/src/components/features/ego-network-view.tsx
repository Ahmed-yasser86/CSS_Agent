"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-react";
import type { VideoNetworkContext } from "@/lib/types";
import { useNetworkVideoContext, useRuns } from "@/services/queries";
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/features/state";
import { NetworkGraph } from "@/components/features/network-graph";
import { DataTable, type Column } from "@/components/features/data-table";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatNumber } from "@/lib/format";

export function EgoNetworkView({ videoId }: { videoId: string }) {
  const [runId, setRunId] = useState<string>("all");
  const runsQuery = useRuns("recommendation");
  const contextQuery = useNetworkVideoContext(
    videoId,
    runId === "all" ? undefined : runId,
  );

  const recommendationRuns =
    runsQuery.data?.filter((r) => r.status !== "pending" && r.status !== "running") ?? [];

  const graph = useMemo(() => {
    const context = contextQuery.data;
    if (!context) return { nodes: [], links: [] as { source: string; target: string }[] };
    const nodes = new Map<string, { id: string; title?: string; kind: "source" | "target" | "both" | "other"; value: number }>();
    nodes.set(videoId, { id: videoId, kind: "source", value: 3 });
    for (const e of context.recommended_by) {
      const existing = nodes.get(e.source_video_id);
      if (existing) {
        existing.kind = "both";
      } else {
        nodes.set(e.source_video_id, { id: e.source_video_id, title: e.title ?? undefined, kind: "other", value: 1 });
      }
    }
    for (const e of context.recommends) {
      const existing = nodes.get(e.recommended_video_id);
      if (existing) {
        existing.kind = "both";
      } else {
        nodes.set(e.recommended_video_id, { id: e.recommended_video_id, title: e.title ?? undefined, kind: "target", value: 1 });
      }
    }
    const links: { source: string; target: string }[] = [
      ...context.recommended_by.map((e) => ({ source: e.source_video_id, target: videoId })),
      ...context.recommends.map((e) => ({ source: videoId, target: e.recommended_video_id })),
    ];
    return { nodes: [...nodes.values()], links };
  }, [contextQuery.data, videoId]);

  const recommendedByColumns: Column<VideoNetworkContext["recommended_by"][number]>[] = [
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
      sortValue: (e) => e.position,
      cell: (e) => (e.position === null ? "—" : `#${e.position + 1}`),
      className: "text-right tabular-nums",
    },
    {
      key: "run_id",
      header: "Run",
      sortable: true,
      sortValue: (e) => e.run_id ?? "",
      cell: (e) => <code className="text-xs text-muted-foreground">{e.run_id ?? "—"}</code>,
    },
  ];

  const recommendsColumns: Column<VideoNetworkContext["recommends"][number]>[] = [
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
      sortValue: (e) => e.position,
      cell: (e) => (e.position === null ? "—" : `#${e.position + 1}`),
      className: "text-right tabular-nums",
    },
    {
      key: "run_id",
      header: "Run",
      sortable: true,
      sortValue: (e) => e.run_id ?? "",
      cell: (e) => <code className="text-xs text-muted-foreground">{e.run_id ?? "—"}</code>,
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
            ...recommendationRuns.map((r) => ({ value: r.run_id, label: r.run_id })),
          ]}
        >
          <SelectTrigger size="sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="w-[--anchor-width]">
            <SelectItem value="all">All runs</SelectItem>
            {recommendationRuns.map((r) => (
              <SelectItem key={r.run_id} value={r.run_id}>
                {r.run_id}
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
        <h2 className="mb-3 text-sm font-medium">Graph</h2>
        <NetworkGraph nodes={graph.nodes} links={graph.links} />
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <section aria-label="Who recommends this video">
          <h2 className="mb-2 flex items-center gap-2 text-sm font-medium">
            <ArrowDownToLine className="size-4 text-muted-foreground" aria-hidden />
            Recommended by ({context.recommended_by.length})
          </h2>
          <DataTable columns={recommendedByColumns} rows={context.recommended_by} getRowKey={(e) => `${e.source_video_id}-${e.run_id ?? ""}`} ariaLabel="Videos recommending this video" />
        </section>
        <section aria-label="Who this video recommends">
          <h2 className="mb-2 flex items-center gap-2 text-sm font-medium">
            <ArrowUpFromLine className="size-4 text-muted-foreground" aria-hidden />
            Recommends ({context.recommends.length})
          </h2>
          <DataTable columns={recommendsColumns} rows={context.recommends} getRowKey={(e) => `${e.recommended_video_id}-${e.run_id ?? ""}`} ariaLabel="Videos recommended by this video" />
        </section>
      </div>
    </div>
  );
}
