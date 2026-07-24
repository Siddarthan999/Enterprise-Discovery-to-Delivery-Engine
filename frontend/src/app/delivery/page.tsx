"use client";

import { useEffect, useState } from "react";

import AppNav from "@/components/layout/AppNav";

import DeliveryHeader from "@/components/delivery/DeliveryHeader";
import SowList from "@/components/approval/SowList";
import ArtifactCards from "@/components/delivery/ArtifactCards";
import ArtifactViewer from "@/components/delivery/ArtifactViewer";

import { getApprovalSows, getDeliveryArtifacts, getDeliveryArtifact, generateDeliveryArtifact, generateAllDeliveryArtifacts, pushToJira } from "@/lib/api";

export default function DeliveryPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);

  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [artifactContent, setArtifactContent] = useState<any>(null);

  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingArtifact, setLoadingArtifact] = useState(false);

  const [generating, setGenerating] = useState<string | null>(null);
  const [generatingAll, setGeneratingAll] = useState(false);

  const [publishing, setPublishing] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject != null) {
      loadArtifacts(selectedProject);
    }
  }, [selectedProject]);

  async function loadProjects() {
    setLoadingProjects(true);

    try {
      const data = await getApprovalSows();

      const approved = data.filter(
        (s: any) => s.status === "Approved"
      );

      setProjects(approved);

      if (approved.length) {
        setSelectedProject(approved[0].id);
      }
    } finally {
      setLoadingProjects(false);
    }
  }

  async function loadArtifacts(sowId: number) {
    const data = await getDeliveryArtifacts(sowId);

    setArtifacts(data);

    if (!data.length) {
      setSelectedArtifact(null);
      setArtifactContent(null);
      return;
    }

    const first = data[0].artifact_type;

    setSelectedArtifact(first);

    await loadArtifact(sowId, first);
  }

  async function loadArtifact(
    sowId: number,
    artifactType: string
  ) {
    setLoadingArtifact(true);

    try {
      const data = await getDeliveryArtifact(
        sowId,
        artifactType
      );

      setArtifactContent(data);
    } finally {
      setLoadingArtifact(false);
    }
  }

  async function handleGenerate(
    artifact: string
  ) {
    if (!selectedProject) return;

    try {
      setGenerating(artifact);

      await generateDeliveryArtifact(
        selectedProject,
        artifact
      );

      await loadArtifacts(selectedProject);

      if (selectedArtifact === artifact) {
        await loadArtifact(
          selectedProject,
          artifact
        );
      }
    } finally {
      setGenerating(null);
    }
  }

  async function handleGenerateAll() {
    if (!selectedProject) return;

    try {
      setGeneratingAll(true);

      await generateAllDeliveryArtifacts(
        selectedProject
      );

      await loadArtifacts(selectedProject);

      if (selectedArtifact) {
        await loadArtifact(
          selectedProject,
          selectedArtifact
        );
      }
    } finally {
      setGeneratingAll(false);
    }
  }

  async function handlePublishToJira() {
    if (!selectedProject) return;

    try {
      setPublishing("jira_backlog");

      await pushToJira(selectedProject);

      await loadArtifacts(selectedProject);

      await loadArtifact(
        selectedProject,
        "jira_backlog"
      );
    } finally {
      setPublishing(null);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />

      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">

        <DeliveryHeader />

        <div className="mt-6">
          <SowList
            loading={loadingProjects}
            sows={projects}
            selectedId={selectedProject}
            onSelect={setSelectedProject}
          />
        </div>

        <div className="mt-6">
          <ArtifactCards
            artifacts={artifacts}
            selected={selectedArtifact}
            onSelect={async (artifact) => {
              setSelectedArtifact(artifact);

              if (selectedProject) {
                await loadArtifact(
                  selectedProject,
                  artifact
                );
              }
            }}
            onGenerate={handleGenerate}
            onGenerateAll={handleGenerateAll}
            onPublishToJira={handlePublishToJira}
            generating={generating}
            generatingAll={generatingAll}
            publishing={publishing}
          />
        </div>

        <div className="mt-6">
          <ArtifactViewer
            loading={loadingArtifact}
            artifact={artifactContent}
          />
        </div>

      </div>
    </div>
  );
}