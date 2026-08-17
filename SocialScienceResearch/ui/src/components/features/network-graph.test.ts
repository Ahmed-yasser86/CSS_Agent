import { describe, expect, it } from "vitest";
import { runColorFor, communityColorFor } from "@/components/features/network-graph";

describe("network graph color helpers", () => {
  it("assigns a stable color per run id", () => {
    expect(runColorFor("run_a")).toBe(runColorFor("run_a"));
    expect(runColorFor("run_b")).toBe(runColorFor("run_b"));
  });

  it("different run ids can resolve to distinct colors", () => {
    const seen = new Set(
      Array.from({ length: 20 }, (_, i) => runColorFor(`run_${i}`)),
    );
    expect(seen.size).toBeGreaterThan(1);
  });

  it("assigns a stable community color per community id", () => {
    expect(communityColorFor(0)).toBe(communityColorFor(0));
    expect(communityColorFor(1)).toBe(communityColorFor(1));
    expect(communityColorFor(0)).not.toBe(communityColorFor(1));
  });
});