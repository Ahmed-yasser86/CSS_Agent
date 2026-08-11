import { CircleCheck, CircleMinus, CircleOff } from "lucide-react";
import type { Availability } from "@/lib/types";
import { availabilityDescription, availabilityLabel } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const ICONS: Record<Availability, React.ComponentType<{ className?: string }>> = {
  available: CircleCheck,
  missing: CircleMinus,
  unsupported: CircleOff,
};

export function AvailabilityBadge({
  availability,
  withLabel = true,
}: {
  availability: Availability;
  withLabel?: boolean;
}) {
  const Icon = ICONS[availability];
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Badge
            variant={
              availability === "available"
                ? "default"
                : availability === "missing"
                  ? "secondary"
                  : "outline"
            }
          />
        }
      >
        <Icon className="size-3" aria-hidden />
        {withLabel ? availabilityLabel[availability] : null}
        <span className="sr-only">{availabilityLabel[availability]}</span>
      </TooltipTrigger>
      <TooltipContent>{availabilityDescription[availability]}</TooltipContent>
    </Tooltip>
  );
}
