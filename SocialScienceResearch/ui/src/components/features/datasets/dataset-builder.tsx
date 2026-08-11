"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import { getProjects, createDataset } from "@/services/datasets";
import type {
  CreateDatasetInput,
  Dataset,
  DatasetEntityType,
  ResearchProject,
} from "@/lib/dataset-types";
import { ErrorState } from "@/components/features/state";

const ENTITY_TYPE_OPTIONS: { value: DatasetEntityType; label: string }[] = [
  { value: "video", label: "Video" },
  { value: "comment", label: "Comment" },
  { value: "channel", label: "Channel" },
  { value: "recommendation", label: "Recommendation" },
  { value: "author", label: "Author" },
];

const SOURCE_OPTIONS: { value: "project" | "raw"; label: string }[] = [
  { value: "raw", label: "Direct (raw rows)" },
  { value: "project", label: "From project" },
];

export function DatasetBuilder({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: (dataset: Dataset) => void;
}) {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entityType, setEntityType] =
    useState<DatasetEntityType>("video");
  const [sourceMode, setSourceMode] = useState<"project" | "raw">("raw");
  const [projectId, setProjectId] = useState("");
  const [includeRaw, setIncludeRaw] = useState(false);

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => getProjects(),
  });

  const projects = projectsQuery.data?.items ?? [];
  const projectsLoading = projectsQuery.isLoading;

  const create = useMutation({
    mutationFn: () => {
      const body: CreateDatasetInput = {
        name: name.trim(),
        entity_type: entityType,
        include_raw: includeRaw,
      };
      if (description.trim()) body.description = description.trim();
      if (sourceMode === "project" && projectId) body.project_id = projectId;
      return createDataset(body);
    },
    onSuccess: (dataset) => {
      toast({
        title: "Dataset created",
        description: `${dataset.name} · ${dataset.entity_type}`,
      });
      onCreated(dataset);
      reset();
    },
    onError: (error) => {
      toast({
        variant: "destructive",
        title: "Could not create dataset",
        description:
          error instanceof Error ? error.message : "Unknown error",
      });
    },
  });

  function reset() {
    setName("");
    setDescription("");
    setEntityType("video");
    setSourceMode("raw");
    setProjectId("");
    setIncludeRaw(false);
  }

  function handleOpenChange(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim() || create.isPending) return;
    if (sourceMode === "project" && !projectId) {
      toast({
        variant: "destructive",
        title: "Select a project",
        description: "Choose the project the dataset should be built from.",
      });
      return;
    }
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New dataset</DialogTitle>
          <DialogDescription>
            Create an exportable research dataset — either directly from raw
            rows or resolved from an existing project.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <Field label="Name">
            <Input
              id="dataset-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. 2026 comments sample"
              autoComplete="off"
              required
            />
          </Field>

          <Field label="Description">
            <Textarea
              id="dataset-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="What this dataset captures…"
            />
          </Field>

          <Field label="Entity type">
            <Select
              value={entityType}
              onValueChange={(value) =>
                setEntityType((value ?? "video") as DatasetEntityType)
              }
              items={ENTITY_TYPE_OPTIONS}
            >
              <SelectTrigger id="dataset-entity-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="w-[--anchor-width]">
                {ENTITY_TYPE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <Field label="Source">
            <div className="flex flex-wrap gap-2">
              {SOURCE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSourceMode(option.value)}
                  aria-pressed={sourceMode === option.value}
                  className="rounded-md border border-border px-3 py-1 text-xs font-medium outline-none hover:bg-muted focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-pressed:bg-primary aria-pressed:text-primary-foreground"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </Field>

          {sourceMode === "project" ? (
            <Field label="Source project">
              {projectsQuery.isError ? (
                <ErrorState
                  message={
                    projectsQuery.error instanceof Error
                      ? projectsQuery.error.message
                      : "Failed to load projects"
                  }
                  retry={() => projectsQuery.refetch()}
                />
              ) : (
                <Select
                  value={projectId}
                  onValueChange={(value) => setProjectId(value ?? "")}
                  items={projects.map((project) => ({
                    value: project.project_id,
                    label: project.name,
                  }))}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select project…" />
                  </SelectTrigger>
                  <SelectContent className="w-[--anchor-width]">
                    {projects.map((project: ResearchProject) => (
                      <SelectItem
                        key={project.project_id}
                        value={project.project_id}
                      >
                        {project.name}
                      </SelectItem>
                    ))}
                    {!projectsLoading && projects.length === 0 ? (
                      <p className="px-2 py-2 text-xs text-muted-foreground">
                        No projects yet — create one on the Projects page.
                      </p>
                    ) : null}
                  </SelectContent>
                </Select>
              )}
            </Field>
          ) : null}

          <div className="flex items-center gap-2">
            <Checkbox
              id="dataset-include-raw"
              checked={includeRaw}
              onCheckedChange={(value) => setIncludeRaw(value === true)}
            />
            <Label htmlFor="dataset-include-raw">
              Include raw fields alongside projected variables
            </Label>
          </div>

          <DialogFooter showCloseButton>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                  Creating…
                </>
              ) : (
                <>
                  <Plus className="size-4" aria-hidden />
                  Create dataset
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </Label>
      {children}
    </div>
  );
}