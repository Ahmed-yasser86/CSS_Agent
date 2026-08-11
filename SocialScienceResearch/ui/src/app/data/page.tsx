import type { Metadata } from "next";
import Link from "next/link";
import { Database, FlaskConical } from "lucide-react";
import { CoveragePanel } from "@/components/features/coverage-panel";

export const metadata: Metadata = {
  title: "Data",
};

export default function DataPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight">Data library</h1>
        <p className="text-sm text-muted-foreground">
          Coverage of the collected corpus, saved samples, and datasets.
        </p>
      </header>
      <CoveragePanel />
      <div className="flex flex-wrap gap-3">
        <Link
          href="/samples"
          className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted"
        >
          <FlaskConical className="size-4 text-muted-foreground" aria-hidden />
          Research samples
        </Link>
        <Link
          href="/datasets"
          className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted"
        >
          <Database className="size-4 text-muted-foreground" aria-hidden />
          Datasets
        </Link>
      </div>
    </div>
  );
}
