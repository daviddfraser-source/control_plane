/**
 * Dependency graph analysis: cycle detection and node state resolution.
 * Migrated from app/src/ui/dependencyGraph.ts for Next.js template library.
 */

export interface DependencyEdge {
  from: string;
  to: string;
}

export interface GraphNodeState {
  id: string;
  blocked: boolean;
  cyclic: boolean;
}

export function detectCycles(edges: DependencyEdge[]): string[][] {
  const graph = new Map<string, string[]>();
  const cycles: string[][] = [];
  const visited = new Set<string>();
  const stack = new Set<string>();
  const path: string[] = [];

  for (const edge of edges) {
    graph.set(edge.from, [...(graph.get(edge.from) || []), edge.to]);
    if (!graph.has(edge.to)) {
      graph.set(edge.to, []);
    }
  }

  function dfs(node: string): void {
    visited.add(node);
    stack.add(node);
    path.push(node);

    for (const next of graph.get(node) || []) {
      if (!visited.has(next)) {
        dfs(next);
      } else if (stack.has(next)) {
        const idx = path.indexOf(next);
        if (idx >= 0) {
          cycles.push([...path.slice(idx), next]);
        }
      }
    }

    path.pop();
    stack.delete(node);
  }

  for (const node of graph.keys()) {
    if (!visited.has(node)) {
      dfs(node);
    }
  }

  return cycles;
}

export function buildGraphNodeState(
  nodes: string[],
  blockedNodes: string[],
  cyclePaths: string[][],
): GraphNodeState[] {
  const blockedSet = new Set(blockedNodes);
  const cycleSet = new Set(cyclePaths.flat());
  return nodes.map((id) => ({
    id,
    blocked: blockedSet.has(id),
    cyclic: cycleSet.has(id),
  }));
}

export function resolvePacketNavigation(packetId: string): string {
  return `/packets/${packetId}`;
}
