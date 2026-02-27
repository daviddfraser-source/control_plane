/**
 * Tree structure builder for hierarchical WBS packet display.
 * Migrated from app/src/ui/wbsTreeGrid.ts for Next.js template library.
 */

import type { WbsPacketRow } from "./types";

export interface TreeNode {
  id: string;
  children: TreeNode[];
}

export function buildTree(rows: WbsPacketRow[]): TreeNode[] {
  const nodes = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];

  for (const row of rows) {
    nodes.set(row.id, { id: row.id, children: [] });
  }

  for (const row of rows) {
    const node = nodes.get(row.id)!;
    if (!row.parentId) {
      roots.push(node);
      continue;
    }
    const parent = nodes.get(row.parentId);
    if (parent) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}
