"""Reverse dependencies must follow incoming edges in BFS order."""

from pathlib import Path
import unittest

from src.local import LocalRepository
from src.reverse import reverse_dependencies

DATA = Path(__file__).parent / "data"


class ReverseTests(unittest.TestCase):
    """Cover branches, diamonds, cycles and isolated targets."""

    def query(self, fixture, target):
        """Query all incoming paths in a complete local repository."""
        repo = LocalRepository(DATA / (fixture + ".json"))
        graph = reverse_dependencies(repo, (target, "1.0.0"), repo.nodes())
        return [node[0] for node in graph.order[1:]]

    def test_shared(self):
        """D is needed by B and C, which are needed by A."""
        self.assertEqual(self.query("shared", "D"), list("BCA"))

    def test_direction(self):
        """An outgoing dependency is not an incoming dependent."""
        self.assertEqual(self.query("acyclic", "B"), ["A"])
        self.assertEqual(self.query("acyclic", "A"), [])

    def test_cycle(self):
        """A cycle terminates without reporting the target as its ancestor."""
        self.assertEqual(self.query("cycle", "A"), list("CB"))

    def test_isolated(self):
        """A declared isolated vertex has no reverse dependencies."""
        self.assertEqual(self.query("isolated", "Z"), [])

    def test_missing(self):
        """An unknown target is an error, not an empty result."""
        with self.assertRaises(ValueError):
            self.query("isolated", "X")
