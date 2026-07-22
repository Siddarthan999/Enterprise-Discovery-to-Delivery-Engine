import axios from "axios";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

const API = axios.create({
  baseURL: API_BASE,
});

//
// Discovery APIs
//
export const runDiscovery = (
  transcript: string,
  title?: string
) =>
  API.post("/discovery/extract", {
    transcript,
    title,
  }).then((res) => res.data);

//
// SOW APIs
//
export const generateSow = (state: any) =>
  API.post("/sow/generate", {
    state,
  }).then((res) => res.data);

export const exportSow = (
  sow: string,
  format: string,
  template_id?: string,
  state?: any,
  transcript?: string,
  sow_id?: number,
  version?: number
) => API.post( "/sow/export", { sow, format, template_id, state, transcript, sow_id, version },{ responseType: "blob",} );

//
// Template APIs
//
export const getTemplates = () =>
  API.get("/template/list").then(
    (res) => res.data
  );

export const uploadTemplate = (
  formData: FormData
) =>
  API.post("/template/upload", formData).then(
    (res) => res.data
  );

export const deleteTemplate = (id: string) =>
  API.delete(`/template/${id}`).then(
    (res) => res.data
  );

//
// Knowledge Base APIs
//
export const getDocuments = () =>
  API.get("/ingest/documents").then(
    (res) => res.data
  );

export const uploadDocument = (
  formData: FormData
) =>
  API.post("/ingest/document", formData).then(
    (res) => res.data
  );

export const deleteDocument = (id: string) =>
  API.delete(`/ingest/document/${id}`).then(
    (res) => res.data
  );

//
// Historical SOW APIs
//
export const getHistoricalSows = () =>
  API.get("/sow-history/list").then(
    (res) => res.data
  );

export async function getHistoricalSowRisks(id: string | number) {
  const res = await fetch(`${API_BASE}/sow-history/${id}/risks`);

  if (!res.ok) {
    throw new Error("Failed to load risks");
  }

  return res.json();
}

export const uploadHistoricalSow = (
  formData: FormData
) =>
  API.post("/sow-history/upload", formData).then(
    (res) => res.data
  );

export const deleteHistoricalSow = (id: string) =>
  API.delete(`/sow-history/${id}`).then(
    (res) => res.data
  );

//
// Transcript APIs
//
export const uploadTranscript = (
  formData: FormData
) =>
  API.post(
    "/transcript/upload",
    formData
  ).then((res) => res.data);

export const ingestTranscriptText = (
  text: string
) =>
  API.post("/transcript/text", {
    text,
  }).then((res) => res.data);

//
// Search APIs
//
export const searchDocuments = (
  query: string
) =>
  API.get("/search", {
    params: { query },
  }).then((res) => res.data);

export default API;

//
// Authors APIs
//
export async function getAuthors() {
  const res = await fetch(`${API_BASE}/authors`);

  if (!res.ok) {
    throw new Error("Failed to load authors");
  }

  return res.json();
}

export async function addAuthor(name: string) {
  const res = await fetch(`${API_BASE}/authors`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });

  if (!res.ok) {
    throw new Error("Failed to add author");
  }

  return res.json();
}

export async function deleteAuthor(id: number) {
  const res = await fetch(`${API_BASE}/authors/${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    throw new Error("Failed to delete author");
  }

  return res.json();
}

//
// Approval APIs
//
export const getApprovalSows = () =>
  API.get("/approval/sows").then((res) => res.data);

export const getApprovalSow = (id: number) =>
  API.get(`/approval/sows/${id}`).then((res) => res.data);

export const getApprovalComments = (id: number) =>
  API.get(`/approval/sows/${id}/comments`).then((res) => res.data);

export const addApprovalComment = (payload: any) =>
  API.post("/approval/comment", payload).then((res) => res.data);

export const approveSow = (payload: any) =>
  API.post("/approval/approve", payload).then((res) => res.data);

export const requestChanges=(payload:any)=>
  API.post("/approval/request-changes", payload).then(res=>res.data);

export const getVersions = (id:number)=>
    API.get(`/approval/sows/${id}/versions`).then(res=>res.data);

export const getVersion = (id:number, version:number)=>
    API.get(`/approval/sows/${id}/version/${version}`).then(res=>res.data);

export const deleteSow = (id: number) =>
  API.delete(`/approval/sows/${id}`).then((res) => res.data);

export const deleteVersion = (sowId: number, version: number) =>
  API.delete(`/approval/sows/${sowId}/version/${version}`).then((res) => res.data);

export const deleteComment = (id:number, reviewerRole:string)=>
  API.delete(`/approval/comment/${id}`,{ params:{ reviewer_role:reviewerRole }}).then(res=>res.data);

export const updateSowVersion = (payload: any) =>
  API.post("/approval/update-version", payload).then(res => res.data);

export const updateSowTitle = (payload: any) =>
  API.post("/approval/update-title", payload).then(res => res.data);

export const compareVersions = (sowId: number, v1: number, v2: number) =>
  API.get(`/approval/sows/${sowId}/compare/${v1}/${v2}`).then(res => res.data);

export const runVersionReview = (payload: { sow_id: number; version: number; mode?: "current" | "new";}) => 
  API.post("/approval/sows/" + payload.sow_id + "/version/" + payload.version + "/run-review", payload).then((res) => res.data);