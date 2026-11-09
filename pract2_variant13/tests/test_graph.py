"""Validate recursive BFS ordering, cycles and local input."""

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.graph import breadth_first
from src.local import LocalRepository

DATA = Path(__file__).parent / "data"


class GraphTests(unittest.TestCase):
    """Test graph invariants independently from network access."""

    def graph(self, name):
        """Build a fixture graph from root A."""
        repo = LocalRepository(DATA / (name + ".json"))
        return breadth_first([("A", "1.0.0")], repo.dependencies)

    def test_breadth_order(self):
        """Siblings precede grandchildren, distinguishing BFS from DFS."""
        graph = self.graph("acyclic")
        self.assertEqual([n[0] for n in graph.order], list("ABCDE"))

    def test_recursion_is_used(self):
        """Each nonempty frontier triggers a recursive level invocation."""
        from src import graph as module
        with patch.object(module, "visit_levels",
                          wraps=module.visit_levels) as recursive:
            self.graph("acyclic")
            self.assertEqual(recursive.call_count, 4)

    def test_cycle_keeps_edge(self):
        """Visit each node once while retaining the edge closing the cycle."""
        graph = self.graph("cycle")
        self.assertEqual([n[0] for n in graph.order], list("ABCD"))
        self.assertIn(("A", "1.0.0"), graph.edges[("C", "1.0.0")])

    def test_shared_once(self):
        """A diamond keeps both incoming edges but fetches D only once."""
        repo = LocalRepository(DATA / "shared.json")
        calls = Counter()

        def neighbors(node):
            """Count actual dependency fetches."""
            calls[node] += 1
            return repo.dependencies(node)

        graph = breadth_first([("A", "1.0.0")], neighbors)
        self.assertEqual(calls[("D", "1.0.0")], 1)
        for parent in "BC":
            self.assertIn(("D", "1.0.0"), graph.edges[(parent, "1.0.0")])
        self.assertNotIn(("Z", "1.0.0"), graph.edges)

    def test_isolated(self):
        """A root with no outgoing edges remains visible."""
        graph = self.graph("isolated")
        self.assertEqual(graph.edges, {("A", "1.0.0"): []})

    def test_all_vertices(self):
        """A multi-root traversal preserves isolated repository vertices."""
        repo = LocalRepository(DATA / "isolated.json")
        self.assertEqual(len(breadth_first(repo.nodes(),
                                           repo.dependencies).edges), 3)

    def test_wrong_version(self):
        """The local repository also enforces the configured version."""
        repo = LocalRepository(DATA / "shared.json")
        with self.assertRaises(ValueError):
            repo.dependencies(("A", "2.0.0"))

    def test_bad_local_graph(self):
        """Reject lowercase names, missing targets and invalid lists."""
        cases = [{"a": []}, {"A": ["B"]}, {"A": "B"},
                 {"A": ["A", "A"]}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            for packages in cases:
                path.write_text(json.dumps({"version": "1.0.0",
                                            "packages": packages}))
                with self.assertRaises(ValueError):
                    LocalRepository(path)

    def test_depth_limit_is_explicit(self):
        """Never silently return a partial graph on resource exhaustion."""
        with patch("src.graph.MAX_DEPTH", 3):
            with self.assertRaisesRegex(ValueError, "depth limit"):
                breadth_first([0], lambda node: [node + 1])
