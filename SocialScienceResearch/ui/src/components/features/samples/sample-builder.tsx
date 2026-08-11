"use client";

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import { useCreateSample } from "@/services/samples";
import { SAMPLE_ENTITY_OPTIONS, type SampleEntityType } from "@/lib/sample-types";
import type { Sample } from "@/lib/sample-types";

const STRATEGY_OPTIONS = [
  { value: "simple_random", label: "Simple random" },
  { value: "systematic", label: "Systematic" },
  { value: "stratified", label: "Stratified" },
  { value: "cluster", label: "Cluster" },
  { value: "convenience", label: "Convenience" },
];

export function SampleBuilder({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated?: (sample: Sample) => void;
}) {
  const { toast } = useToast();
  const [entityType, setEntityType] = useState<SampleEntityType>("video");
  const [strategy, setStrategy] = useState("simple_random");
  const [seed, setSeed] = useState("");
  const [populationSize, setPopulationSize] = useState("");
  const [memberIds, setMemberIds] = useState("");
  const [criteria, setCriteria] = useState("");
  const [populationQueryHash, setPopulationQueryHash] = useState("");

  const create = useCreateSample();

  function reset() {
    setEntityType("video");
    setStrategy("simple_random");
    setSeed("");
    setPopulationSize("");
    setMemberIds("");
    setCriteria("");
    setPopulationQueryHash("");
  }

  function handleOpenChange(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const ids = memberIds
      .split(/[\s,]+/)
      .map((part) => part.trim())
      .filter(Boolean);
    const population = Number(populationSize);
    if (!population || population < 0) {
      toast({
        variant: "destructive",
        title: "Invalid population size",
        description: "Enter the size of the population the sample was drawn from.",
      });
      return;
    }
    let criteriaJson: Record<string, unknown> | undefined;
    if (criteria.trim()) {
      try {
        criteriaJson = JSON.parse(criteria) as Record<string, unknown>;
      } catch {
        toast({
          variant: "destructive",
          title: "Invalid criteria JSON",
          description: "Criteria must be valid JSON.",
        });
        return;
      }
    }
    create.mutate(
      {
        entity_type: entityType,
        strategy,
        seed: seed === "" ? null : Number(seed),
        population_size: population,
        member_ids: ids,
        criteria_json: criteriaJson,
        population_query_hash: populationQueryHash.trim(),
      },
      {
        onSuccess: (sample) => {
          toast({
            title: "Sample saved",
            description: `${sample.sample_id} · ${sample.sample_size} members`,
          });
          onCreated?.(sample);
          onOpenChange(false);
        },
        onError: (error) => {
          toast({
            variant: "destructive",
            title: "Could not save sample",
            description: error instanceof Error ? error.message : "Unknown error",
          });
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New sample</DialogTitle>
          <DialogDescription>
            Persist an immutable, reproducible sample. Member ids and criteria
            are recorded verbatim so the design can be audited and re-run.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Entity type">
              <Select
                value={entityType}
                onValueChange={(value) =>
                  setEntityType((value ?? "video") as SampleEntityType)
                }
                items={SAMPLE_ENTITY_OPTIONS.map((o) => ({
                  value: o.value,
                  label: o.label,
                }))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SAMPLE_ENTITY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Strategy">
              <Select
                value={strategy}
                onValueChange={(value) => setStrategy(value ?? "simple_random")}
                items={STRATEGY_OPTIONS}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STRATEGY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Seed (optional)">
              <Input
                id="sample-seed"
                type="number"
                value={seed}
                onChange={(event) => setSeed(event.target.value)}
                autoComplete="off"
              />
            </Field>

            <Field label="Population size">
              <Input
                id="sample-population"
                type="number"
                min={0}
                value={populationSize}
                onChange={(event) => setPopulationSize(event.target.value)}
                required
                autoComplete="off"
              />
            </Field>
          </div>

          <Field label="Population query hash (optional)">
            <Input
              id="sample-query-hash"
              value={populationQueryHash}
              onChange={(event) => setPopulationQueryHash(event.target.value)}
              placeholder="sha256 of the population definition"
              autoComplete="off"
            />
          </Field>

          <Field label="Member ids">
            <Textarea
              id="sample-members"
              value={memberIds}
              onChange={(event) => setMemberIds(event.target.value)}
              placeholder="id_1, id_2, id_3 … (space or comma separated)"
              rows={4}
            />
          </Field>

          <Field label="Criteria JSON (optional)">
            <Textarea
              id="sample-criteria"
              value={criteria}
              onChange={(event) => setCriteria(event.target.value)}
              placeholder='{"sample":"video comments"}'
              rows={3}
            />
          </Field>

          <DialogFooter showCloseButton>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                  Saving…
                </>
              ) : (
                <>
                  <Plus className="size-4" aria-hidden />
                  Save sample
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </Label>
      {children}
    </div>
  );
}
