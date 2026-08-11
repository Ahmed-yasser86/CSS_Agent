import { Inbox, Loader2, AlertTriangle, HelpCircle, CircleOff } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

export function LoadingState({
  label = "Loading…",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex min-h-40 flex-col items-center justify-center gap-3 text-muted-foreground",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="size-5 animate-spin" aria-hidden />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon: Icon = Inbox,
  className,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex min-h-40 flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center",
        className,
      )}
    >
      <Icon className="size-6 text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium">{title}</p>
      {description ? (
        <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  message,
  detail,
  retry,
}: {
  message: string;
  detail?: string;
  retry?: () => void;
}) {
  return (
    <Alert variant="destructive" className="min-h-40 items-center justify-center">
      <AlertTriangle className="size-4" aria-hidden />
      <AlertTitle>Request failed</AlertTitle>
      <AlertDescription className="flex flex-col gap-2">
        <span>{message}</span>
        {detail ? <code className="text-xs">{detail}</code> : null}
        {retry ? (
          <button
            type="button"
            onClick={retry}
            className="w-fit rounded-md border border-border px-3 py-1 text-xs font-medium outline-none hover:bg-muted focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            Retry
          </button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}

export function UnsupportedState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Alert className="min-h-40 items-center justify-center">
      <CircleOff className="size-4" aria-hidden />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{description}</AlertDescription>
    </Alert>
  );
}

export function PartialState({
  title,
  description,
  icon: Icon = HelpCircle,
}: {
  title: string;
  description: string;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Alert className="min-h-40 items-center justify-center">
      <Icon className="size-4" aria-hidden />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{description}</AlertDescription>
    </Alert>
  );
}
