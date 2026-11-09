"""Independent tests for XML settings."""

from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from src.config import load_config

TEMPLATE = (Path(__file__).parents[1] / "configs/nuget.xml").read_text()


class ConfigTests(unittest.TestCase):
    """Cover each required setting and malformed input."""

    def setUp(self):
        """Create an isolated writable configuration directory."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.xml"

    def load(self, text):
        """Write a configuration and invoke the production loader."""
        self.path.write_text(text)
        return load_config(self.path)

    def test_valid(self):
        """Resolve the output relative to the configuration."""
        result = self.load(TEMPLATE)
        self.assertEqual(result.output.parent, self.path.parent.resolve())
        self.assertTrue(result.ascii)
        self.assertFalse(result.test_mode)

    def test_missing_file(self):
        """A missing XML file raises an operating system error."""
        with self.assertRaises(OSError):
            load_config(self.path)

    def test_malformed(self):
        """Reject malformed XML."""
        with self.assertRaises(ET.ParseError):
            self.load("<config>")

    def test_invalid_values(self):
        """Reject incorrect names, types, URL and output paths."""
        changes = [("true", "yes"), ("8.0.0", "banana"),
                   ("Microsoft.Extensions.Logging", "bad/name"),
                   ("https://api.nuget.org/v3/index.json", "relative"),
                   ("logging.png", "missing/out.png"),
                   ("logging.png", "out.jpg")]
        for old, new in changes:
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.load(TEMPLATE.replace(old, new))

    def test_missing_each_setting(self):
        """Every required XML field must be present."""
        for tag in ("package", "repository", "test_mode", "version",
                    "output", "ascii"):
            root = ET.fromstring(TEMPLATE)
            root.remove(root.find(tag))
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.load(ET.tostring(root, encoding="unicode"))

    def test_unknown_duplicate_and_entities(self):
        """Reject ambiguous settings and entity declarations."""
        for extra in ("<ascii>true</ascii>", "<other>1</other>"):
            with self.assertRaises(ValueError):
                self.load(TEMPLATE.replace("</config>", extra + "</config>"))
        with self.assertRaises(ValueError):
            self.load('<!DOCTYPE config SYSTEM "x">' + TEMPLATE)

    def test_local_file(self):
        """Test mode requires an existing repository file."""
        text = TEMPLATE.replace("false", "true")
        text = text.replace("https://api.nuget.org/v3/index.json", "g.json")
        with self.assertRaises(ValueError):
            self.load(text)
        (self.path.parent / "g.json").write_text("{}")
        self.assertTrue(self.load(text).test_mode)
