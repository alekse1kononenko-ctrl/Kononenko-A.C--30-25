"""Explicit, deliberately limited .NET framework group selection."""

import re

NET = re.compile(r"(?:net|\.netcoreapp)(\d+)\.\d+", re.I)
STANDARD = {"netstandard2.1", ".netstandard2.1",
            "netstandard2.0", ".netstandard2.0"}


def canonical(value):
    """Normalize long nuspec framework names to short TFMs."""
    value = value.lower().replace(",version=v", "").replace(" ", "")
    return value.replace(".netstandard", "netstandard").replace(
        ".netcoreapp", "net")


def select_group(groups, target):
    """Select exact TFM, older modern .NET or netstandard; never union."""
    target = canonical(target)
    indexed = {canonical(g.get("targetFramework", "")): g for g in groups}
    if len(indexed) != len(groups):
        raise ValueError("Duplicate dependency framework group")
    if target in indexed:
        return indexed[target]
    match = NET.fullmatch(target)
    if match:
        major = int(match[1])
        candidates = [name for name in indexed if NET.fullmatch(name)
                      and int(NET.fullmatch(name)[1]) <= major]
        if candidates:
            selected = max(candidates, key=lambda n: int(NET.fullmatch(n)[1]))
            return indexed[selected]
        for name in ("netstandard2.1", "netstandard2.0"):
            if name in indexed:
                return indexed[name]
    if target in {"netstandard2.0", "netstandard2.1"}:
        if "netstandard2.0" in indexed:
            return indexed["netstandard2.0"]
    if "" in indexed:
        return indexed[""]
    raise ValueError(f"No supported group for {target}; groups: {list(indexed)}")
