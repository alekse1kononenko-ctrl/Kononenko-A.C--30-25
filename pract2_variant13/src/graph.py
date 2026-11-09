"""Recursive breadth-first traversal and dependency graph construction."""

from collections import deque
from dataclasses import dataclass

MAX_DEPTH = 500
MAX_NODES = 10000


@dataclass
class Graph:
    """All outgoing edges and the observed breadth-first visit order."""

    edges: dict
    order: list


def visit_levels(queue, seen, state, depth=0):
    """Recursively drain one FIFO level, then recurse into the next level."""
    if not queue:
        return
    if depth >= MAX_DEPTH:
        raise ValueError("BFS depth limit reached; graph was not truncated")
    neighbors, edges, order = state
    for _ in range(len(queue)):
        node = queue.popleft()
        order.append(node)
        children = list(dict.fromkeys(neighbors(node)))
        edges[node] = children
        for child in children:
            if child not in seen:
                if len(seen) >= MAX_NODES:
                    raise ValueError("BFS node limit reached")
                seen.add(child)
                queue.append(child)
    visit_levels(queue, seen, state, depth + 1)


def breadth_first(roots, neighbors):
    """Return a graph using recursive FIFO levels and one visit per node."""
    roots = list(dict.fromkeys(roots))
    if len(roots) > MAX_NODES:
        raise ValueError("Too many root nodes")
    edges, order = {}, []
    visit_levels(deque(roots), set(roots), (neighbors, edges, order))
    return Graph(edges, order)


def label(node):
    """Format a versioned graph node."""
    return f"{node[0]}@{node[1]}"


def describe(graph):
    """Produce a reproducible plain-text adjacency listing and BFS order."""
    lines = ["BFS: " + " -> ".join(map(label, graph.order))]
    for parent, children in graph.edges.items():
        suffix = ", ".join(map(label, children)) or "(none)"
        lines.append(f"{label(parent)} -> {suffix}")
    return "\n".join(lines)
