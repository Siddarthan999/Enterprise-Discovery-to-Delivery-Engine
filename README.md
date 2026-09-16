# Enterprise Discovery-to-Delivery Engine

Transform scattered enterprise knowledge into validated solutioning, proposals, and Statements of Work (SOWs)—in minutes, not days.

## Demo

<video src="./Demo.mp4" controls>
  Your browser does not support embedded video. <a href="./Demo.mp4">Download the demo video</a>.
</video>

## Architecture

### The Intelligence Layer — Big Picture

<img width="1585" height="676" alt="The Intelligence Layer (Big Picture)" src="https://github.com/user-attachments/assets/8770fd24-e545-4d03-9de8-c122545deec4" />

### The Intelligence Layer — Under the Hood

<img width="1151" height="722" alt="The Intelligence Layer (Under The Hood)" src="https://github.com/user-attachments/assets/22b568fd-2693-43df-98b5-c706584cae3d" />

## The Problem

### Current Enterprise Workflow Is Broken

- Manual proposal and SOW creation
- Knowledge scattered across systems
- Repetitive documentation
- Missing requirements
- Inconsistent deliverables
- Slow project kickoff

## Our Solution

### AI-Powered Proposal & SOW Generation

Enterprise-ready SOWs from approved templates and organizational knowledge.

### AI Validation & Approval

Coverage · GRC · Risk · Feasibility · Confidence Score · Approval Workflow

### Three Pillars of Intelligent Delivery

#### Enterprise Intelligence

Knowledge Graph · Enterprise Copilot · MCP Automation

## Technology Stack

| Area | Technologies |
| --- | --- |
| Frontend | Next.js · React · TypeScript · Tailwind CSS |
| Backend | FastAPI · Python |
| AI & LLMs | Ollama (Qwen 2.5:7B) · Gemini 2.5 · Multi-Agent Review Pipeline |
| Infrastructure | Docker · Docker Compose |
| Data layer | PostgreSQL + pgvector · Neo4j Knowledge Graph |
| Enterprise integration | Jira REST API · MCP-ready Architecture |
| Knowledge & retrieval | Hybrid Search (Semantic + Keyword) · Sentence Transformers (`all-MiniLM-L6-v2`) |

## What We Deliver

| Impact | Outcome |
| --- | --- |
| **Minutes, Not Days** | From scattered conversations to validated solutioning and SOWs—in minutes. |
| **Reusable Knowledge** | Enterprise knowledge becomes a reusable organizational asset. |
| **AI-Generated & Reviewed** | Every SOW is AI-generated, AI-reviewed, and enterprise-aware. |
| **Risks Identified Early** | Governance gaps and risks are surfaced before delivery begins. |
| **Zero Manual Overhead** | From enterprise knowledge to enterprise execution—automatically. |
| **Trusted AI Consulting** | Redefining enterprise consulting with trusted AI. |

## Run the Application

### Build

```bash
docker compose up --build
```

### Stop

```bash
docker compose down
```

### Start

```bash
docker compose up --d
```

### Service URLs

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| Backend API docs | `http://localhost:8000/docs#/` |
| Neo4j | `http://localhost:7474` |

### Frontend

Restart the frontend:

```bash
docker compose restart frontend
```

### Backend

View backend logs:

```bash
docker compose logs -f backend
```

### Neo4j

Connection protocol: `neo4j://`

#### Login

```text
neo4j
password
```

#### Delete All Nodes

```cypher
MATCH (n)
DETACH DELETE n;
```

### PostgreSQL

Open a PostgreSQL shell:

```bash
docker exec -it enterprisediscovery-to-deliveryengine-postgres-1 psql -U postgres -d enterprise
```

List all rows in a table:

```sql
SELECT * FROM sow_documents;
```

Delete the existing database data:

```sql
DELETE FROM document_chunks;
DELETE FROM documents;
TRUNCATE TABLE proposal_versions, proposal_documents RESTART IDENTITY;
```

### Ollama

If the GPU layer causes issues and Ollama is not running:

```bash
set OLLAMA_NO_GPU=1
```

Install the models:

```bash
ollama pull  qwen2.5:7b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b
```

Run the models:

```bash
ollama run qwen2.5:7b
ollama run qwen2.5-coder:3b
ollama run qwen2.5-coder:7b
```
