"use client";
import { useEffect, useRef } from "react";

interface GraphNode {
  id: string;
  title: string;
  wbs_ref: string;
  status: string;
}

interface GraphEdge {
  from: string;
  to: string;
}

interface DependencyGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightCriticalPath?: boolean;
}

export function DependencyGraph({ nodes, edges, highlightCriticalPath }: DependencyGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !nodes.length) return;

    const svg = svgRef.current;
    const width = svg.clientWidth;
    const height = svg.clientHeight || 500;

    // Clear previous content
    svg.innerHTML = "";

    // Create a simple force-directed graph layout
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    // Calculate positions using a simple circular layout
    const radius = Math.min(width, height) * 0.35;
    const centerX = width / 2;
    const centerY = height / 2;
    const angleStep = (2 * Math.PI) / nodes.length;

    const positions = new Map<string, { x: number; y: number }>();
    nodes.forEach((node, i) => {
      const angle = i * angleStep;
      positions.set(node.id, {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      });
    });

    // Create SVG group for edges
    const edgesGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.appendChild(edgesGroup);

    // Draw edges
    edges.forEach(edge => {
      const fromPos = positions.get(edge.from);
      const toPos = positions.get(edge.to);

      if (!fromPos || !toPos) {
        console.warn(`Edge references missing node: ${edge.from} -> ${edge.to}`);
        return;
      }

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", fromPos.x.toString());
      line.setAttribute("y1", fromPos.y.toString());
      line.setAttribute("x2", toPos.x.toString());
      line.setAttribute("y2", toPos.y.toString());
      line.setAttribute("stroke", "#d1d5db");
      line.setAttribute("stroke-width", "1");
      line.setAttribute("opacity", "0.6");
      edgesGroup.appendChild(line);

      // Add arrow marker
      const dx = toPos.x - fromPos.x;
      const dy = toPos.y - fromPos.y;
      const angle = Math.atan2(dy, dx);
      const arrowLength = 8;
      const arrowX = toPos.x - arrowLength * Math.cos(angle);
      const arrowY = toPos.y - arrowLength * Math.sin(angle);

      const arrow = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
      const points = [
        [toPos.x, toPos.y],
        [arrowX - 4 * Math.sin(angle), arrowY + 4 * Math.cos(angle)],
        [arrowX + 4 * Math.sin(angle), arrowY - 4 * Math.cos(angle)],
      ].map(p => p.join(",")).join(" ");
      arrow.setAttribute("points", points);
      arrow.setAttribute("fill", "#9ca3af");
      edgesGroup.appendChild(arrow);
    });

    // Create SVG group for nodes
    const nodesGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.appendChild(nodesGroup);

    // Draw nodes
    nodes.forEach(node => {
      const pos = positions.get(node.id);
      if (!pos) return;

      // Determine color based on status
      let color = "#9ca3af"; // default gray
      if (node.status === "done") color = "#10b981"; // green
      else if (node.status === "in_progress") color = "#3b82f6"; // blue
      else if (node.status === "failed") color = "#ef4444"; // red
      else if (node.status === "blocked") color = "#f59e0b"; // yellow

      // Node circle
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", pos.x.toString());
      circle.setAttribute("cy", pos.y.toString());
      circle.setAttribute("r", "8");
      circle.setAttribute("fill", color);
      circle.setAttribute("stroke", "#ffffff");
      circle.setAttribute("stroke-width", "2");
      circle.style.cursor = "pointer";

      // Tooltip
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${node.wbs_ref}: ${node.title}\nStatus: ${node.status}`;
      circle.appendChild(title);

      nodesGroup.appendChild(circle);

      // Label
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", pos.x.toString());
      text.setAttribute("y", (pos.y + 20).toString());
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-size", "10");
      text.setAttribute("fill", "currentColor");
      text.textContent = node.wbs_ref;
      nodesGroup.appendChild(text);
    });

  }, [nodes, edges, highlightCriticalPath]);

  if (!nodes.length) {
    return (
      <div className="w-full min-h-[400px] flex items-center justify-center border border-token-border-default rounded-lg bg-token-inset">
        <p className="text-sm text-token-tertiary">No dependency data available</p>
      </div>
    );
  }

  return (
    <svg
      ref={svgRef}
      className="w-full h-[500px] border border-token-border-default rounded-lg bg-token-primary"
      style={{ color: "var(--text-primary)" }}
    />
  );
}
