import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { ChannelWorkspace } from "@/components/features/channel-workspace";

const TABS = ["overview", "videos", "sampling"] as const;

export default async function ChannelPage({
  params,
  searchParams,
}: {
  params: Promise<{ channelId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { channelId } = await params;
  const sp = await searchParams;
  const rawTab = typeof sp.tab === "string" ? sp.tab : "overview";
  const tab = (TABS as readonly string[]).includes(rawTab) ? rawTab : "overview";

  return (
    <div className="space-y-4">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-muted-foreground">
        <Link href="/" className="underline-offset-2 hover:underline">
          Workspace
        </Link>
        <ChevronRight className="size-3" aria-hidden />
        <span className="font-mono">{channelId}</span>
      </nav>
      <ChannelWorkspace
        channelId={channelId}
        initialTab={tab as "overview" | "videos" | "sampling"}
        searchParams={sp}
      />
    </div>
  );
}
