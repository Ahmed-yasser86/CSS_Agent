"use client";

import { useState } from "react";
import { FlaskConical, Loader2, SlidersHorizontal } from "lucide-react";
import type { UseMutationResult } from "@tanstack/react-query";
import type { SamplingResult, SamplingSpec, SamplingStrategy } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface StrategyOption {
  value: SamplingStrategy;
  label: string;
  description: string;
}

const STRATEGIES: Record<"video" | "comment", StrategyOption[]> = {
  video: [
    { value: "top_views", label: "Top by views", description: "Highest view counts first." },
    { value: "bottom_views", label: "Bottom by views", description: "Lowest view counts first." },
    { value: "top_likes", label: "Top by likes", description: "Highest like counts first." },
    { value: "bottom_likes", label: "Bottom by likes", description: "Lowest like counts first." },
    { value: "top_engagement", label: "Top by engagement rate", description: "Highest (likes+comments)/views." },
    { value: "bottom_engagement", label: "Bottom by engagement rate", description: "Lowest (likes+comments)/views." },
    { value: "top_comments", label: "Top by comments", description: "Highest comment counts first." },
    { value: "top_comment_rate", label: "Top by comment rate", description: "Highest comments/views." },
    { value: "top_like_rate", label: "Top by like rate", description: "Highest likes/views." },
    { value: "longest", label: "Longest", description: "Longest duration first." },
    { value: "shortest", label: "Shortest", description: "Shortest duration first." },
    { value: "latest", label: "Latest published", description: "Most recent upload first." },
    { value: "earliest", label: "Earliest published", description: "Oldest upload first." },
    { value: "date_range", label: "Date range", description: "Published within the chosen window." },
    { value: "random", label: "Random (seeded)", description: "Seeded random order for reproducibility." },
    { value: "stratified", label: "Stratified", description: "Balanced per year/month/weekday stratum." },
  ],
  comment: [
    { value: "top_likes", label: "Top by likes", description: "Highest like counts first." },
    { value: "latest", label: "Latest published", description: "Most recent comment first." },
    { value: "earliest", label: "Earliest published", description: "Oldest comment first." },
    { value: "date_range", label: "Date range", description: "Published within the chosen window." },
    { value: "random", label: "Random (seeded)", description: "Seeded random order for reproducibility." },
    { value: "stratified", label: "Stratified", description: "Balanced per year/month/weekday stratum." },
  ],
};

const STRATA_OPTIONS: { value: "year" | "month" | "weekday"; label: string }[] = [
  { value: "year", label: "Year" },
  { value: "month", label: "Month" },
  { value: "weekday", label: "Weekday" },
];

export function SamplingWorkbench({
  entityType,
  populationSize,
  mutate,
}: {
  entityType: "video" | "comment";
  populationSize: number;
  mutate: UseMutationResult<SamplingResult, Error, SamplingSpec>;
}) {
  const [strategy, setStrategy] = useState<SamplingStrategy>("random");
  const [size, setSize] = useState<string>("10");
  const [percent, setPercent] = useState<string>("");
  const [seed, setSeed] = useState<string>("");
  const [strata, setStrata] = useState<"year" | "month" | "weekday">("year");
  const [perStratum, setPerStratum] = useState<string>("1");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [result, setResult] = useState<SamplingResult | null>(null);

  const options = STRATEGIES[entityType];
  const selected = options.find((o) => o.value === strategy);

  function execute() {
    const spec: SamplingSpec = { strategy };
    if (size !== "") spec.size = Math.max(0, Math.floor(Number(size)));
    if (percent !== "") spec.percent = Number(percent);
    if (seed !== "") spec.seed = Number(seed);
    if (strategy === "stratified") {
      spec.strata = strata;
      if (perStratum !== "") spec.sample_per_stratum = Math.max(1, Math.floor(Number(perStratum)));
    }
    if (strategy === "date_range") {
      if (dateFrom) spec.date_from = dateFrom;
      if (dateTo) spec.date_to = dateTo;
    }
    setResult(null);
    mutate.mutate(spec, {
      onSuccess: (data) => setResult(data),
    });
  }

  const showStratified = strategy === "stratified";
  const showDateRange = strategy === "date_range";

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Card className="p-4">
        <h3 className="mb-1 flex items-center gap-2 text-sm font-medium">
          <SlidersHorizontal className="size-4 text-muted-foreground" aria-hidden />
          Sampling criteria
        </h3>
        <p className="mb-4 text-xs text-muted-foreground">
          Sampling is reproducible: the exact criteria are recorded and returned
          with every sample. Videos or comments whose ranking metric is
          unavailable are ranked last and reported — never assigned a value.
        </p>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="sampling-strategy">Strategy</Label>
            <Select
              value={strategy}
              onValueChange={(v) => setStrategy(v as SamplingStrategy)}
              items={options.map((o) => ({ value: o.value, label: o.label }))}
            >
              <SelectTrigger id="sampling-strategy" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="w-[--anchor-width]">
                {options.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <span className="flex flex-col">
                      <span>{option.label}</span>
                      <span className="text-xs font-normal text-muted-foreground">
                        {option.description}
                      </span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="sample-size">Size (count)</Label>
              <Input
                id="sample-size"
                type="number"
                min={0}
                value={size}
                onChange={(e) => setSize(e.target.value)}
                disabled={percent !== ""}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="sample-percent">Or percent (%)</Label>
              <Input
                id="sample-percent"
                type="number"
                min={0}
                max={100}
                value={percent}
                onChange={(e) => setPercent(e.target.value)}
                disabled={size !== ""}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="sample-seed">Seed (optional)</Label>
              <Input
                id="sample-seed"
                type="number"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                placeholder="default (42)"
              />
            </div>
          </div>

          {showStratified ? (
            <div className="grid grid-cols-2 gap-3 rounded-md border bg-muted/30 p-3">
              <div className="space-y-1.5">
                <Label htmlFor="strata">Stratum</Label>
                <Select
                  value={strata}
                  onValueChange={(v) => setStrata(v as "year" | "month" | "weekday")}
                  items={STRATA_OPTIONS}
                >
                  <SelectTrigger id="strata" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="w-[--anchor-width]">
                    {STRATA_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="per-stratum">Per stratum</Label>
                <Input
                  id="per-stratum"
                  type="number"
                  min={1}
                  value={perStratum}
                  onChange={(e) => setPerStratum(e.target.value)}
                />
              </div>
            </div>
          ) : null}

          {showDateRange ? (
            <div className="grid grid-cols-2 gap-3 rounded-md border bg-muted/30 p-3">
              <div className="space-y-1.5">
                <Label htmlFor="date-from">From</Label>
                <Input
                  id="date-from"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="date-to">To</Label>
                <Input
                  id="date-to"
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>
          ) : null}

          <Button onClick={execute} disabled={mutate.isPending}>
            {mutate.isPending ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Sampling…
              </>
            ) : (
              <>
                <FlaskConical className="size-4" aria-hidden />
                Run sample
              </>
            )}
          </Button>

          {mutate.isError ? (
            <p className="text-sm text-destructive">
              {(mutate.error as Error).message}
            </p>
          ) : null}
        </div>
      </Card>

      <div className="space-y-4">
        <Card className="p-4">
          <h3 className="mb-2 text-sm font-medium">Method</h3>
          <p className="text-sm text-muted-foreground">
            {selected?.description ?? ""}{" "}
            {strategy === "random"
              ? "Uses the configured RNG seed so the same criteria reproduce the same sample."
              : strategy === "stratified"
                ? `Balanced selection by ${strata}.`
                : strategy === "date_range"
                  ? "Only records published inside the chosen window contribute."
                  : "Items lacking the metric are ranked last and counted in missing-metric reporting."}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Population: {formatNumber(populationSize)}{" "}
            {entityType === "video" ? "video(s)" : "comment(s)"}
          </p>
        </Card>

        {result ? (
          <Card className="space-y-3 p-4">
            <h3 className="text-sm font-medium">Sample result</h3>
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <ResultField label="Strategy" value={result.strategy} />
              <ResultField label="Population" value={formatNumber(result.population_size)} />
              <ResultField label="Sample size" value={formatNumber(result.sample_size)} />
              <ResultField label="Seed" value={result.seed === null ? "—" : String(result.seed)} />
            </div>
            {result.missing_metric_count > 0 ? (
              <p className="text-xs text-muted-foreground">
                {formatNumber(result.missing_metric_count)} record(s) had no value
                for the ranking metric and were ranked last (reported, never
                fabricated).
              </p>
            ) : null}
            <div>
              <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Recorded criteria (reproducibility)
              </h4>
              <pre className="overflow-x-auto rounded-md border bg-muted/40 p-3 text-xs">
                {JSON.stringify(result.criteria_json, null, 2)}
              </pre>
            </div>
            <div>
              <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Entity ids ({result.sample_size})
              </h4>
              <div className="flex max-h-40 flex-wrap gap-1 overflow-y-auto">
                {result.entity_ids.map((id) => (
                  <code
                    key={id}
                    className="rounded border border-border bg-muted/40 px-1.5 py-0.5 text-[10px]"
                  >
                    {id}
                  </code>
                ))}
                {result.entity_ids.length === 0 ? (
                  <span className="text-xs text-muted-foreground">
                    Empty sample — no records matched the criteria.
                  </span>
                ) : null}
              </div>
            </div>
          </Card>
        ) : null}

        {!result && !mutate.isPending ? (
          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Run the sample to preview the exact criteria that will be recorded
            and the resulting entity ids.
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ResultField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-2">
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="truncate font-mono text-xs">{value}</p>
    </div>
  );
}
