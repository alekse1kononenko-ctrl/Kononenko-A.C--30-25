"""Verify diagram semantics rather than the external renderer's layout."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.graph import Graph
from src.visualize import ascii_tree, mermaid, render_png


class VisualizationTests(unittest.TestCase):
    """Preserve directions, repeated nodes, cycles and isolated roots."""

    def test_mermaid_edges(self):
        """A cycle retains both arrows and each node is declared once."""
        a, b = ("A", "1"), ("B", "1")
        text = mermaid(Graph({a: [b], b: [a]}, [a, b]))
        self.assertEqual(text.count('["'), 2)
        self.assertIn("n0 --> n1", text)
        self.assertIn("n1 --> n0", text)

    def test_tree_cycle(self):
        """A back edge prints a cycle marker and stops expanding."""
        a, b = ("A", "1"), ("B", "1")
        text = ascii_tree(Graph({a: [b], b: [a]}, [a, b]), a)
        self.assertIn("A@1 [cycle]", text)
        self.assertEqual(len(text.splitlines()), 3)

    def test_tree_shared(self):
        """A diamond prints a shared marker instead of repeating a subtree."""
        a, b, c, d = [(name, "1") for name in "ABCD"]
        graph = Graph({a: [b, c], b: [d], c: [d], d: []}, [a, b, c, d])
        text = ascii_tree(graph, a)
        self.assertIn("D@1 [shared]", text)
        self.assertNotIn("[cycle]", text)

    def test_isolated(self):
        """An isolated node has a Mermaid declaration and one tree line."""
        a = ("A", "1")
        graph = Graph({a: []}, [a])
        self.assertIn('n0["A@1"]', mermaid(graph))
        self.assertEqual(ascii_tree(graph, a), "A@1")

    def test_missing_renderer(self):
        """Missing renderer produces an actionable error."""
        with patch.dict("os.environ", {"MMDC": ""}):
            with patch("shutil.which", return_value=None):
                with self.assertRaisesRegex(ValueError, "Mermaid CLI missing"):
                    render_png(Path("a.mmd"), Path("a.png"))
