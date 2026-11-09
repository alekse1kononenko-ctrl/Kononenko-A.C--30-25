"""Offline HTTP fixtures and NuGet dependency extraction tests."""

import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.nuget import NuGetRepository, fetch, manifest
from src.versions import choose, normalize, satisfies, version_key
from src.frameworks import select_group
import xml.etree.ElementTree as ET

INDEX = b'{"resources":[{"@type":"PackageBaseAddress/3.0.0",' \
        b'"@id":"https://example.org/flat/"}]}'
NUSPEC = b'''<package xmlns="urn:nuget-test">
<metadata><id>Root</id><version>2.0.0</version><dependencies>
<group targetFramework="net8.0"><dependency id="Child" version="[1,2)"/>
</group><group targetFramework="net48"><dependency id="Wrong" version="1"/>
</group></dependencies></metadata></package>'''


def reader(url):
    """Serve deterministic V3 responses without network access."""
    if url.endswith("v3.json"):
        return INDEX
    if url.endswith("root/index.json"):
        return b'{"versions":["1.0.0","2.0.0"]}'
    if url.endswith("child/index.json"):
        return b'{"versions":["1.1.0","1.0.0","2.0.0"]}'
    if url.endswith("root.nuspec"):
        return NUSPEC
    raise ValueError("Unexpected URL: " + url)


class NuGetTests(unittest.TestCase):
    """Check exact versions, TFM isolation, intervals and server failures."""

    def test_exact_manifest(self):
        """Use the requested version and only the selected TFM group."""
        repo = NuGetRepository("https://example.org/v3.json", "net8.0", reader)
        self.assertEqual(repo.dependencies(("Root", "2.0.0")),
                         [("child", "1.0.0")])
        with self.assertRaises(ValueError):
            repo.dependencies(("Root", "9.0.0"))

    def test_ranges(self):
        """Distinguish exact, inclusive, exclusive and minimum versions."""
        cases = [("[1]", "1.0.0"), ("(1,2)", "1.1.0"),
                 ("[1,2)", "1.0.0"), ("(,1]", "1.0.0"),
                 ("1.1", "1.1.0")]
        for expression, expected in cases:
            with self.subTest(expression=expression):
                self.assertEqual(choose(["2.0.0", "1.1.0", "1.0.0"],
                                        expression), expected)
        self.assertFalse(satisfies("2.0", "[1,2)"))
        with self.assertRaises(ValueError):
            choose(["1.0"], "(1.0)")

    def test_prerelease(self):
        """Prereleases are opt-in and numeric labels compare numerically."""
        self.assertLess(version_key("1.0-rc.2"), version_key("1.0-rc.10"))
        self.assertEqual(choose(["1.0-beta", "1.0"], "1.0-beta"),
                         "1.0-beta")
        self.assertEqual(normalize("01.0.0.0"), "1.0.0")
        with self.assertRaises(ValueError):
            choose(["1.0-beta"], "")

    def test_framework_fallback(self):
        """Prefer exact or compatible framework; reject incompatible groups."""
        root = ET.fromstring('<x><group targetFramework="netstandard2.0"/>'
                             '<group targetFramework="net6.0"/></x>')
        self.assertEqual(select_group(list(root), "net8.0").get(
            "targetFramework"), "net6.0")
        with self.assertRaises(ValueError):
            select_group(list(root), "net48")

    def test_empty_exact_group(self):
        """An empty exact group must not fall back to another group."""
        data = NUSPEC.replace(b'<dependency id="Child" version="[1,2)"/>', b'')
        repo = NuGetRepository("https://example.org/v3.json", "net8.0", reader)
        self.assertEqual(repo.read_dependencies(manifest(data)), [])

    def test_network_failure(self):
        """Convert transport errors into a user-facing diagnostic."""
        with patch("src.nuget.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(ValueError, "Network error"):
                fetch("https://example.org/index.json")

    def test_invalid_metadata(self):
        """Reject missing service resources, malformed JSON and nuspec."""
        for data in (b'{}', b'[]', b'no json',
                     b'{"resources":[1]}', b'{"resources":{}}'):
            with self.assertRaises(ValueError):
                NuGetRepository("https://example.org", "net8.0",
                                lambda url: data)
        with self.assertRaises(ValueError):
            manifest(b'<other/>')
        with self.assertRaises(ET.ParseError):
            manifest(b'<package>')


class ManifestFailureTests(unittest.TestCase):
    """Check malformed server responses and missing packages explicitly."""

    def test_http_not_found(self):
        """Preserve a useful HTTP status for an unavailable package."""
        from urllib.error import HTTPError
        error = HTTPError("https://example.org", 404, "Not found", {}, None)
        with patch("src.nuget.urlopen", side_effect=error):
            with self.assertRaisesRegex(ValueError, "HTTP 404"):
                fetch("https://example.org/index.json")

    def test_wrong_manifest_identity(self):
        """Reject a different ID or version returned by the server."""
        for old, new in [(b"<id>Root</id>", b"<id>Wrong</id>"),
                         (b"<version>2.0.0", b"<version>1.0.0")]:
            def changed(url):
                """Alter only the real manifest fixture response."""
                return reader(url).replace(old, new)
            repo = NuGetRepository("https://example.org/v3.json", "net8.0",
                                   changed)
            with self.assertRaises(ValueError):
                repo.dependencies(("Root", "2.0.0"))

    def test_invalid_version_response(self):
        """Reject a malformed versions array."""
        def changed(url):
            """Return a non-string version without contacting a network."""
            return b'{"versions":[1]}' if url.endswith("index.json") \
                else INDEX
        repo = NuGetRepository("https://example.org/v3.json", "net8.0",
                               changed)
        with self.assertRaises(ValueError):
            repo.versions("Root")
