"use client";

import JiraBacklogViewer from "./viewer/JiraBacklogViewer";
import RaidRegisterViewer from "./viewer/RaidRegisterViewer";
import ProjectPlanViewer from "./viewer/ProjectPlanViewer";
import SprintPlanViewer from "./viewer/SprintPlanViewer";
import ResourcePlanViewer from "./viewer/ResourcePlanViewer";
import StakeholderMatrixViewer from "./viewer/StakeholderMatrixViewer";
import RaciMatrixViewer from "./viewer/RaciMatrixViewer";
import DevelopmentOrderViewer from "./viewer/DevelopmentOrderViewer";

type Props = {
  loading: boolean;
  artifact: any;
};

export default function ArtifactViewer({
  loading,
  artifact,
}: Props) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-10">
        Loading...
      </div>
    );
  }

  if (!artifact?.content) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-16 text-center text-zinc-500">
        Artifact not generated yet.
      </div>
    );
  }

  switch (artifact.artifact_type) {
    case "jira_backlog":
      return <JiraBacklogViewer data={artifact.content} />;

    case "raid_register":
      return <RaidRegisterViewer data={artifact.content} />;

    case "project_plan":
      return <ProjectPlanViewer data={artifact.content} />;

    case "sprint_plan":
      return <SprintPlanViewer data={artifact.content} />;

    case "resource_plan":
      return <ResourcePlanViewer data={artifact.content} />;

    case "stakeholder_matrix":
      return <StakeholderMatrixViewer data={artifact.content} />;

    case "raci_matrix":
      return <RaciMatrixViewer data={artifact.content} />;

    case "development_order":
      return <DevelopmentOrderViewer data={artifact.content} />;

    default:
      return (
        <pre className="rounded-xl border border-white/10 bg-zinc-950 p-5 text-sm">
          {JSON.stringify(artifact.content, null, 2)}
        </pre>
      );
  }
}