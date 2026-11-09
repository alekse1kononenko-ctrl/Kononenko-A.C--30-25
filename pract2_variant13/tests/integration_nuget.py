"""Explicit online checks; excluded from default test_*.py discovery."""

import unittest

from src.graph import breadth_first
from src.nuget import NuGetRepository


class LiveNuGetTests(unittest.TestCase):
    """Check three exact public NuGet package versions over real HTTP."""

    def test_three_packages(self):
        """Validate complete node and edge counts for exact net8.0 groups."""
        cases = [("microsoft.extensions.logging", 6, 7),
                 ("microsoft.extensions.configuration", 3, 3),
                 ("microsoft.extensions.dependencyinjection", 2, 1)]
        for package, nodes, edges in cases:
            with self.subTest(package=package):
                repo = NuGetRepository("https://api.nuget.org/v3/index.json",
                                       "net8.0")
                graph = breadth_first([(package, "8.0.0")], repo.dependencies)
                self.assertEqual(len(graph.edges), nodes)
                self.assertEqual(sum(map(len, graph.edges.values())), edges)
