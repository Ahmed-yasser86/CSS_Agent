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
import { useNetworkMetrics, getNetworkExportUrl } from "@/services/networkFull";
import { EXPORT_FORMATS } from "@/lib/network-full-types";

export function FullNetworkView() {
  const runsQuery = useRuns();
  const [runId, setRunId] = useState<string | null>(null);
  const [temporalRuns, setTemporalRuns] = useState<string[]>([]);
  const [tab, setTab] = useState<"metrics" | "temporal" | "edges">("metrics");

  const runs = useMemo(() => {
    const ids = (runsQuery.data ?? []).map((run) => run.run_id);
    return [...new Set(ids)];
  }, [runsQuery.data]);

  const metrics = useNetworkMetrics(runId ?? undefined, 10);

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

      <Tabs value={tab} onValueChange={(value) => setTab(value as "metrics" | "temporal" | "edges")}>
        <TabsList>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="temporal">Temporal</TabsTrigger>
          <TabsTrigger value="edges">Edges</TabsTrigger>
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
                  <code>{runId}</code>
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
                      {id}
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
      </Tabs>
    </div>
  );
}

function RunPicker({
  runs,
  value,
  placeholder,
  onChange,
}: {
  runs: string[];
  value: string | null;
  placeholder: string;
  onChange: (value: string | null) => void;
}) {
  return (
    <Select
      value={value ?? ""}
      onValueChange={(next) => onChange(next || null)}
      items={runs.map((id) => ({ value: id, label: id }))}
    >
      <SelectTrigger className="w-72" aria-label="Select network slice run">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="">{placeholder}</SelectItem>
        {runs.map((id) => (
          <SelectItem key={id} value={id}>
            {id}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
