"use client";
import { useState } from "react";
import { StatusBadge } from "./StatusBadge";

interface TreeNode {
  id: string;
  label: string;
  status?: string;
  children?: TreeNode[];
}

interface TreeViewProps {
  nodes: TreeNode[];
  onNodeClick?: (id: string) => void;
}

function TreeItem({ node, depth, onNodeClick }: { node: TreeNode; depth: number; onNodeClick?: (id: string) => void }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <div
        className="flex items-center gap-2 py-1.5 px-2 rounded-[var(--radius-md)] hover:bg-token-inset cursor-pointer text-sm"
        style={{ paddingLeft: `${12 + depth * 20}px` }}
        onClick={() => onNodeClick?.(node.id)}
      >
        <button
          className="w-4 text-xs text-token-tertiary"
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        >
          {hasChildren ? (expanded ? "▾" : "▸") : "·"}
        </button>
        <span className="flex-1 font-medium">{node.label}</span>
        {node.status && <StatusBadge status={node.status} />}
      </div>
      {hasChildren && expanded && node.children!.map(child => (
        <TreeItem key={child.id} node={child} depth={depth + 1} onNodeClick={onNodeClick} />
      ))}
    </div>
  );
}

export function TreeView({ nodes, onNodeClick }: TreeViewProps) {
  return (
    <div className="border border-token-default rounded-[var(--radius-xl)] bg-token-surface p-2">
      {nodes.map(node => <TreeItem key={node.id} node={node} depth={0} onNodeClick={onNodeClick} />)}
    </div>
  );
}
