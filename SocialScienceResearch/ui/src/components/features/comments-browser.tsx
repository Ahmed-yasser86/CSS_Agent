"use client";

import { useState } from "react";
import { MessageSquare } from "lucide-react";
import type { Comment } from "@/lib/types";
import {
  useVideoComments,
  useCommentPercentiles,
  useCommentVelocity,
  useSampleComments,
} from "@/services/queries";
import { DataTable, type Column } from "@/components/features/data-table";
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/features/state";
import { ChartCard, HistogramChart, TimelineChart } from "@/components/features/charts";
import { SamplingWorkbench } from "@/components/features/sampling-workbench";
import { AvailabilityBadge } from "@/components/features/availability-badge";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatDateTime, formatNumber } from "@/lib/format";

const BAND_ORDER = ["75", "90", "95", "99"];

export function CommentsBrowser({ videoId }: { videoId: string }) {
  const [bucket, setBucket] = useState<"day" | "hour">("day");
  const commentsQuery = useVideoComments(videoId);
  const percentilesQuery = useCommentPercentiles(videoId);
  const velocityQuery = useCommentVelocity(videoId, bucket);
  const sampleMutation = useSampleComments(videoId);

  const columns: Column<Comment>[] = [
    {
      key: "author",
      header: "Author",
      sortable: true,
      sortValue: (c) => c.author_name ?? "",
      cell: (c) => (
        <span className="flex items-center gap-1.5">
          {c.is_author ? <Badge variant="secondary">uploader</Badge> : null}
          <span className="font-medium">{c.author_name ?? c.author_id ?? "anonymous"}</span>
        </span>
      ),
    },
    {
      key: "comment_text",
      header: "Comment",
      cell: (c) => (
        <span className="line-clamp-2 max-w-xl text-sm">{c.comment_text ?? "—"}</span>
      ),
    },
    {
      key: "published_at",
      header: "Published",
      sortable: true,
      sortValue: (c) => c.published_at ?? "",
      cell: (c) => formatDateTime(c.published_at),
    },
    {
      key: "thread",
      header: "Thread",
      sortable: true,
      sortValue: (c) => (c.is_reply ? "reply" : "root"),
      cell: (c) => (
        <Badge variant="outline">{c.is_reply ? "reply" : "root"}</Badge>
      ),
    },
  ];

  const bands = percentilesQuery.data;

  return (
    <div className="space-y-6">
      <section aria-label="Comment like distribution">
        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Like-count distribution"
            description="Histogram of each comment's latest observed like count, with percentile bands."
          >
            {percentilesQuery.isLoading ? (
              <LoadingState label="Computing percentiles…" />
            ) : percentilesQuery.isError ? (
              <ErrorState message={(percentilesQuery.error as Error).message} />
            ) : bands && bands.availability === "missing" ? (
              <EmptyState
                title="No observed comment like counts"
                description="Percentile bands require at least one comment with an observed like count."
              />
            ) : bands ? (
              <div className="space-y-3">
                <HistogramChart
                  percentiles={bands}
                  ariaLabel="Distribution of comment like counts with percentile bands"
                />
                <div className="flex flex-wrap items-center gap-2">
                  <AvailabilityBadge availability={bands.availability} />
                  {BAND_ORDER.map((band) => (
                    <Badge key={band} variant="outline">
                      P{band}:{" "}
                      {bands.bands[band] === null || bands.bands[band] === undefined
                        ? "—"
                        : formatNumber(bands.bands[band])}
                    </Badge>
                  ))}
                  <span className="text-xs text-muted-foreground">
                    n = {formatNumber(bands.observed_like_counts.length)}
                  </span>
                </div>
              </div>
            ) : null}
          </ChartCard>

          <ChartCard
            title="Comment velocity"
            description="Comments published per time bucket. Records without a timestamp are counted separately."
          >
            <div className="mb-2 flex items-center justify-between">
              <Select
                value={bucket}
                onValueChange={(v) => setBucket(v as "day" | "hour")}
                items={[
                  { value: "day", label: "Per day" },
                  { value: "hour", label: "Per hour" },
                ]}
              >
                <SelectTrigger size="sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="w-[--anchor-width]">
                  <SelectItem value="day">Per day</SelectItem>
                  <SelectItem value="hour">Per hour</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {velocityQuery.isLoading ? (
              <LoadingState label="Computing velocity…" />
            ) : velocityQuery.isError ? (
              <ErrorState message={(velocityQuery.error as Error).message} />
            ) : velocityQuery.data && velocityQuery.data.length > 0 ? (
              <TimelineChart
                data={velocityQuery.data}
                ariaLabel={`Comment publication timeline by ${bucket}`}
              />
            ) : (
              <EmptyState
                icon={MessageSquare}
                title="No comment timestamps"
                description="Comments have not been collected for this video."
              />
            )}
          </ChartCard>
        </div>
      </section>

      <section aria-label="Comment population">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-medium">
          <MessageSquare className="size-4 text-muted-foreground" aria-hidden />
          Comment population
        </h2>
        {commentsQuery.isLoading ? (
          <LoadingState label="Loading comments…" />
        ) : commentsQuery.isError ? (
          <ErrorState message={(commentsQuery.error as Error).message} retry={() => commentsQuery.refetch()} />
        ) : (
          <DataTable
            columns={columns}
            rows={commentsQuery.data ?? []}
            getRowKey={(c) => c.comment_id}
            initialSortKey="published_at"
            initialSortDirection="desc"
            emptyTitle="No comments collected"
            emptyDescription="Collect the video with comment collection enabled to build this population."
            ariaLabel="Video comments"
          />
        )}
      </section>

      <section aria-label="Comment sampling">
        <h2 className="mb-3 text-sm font-medium">Sample comments</h2>
        <SamplingWorkbench
          entityType="comment"
          populationSize={commentsQuery.data?.length ?? 0}
          mutate={sampleMutation}
        />
      </section>
    </div>
  );
}
