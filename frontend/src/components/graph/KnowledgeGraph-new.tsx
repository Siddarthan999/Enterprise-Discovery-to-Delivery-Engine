"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

type Node = {
  id: string;
  label: string;
  type?: string;
};

type Link = {
  source: string;
  target: string;
  type?: string;
};

export default function KnowledgeGraph({ query }: { query: string }) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);

  const [selected, setSelected] = useState<Node | null>(null);

  // ---------------- FETCH ROOT GRAPH ----------------
  async function fetchGraph() {
    if (!query) return;

    const res = await fetch(
      `http://localhost:8000/api/graph/search?query=${query}`
    );

    const data = await res.json();

    const newNodes: Node[] = [];
    const newLinks: Link[] = [];

    data.forEach((d: any) => {
      const docId = String(d.id);

      newNodes.push({
        id: docId,
        label: d.title,
        type: "document",
      });

      // expand relations
      (d.relations || []).forEach((r: any, i: number) => {
        if (!r.target) return;

        const targetId = `${docId}-rel-${i}`;

        newNodes.push({
          id: targetId,
          label: r.target.name || r.target.title || "entity",
          type: r.type,
        });

        newLinks.push({
          source: docId,
          target: targetId,
          type: r.type,
        });
      });
    });

    setNodes(newNodes);
    setLinks(newLinks);
  }

  // ---------------- EXPAND ON CLICK ----------------
  async function expandNode(nodeId: string) {
    const res = await fetch(
      `http://localhost:8000/api/graph/expand/${nodeId}`
    );

    const data = await res.json();

    const extraNodes: Node[] = [];
    const extraLinks: Link[] = [];

    data.forEach((r: any, i: number) => {
      const targetId = `${nodeId}-exp-${i}`;

      extraNodes.push({
        id: targetId,
        label: r.node.name || r.node.title || "node",
        type: r.relationship,
      });

      extraLinks.push({
        source: nodeId,
        target: targetId,
        type: r.relationship,
      });
    });

    setNodes((prev) => [...prev, ...extraNodes]);
    setLinks((prev) => [...prev, ...extraLinks]);
  }

  // ---------------- INIT ----------------
  useEffect(() => {
    fetchGraph();
  }, [query]);

  // ---------------- D3 RENDER ----------------
  useEffect(() => {
    if (!nodes.length) return;

    const width = 900;
    const height = 600;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const container = svg
      .attr("width", width)
      .attr("height", height)
      .call(
        d3.zoom<SVGSVGElement, unknown>().on("zoom", (event) => {
          containerGroup.attr("transform", event.transform);
        })
      );

    const containerGroup = svg.append("g");

    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        "link",
        d3.forceLink(links as any).id((d: any) => d.id).distance(120)
      )
      .force("charge", d3.forceManyBody().strength(-500))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = containerGroup
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#666");

    const node = containerGroup
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", (d: any) => (d.type === "document" ? 22 : 14))
      .attr("fill", (d: any) =>
        d.type === "document" ? "#4f46e5" : "#22c55e"
      )
      .call(
        d3
          .drag<SVGCircleElement, any>()
          .on("start", dragStart)
          .on("drag", dragged)
          .on("end", dragEnd)
      )
      .on("click", (_, d: any) => {
        setSelected(d);

        // 🚀 expand only documents
        if (d.type === "document") {
          expandNode(d.id);
        }
      });

    const label = containerGroup
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .text((d: any) => d.label?.slice(0, 18))
      .attr("fill", "white")
      .attr("font-size", 10);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);

      label.attr("x", (d: any) => d.x + 10).attr("y", (d: any) => d.y);
    });

    function dragStart(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnd(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }, [nodes, links]);

  return (
    <div className="flex gap-4">
      <svg ref={svgRef} className="border border-zinc-800 rounded-xl" />

      <div className="w-80 p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
        <h2 className="font-semibold mb-3">Inspector</h2>

        {selected ? (
          <div className="text-sm space-y-2">
            <div>ID: {selected.id}</div>
            <div>Type: {selected.type}</div>
            <div>Label: {selected.label}</div>
          </div>
        ) : (
          <p className="text-zinc-500">Click nodes to explore graph</p>
        )}
      </div>
    </div>
  );
}