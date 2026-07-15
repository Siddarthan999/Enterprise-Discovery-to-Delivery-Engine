"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

type Node = {
  id: string;
  title?: string;
  type?: string;
  source?: string;
  x?: number;
  y?: number;
};

type Link = {
  source: string;
  target: string;
};

const TYPE_COLORS: Record<string, string> = {
  document: "#22d3ee",
  email: "#a78bfa",
  policy: "#f472b6",
  default: "#38bdf8",
};

function colorForType(type?: string) {
  if (!type) return TYPE_COLORS.default;
  return TYPE_COLORS[type.toLowerCase()] || TYPE_COLORS.default;
}

export default function KnowledgeGraph({ query }: { query: string }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [selected, setSelected] = useState<Node | null>(null);
  const [loading, setLoading] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 520 });

  // FETCH GRAPH DATA
  async function fetchGraph() {
    if (!query) return;
    setLoading(true);

    try {
      const res = await fetch(
        `http://localhost:8000/api/graph/search?query=${encodeURIComponent(query)}`
      );

      const data = await res.json();

      const fetchedNodes: Node[] = data.map((d: any) => ({
        id: String(d.id),
        title: d.title,
        type: d.type,
        source: d.source,
      }));

      const fetchedLinks: Link[] = fetchedNodes.slice(1).map((n) => ({
        source: fetchedNodes[0].id,
        target: n.id,
      }));

      setNodes(fetchedNodes);
      setLinks(fetchedLinks);
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchGraph();
  }, [query]);

  // TRACK CONTAINER SIZE — this is what makes the graph fill its parent
  // (a chat modal, a page section, whatever) instead of being stuck at a
  // fixed 900x600 regardless of context.
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) {
        setDimensions({ width, height });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // D3 RENDER
  useEffect(() => {
    if (!nodes.length || !svgRef.current) return;

    const { width, height } = dimensions;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    svg
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    const containerGroup = svg.append("g");

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.4, 2.5])
        .on("zoom", (event) => {
          containerGroup.attr("transform", event.transform);
        })
    );

    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        "link",
        d3
          .forceLink(links as any)
          .id((d: any) => d.id)
          .distance(140)
      )
      .force("charge", d3.forceManyBody().strength(-320))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(40));

    // LINKS
    const link = containerGroup
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#3f3f4680")
      .attr("stroke-width", 1.5);

    // NODE GROUPS (circle + label together, easier to style/hover as one unit)
    const nodeGroup = containerGroup
      .selectAll("g.node")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, any>()
          .on("start", dragStarted)
          .on("drag", dragged)
          .on("end", dragEnded)
      )
      .on("click", (_, d) => setSelected(d));

    nodeGroup
      .append("circle")
      .attr("r", 16)
      .attr("fill", (d: any) => colorForType(d.type))
      .attr("stroke", "#0a0a0f")
      .attr("stroke-width", 2)
      .style("filter", "drop-shadow(0 0 6px rgba(56,189,248,0.35))");

    nodeGroup
      .append("text")
      .text((d: any) => (d.title ? d.title.slice(0, 22) : d.id))
      .attr("fill", "#e4e4e7")
      .attr("font-size", 11)
      .attr("dx", 22)
      .attr("dy", 4)
      .style("pointer-events", "none");

    nodeGroup
      .on("mouseenter", function () {
        d3.select(this).select("circle").attr("r", 20);
      })
      .on("mouseleave", function () {
        d3.select(this).select("circle").attr("r", 16);
      });

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      nodeGroup.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    function dragStarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [nodes, links, dimensions]);

  return (
    <div ref={containerRef} className="relative h-full w-full min-h-[420px]">
      <svg ref={svgRef} className="h-full w-full" />

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-950/40">
          <p className="text-sm text-zinc-500">Loading graph…</p>
        </div>
      )}

      {!loading && nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-sm text-zinc-500">
            No related nodes found for this document.
          </p>
        </div>
      )}

      {/* SIDE PANEL — floats over the graph instead of squeezing it into
          a narrower column, so the graph keeps the full canvas width. */}
      {selected && (
        <div className="absolute right-4 top-4 w-72 rounded-xl border border-zinc-800 bg-zinc-900/95 p-4 shadow-xl shadow-black/30 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200">
              Node Inspector
            </h2>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-zinc-500 hover:text-zinc-300"
            >
              ✕
            </button>
          </div>

          <div className="mt-3 space-y-2 text-xs">
            <p>
              <span className="text-zinc-500">ID: </span>
              <span className="text-zinc-300">{selected.id}</span>
            </p>
            <p>
              <span className="text-zinc-500">Title: </span>
              <span className="text-zinc-300">{selected.title || "—"}</span>
            </p>
            <p>
              <span className="text-zinc-500">Type: </span>
              <span className="text-zinc-300">{selected.type || "—"}</span>
            </p>
            <p>
              <span className="text-zinc-500">Source: </span>
              <span className="text-zinc-300">{selected.source || "—"}</span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}