import type { Metadata } from "next";
import { FlaskConical } from "lucide-react";
import { SampleLibrary } from "@/components/features/samples/sample-library";

export const metadata: Metadata = {
  title: "Samples",
};

export default function SamplesPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
          <FlaskConical className="size-5 text-muted-foreground" aria-hidden />
          Research samples
        </h1>
        <p className="text-sm text-muted-foreground">
          Immutable, reproducible samples preserve a population definition and
          its exact membership. Deletion is the only mutation; overlap analysis
          reports Jaccard similarity across persisted samples.
        </p>
      </header>
      <SampleLibrary />
    </div>
  );
}
