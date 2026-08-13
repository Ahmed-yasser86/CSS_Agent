import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { ProjectDetail } from "@/components/features/datasets/project-detail";

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <div className="space-y-4">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-muted-foreground">
        <Link href="/projects" className="underline-offset-2 hover:underline">
          Projects
        </Link>
        <ChevronRight className="size-3" aria-hidden />
        <span className="font-mono">{projectId}</span>
      </nav>
      <ProjectDetail projectId={projectId} />
    </div>
  );
}