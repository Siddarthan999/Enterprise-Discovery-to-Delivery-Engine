import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000/api",
});

// ------------------------
// Discovery APIs
// ------------------------
export const runDiscovery = (transcript: string, title?: string) =>
  API.post("/discovery/extract", { transcript, title });

// ------------------------
// SOW APIs
// ------------------------
export const generateSow = () =>
  API.post("/sow/generate");

export const exportSow = (sow: string, format: string) =>
  API.post("/sow/export", { sow, format });

// ------------------------
// Search APIs
// ------------------------
export const searchDocuments = (query: string) =>
  API.get("/search", {
    params: { query },
  }).then((res) => res.data);