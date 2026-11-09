"""Execute characteristic configuration failures through the actual CLI."""

from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Demonstrate every configuration field without modifying user files."""
    template = (ROOT / "configs/nuget.xml").read_text()
    cases = [("package", "Microsoft.Extensions.Logging", "bad/name"),
             ("repository", "https://api.nuget.org/v3/index.json", "bad"),
             ("test_mode", "false", "yes"),
             ("version", "8.0.0", "banana"),
             ("output", "logging.png", "missing/graph.png"),
             ("ascii", "true", "yes")]
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bad.xml"
        for field, old, new in cases:
            path.write_text(template.replace(old, new))
            result = subprocess.run([sys.executable, "-m", "src.main",
                                     str(path), "--stage", "1"],
                                    cwd=ROOT, capture_output=True, text=True)
            print(f"{field}: exit={result.returncode}")
            print(result.stderr.strip())
        path.write_text("<config>")
        result = subprocess.run([sys.executable, "-m", "src.main", str(path)],
                                cwd=ROOT, capture_output=True, text=True)
        print(f"malformed XML: exit={result.returncode}")
        print(result.stderr.strip())


if __name__ == "__main__":
    main()
