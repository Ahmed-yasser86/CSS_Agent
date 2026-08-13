import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { ProjectItemDetail } from "@/components/features/datasets/project-item-detail";

export default async function ProjectItemPage({
  params,
}: {
  params: Promise<{ projectId: string; itemId: string }>;
}) {
  const { projectId, itemId } = await params;
  return (
    <div className="space-y-4">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-muted-foreground">
        <Link href="/projects" className="underline-offset-2 hover:underline">
          Projects
        </Link>
        <ChevronRight className="size-3" aria-hidden />
        <Link
          href={`/projects/${projectId}`}
          className="underline-offset-2 hover:underline"
        >
          {projectId}
        </Link>
        <ChevronRight className="size-3" aria-hidden />
        <span className="font-mono">{itemId}</span>
      </nav>
      <ProjectItemDetail projectId={projectId} itemId={itemId} />
    </div>
  );
}