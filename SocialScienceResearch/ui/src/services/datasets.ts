import { request, toQuery } from "@/services/api";
import type {
  CreateDatasetInput,
  CreateProjectInput,
  Dataset,
  DatasetDeleteResult,
  DatasetEntityType,
  DatasetExportFormat,
  DatasetQuality,
  Paginated,
  ProjectDeleteResult,
  ResearchProject,
  UpdateProjectInput,
} from "@/lib/dataset-types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "/api/v1/social-science";

export function getProjects(
  cursor?: string,
): Promise<Paginated<ResearchProject>> {
  return request(`/projects${toQuery({ cursor })}`);
}

export function getProject(projectId: string): Promise<ResearchProject> {
  return request(`/projects/${projectId}`);
}

export function createProject(
  body: CreateProjectInput,
): Promise<ResearchProject> {
  return request("/projects", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateProject(
  projectId: string,
  patch: UpdateProjectInput,
): Promise<ResearchProject> {
  return request(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteProject(
  projectId: string,
): Promise<ProjectDeleteResult> {
  return request(`/projects/${projectId}`, { method: "DELETE" });
}

export function getDatasets(
  cursor?: string,
): Promise<Paginated<Dataset>> {
  return request(`/datasets${toQuery({ cursor })}`);
}

export function getDataset(datasetId: string): Promise<Dataset> {
  return request(`/datasets/${datasetId}`);
}

export function createDataset(body: CreateDatasetInput): Promise<Dataset> {
  return request("/datasets", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function deleteDataset(
  datasetId: string,
): Promise<DatasetDeleteResult> {
  return request(`/datasets/${datasetId}`, { method: "DELETE" });
}

export function getDatasetMembers(
  datasetId: string,
  cursor?: string,
): Promise<Paginated<Record<string, unknown>>> {
  return request(`/datasets/${datasetId}/members${toQuery({ cursor })}`);
}

export function getDatasetQuality(
  datasetId: string,
): Promise<DatasetQuality> {
  return request(`/datasets/${datasetId}/quality`);
}

export function getDatasetExportUrl(
  datasetId: string,
  format: DatasetExportFormat,
): string {
  return `${API_BASE}/datasets/${datasetId}/export${toQuery({ format })}`;
}

export type { DatasetEntityType };