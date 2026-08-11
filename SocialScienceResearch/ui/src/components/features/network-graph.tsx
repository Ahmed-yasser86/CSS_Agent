"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import { LoadingState } from "@/components/features/state";
import { CHART_VARS, resolveChartColors } from "@/lib/colors";
import { useTheme } from "@/lib/theme";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => <LoadingState label="Rendering network…" />,
});

export interface NetworkNode {
  id: string;
  title?: string | null;
  kind: "source" | "target" | "both" | "other";
  value?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
  runId?: string | null;
  position?: number | null;
}

const NODE_COLORS: Record<NetworkNode["kind"], string> = {
  source: CHART_VARS.ink,
  target: CHART_VARS.dim,
  both: CHART_VARS.ink,
  other: CHART_VARS.faint,
};

export function NetworkGraph({
  nodes,
  links,
  height = 480,
  onNodeClick,
}: {
  nodes: NetworkNode[];
  links: NetworkLink[];
  height?: number;
  onNodeClick?: (id: string) => void;
}) {
  const { theme } = useTheme();
  // eslint-disable-next-line react-hooks/exhaustive-deps -- theme intentionally forces a canvas recolor on toggle
  const canvasColors = useMemo(() => resolveChartColors(), [theme]);
  const graphData = useMemo(
    () => ({
      nodes: nodes.map((n) => ({
        id: n.id,
        title: n.title ?? n.id,
        val: n.value ?? 1,
      })),
      links: links.map((l) => ({
        source: l.source,
        target: l.target,
      })),
    }),
    [nodes, links],
  );

  return (
    <div>
      <div
        className="w-full overflow-hidden rounded-md border bg-muted/30"
        style={{ height }}
      >
        {nodes.length > 0 ? (
          <ForceGraph2D
            graphData={graphData}
            backgroundColor="transparent"
            nodeRelSize={5}
            // The force-graph typings model nodes loosely; accessors use any.
            nodeVal={(d: unknown) => (d as { val?: number }).val ?? 1}
            nodeColor={(d: unknown) => {
              const id = (d as { id?: string }).id;
              const match = id ? nodes.find((n) => n.id === id) : undefined;
              const kind = match ? match.kind : "other";
              const map: Record<NetworkNode["kind"], string> = {
                source: canvasColors.ink,
                target: canvasColors.dim,
                both: canvasColors.ink,
                other: canvasColors.faint,
              };
              return map[kind];
            }}
            nodeLabel={(d: unknown) => {
              const node = d as { title?: string; id?: string };
              return node.title ?? node.id ?? "video";
            }}
            linkColor={() => canvasColors.link}
            linkWidth={1.2}
            cooldownTicks={120}
            onNodeClick={(d: unknown) => {
              const id = (d as { id?: string }).id;
              if (id) onNodeClick?.(id);
            }}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            No network to render
          </div>
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
        <LegendItem color={NODE_COLORS.source} label="Focus video" />
        <LegendItem color={NODE_COLORS.target} label="Connected video" />
        <LegendItem color={NODE_COLORS.other} label="Other" />
        <span>Click a node to inspect its ego-network.</span>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        aria-hidden
        className="size-2.5 rounded-full border border-border"
        style={{ background: color }}
      />
      {label}
    </span>
  );
}
