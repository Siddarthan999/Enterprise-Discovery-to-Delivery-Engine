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
  transcript?: string
) =>
  API.post(
    "/sow/export",
    {
      sow,
      format,
      template_id,
      state,
      transcript,
    },
    {
      responseType: "blob",
    }
  );

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