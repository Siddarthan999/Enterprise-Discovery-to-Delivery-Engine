"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

type Node = {
  id: string;
  title?: string;
  type?: string;
  source?: string;
};

type Link = {
  source: string;
  target: string;
};

export default function KnowledgeGraph({ query }: { query: string }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [selected, setSelected] = useState<Node | null>(null);

  // FETCH GRAPH DATA
  async function fetchGraph() {
    if (!query) return;

    const res = await fetch(
      `http://localhost:8000/api/graph/search?query=${query}`
    );

    const data = await res.json();

    // transform backend response → nodes
    const nodes: Node[] = data.map((d: any) => ({
      id: String(d.id),
      title: d.title,
      type: d.type,
      source: d.source,
    }));

    // simple self-links (can extend later with relationships)
    const links: Link[] = nodes.slice(1).map((n, i) => ({
      source: nodes[0].id,
      target: n.id,
    }));

    setNodes(nodes);
    setLinks(links);
  }

  useEffect(() => {
    fetchGraph();
  }, [query]);

  // D3 RENDER
  useEffect(() => {
    if (!nodes.length) return;

    const width = 900;
    const height = 600;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // container
    const container = svg
      .attr("width", width)
      .attr("height", height)
      .call(
        d3.zoom<SVGSVGElement, unknown>().on("zoom", (event) => {
          containerGroup.attr("transform", event.transform);
        })
      );

    const containerGroup = svg.append("g");

    // FORCE SIMULATION
    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        "link",
        d3
          .forceLink(links as any)
          .id((d: any) => d.id)
          .distance(120)
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // LINKS
    const link = containerGroup
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#555")
      .attr("stroke-width", 1.5);

    // NODES
    const node = containerGroup
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", 18)
      .attr("fill", "#4f46e5")
      .call(
        d3
          .drag<SVGCircleElement, any>()
          .on("start", dragStarted)
          .on("drag", dragged)
          .on("end", dragEnded)
      )
      .on("click", (_, d) => setSelected(d));

    // LABELS
    const label = containerGroup
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .text((d: any) => d.title?.slice(0, 20) || d.id)
      .attr("fill", "white")
      .attr("font-size", 10)
      .attr("dx", 20)
      .attr("dy", 4);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);

      label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
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
  }, [nodes, links]);

  return (
    <div className="flex gap-6">
      {/* GRAPH */}
      <div className="border border-zinc-800 rounded-xl bg-zinc-950 p-2">
        <svg ref={svgRef}></svg>
      </div>

      {/* SIDE PANEL */}
      <div className="w-80 p-4 border border-zinc-800 rounded-xl bg-zinc-900">
        <h2 className="text-lg font-semibold mb-3">Node Inspector</h2>

        {selected ? (
          <div className="space-y-2 text-sm">
            <p><span className="text-zinc-400">ID:</span> {selected.id}</p>
            <p><span className="text-zinc-400">Title:</span> {selected.title}</p>
            <p><span className="text-zinc-400">Type:</span> {selected.type}</p>
            <p><span className="text-zinc-400">Source:</span> {selected.source}</p>
          </div>
        ) : (
          <p className="text-zinc-500 text-sm">
            Click a node to inspect document metadata
          </p>
        )}
      </div>
    </div>
  );
}