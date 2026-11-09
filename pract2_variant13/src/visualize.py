"""Generate Mermaid and finite ASCII trees from the constructed graph."""

import os
from pathlib import Path
import shutil
import subprocess

from src.graph import label

MAX_ASCII_LINES = 20000
LABEL_WIDTH = 28
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def diagram_label(node):
    """Wrap long dotted package names while retaining the full identifier."""
    text = label(node)
    if len(text) > LABEL_WIDTH:
        text = node[0].replace(".", ".<br/>") + "<br/>@" + node[1]
    return text.replace('"', "&quot;")


def mermaid(graph):
    """Assign safe unique IDs and preserve all directed edges."""
    identities = {node: f"n{index}" for index, node in enumerate(graph.edges)}
    lines = ["flowchart TD"]
    for node, identity in identities.items():
        text = diagram_label(node)
        lines.append(f'    {identity}["{text}"]')
    for parent, children in graph.edges.items():
        for child in children:
            lines.append(f"    {identities[parent]} --> {identities[child]}")
    return "\n".join(lines) + "\n"


def ascii_tree(graph, root):
    """Use an explicit stack; distinguish active cycles from shared nodes."""
    lines, expanded = [], set()
    stack = [(root, "", "", frozenset())]
    while stack:
        node, prefix, branch, ancestors = stack.pop()
        suffix = ""
        if node in ancestors:
            suffix = " [cycle]"
        elif node in expanded:
            suffix = " [shared]"
        lines.append(prefix + branch + label(node) + suffix)
        if len(lines) > MAX_ASCII_LINES:
            raise ValueError("ASCII tree size limit reached")
        if suffix:
            continue
        expanded.add(node)
        children = graph.edges.get(node, [])
        next_prefix = prefix + ("    " if branch == "`-- " else "|   ")
        if not branch:
            next_prefix = ""
        for index in reversed(range(len(children))):
            marker = "`-- " if index == len(children) - 1 else "+-- "
            stack.append((children[index], next_prefix, marker,
                          ancestors | {node}))
    return "\n".join(lines)


def render_png(source, output):
    """Run only Mermaid's renderer; dependency extraction is already done."""
    executable = os.environ.get("MMDC") or shutil.which("mmdc")
    if not executable:
        raise ValueError("Mermaid CLI missing; install it or set MMDC")
    command = [executable, "-i", str(source), "-o", str(output),
               "-b", "white", "-s", "2"]
    browser_config = os.environ.get("MERMAID_PUPPETEER_CONFIG")
    if browser_config:
        command += ["-p", browser_config]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"Mermaid renderer failed: {error}") from error
    if result.returncode:
        raise ValueError("Mermaid renderer failed: " + result.stderr.strip())
    if not Path(output).is_file():
        raise ValueError("Renderer did not produce an image")
    with Path(output).open("rb") as stream:
        if stream.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            raise ValueError("Renderer output is not a PNG")


def visualize(graph, root, output, tree):
    """Save Mermaid beside the configured PNG and optionally print a tree."""
    source = output.with_suffix(".mmd")
    source.write_text(mermaid(graph), encoding="utf-8")
    if tree:
        print(ascii_tree(graph, root))
    render_png(source, output)
    print(f"Mermaid: {os.path.relpath(source)}")
    print(f"PNG: {os.path.relpath(output)}")
