"""Explicit, deliberately limited .NET framework group selection."""

import re

NET = re.compile(r"net(\d+)\.0", re.I)
STANDARD = ("netstandard2.1", "netstandard2.0")
MIN_MODERN_NET = 5


def canonical(value):
    """Normalize long nuspec framework names to short TFMs."""
    value = value.lower().replace(",version=v", "").replace(" ", "")
    return value.replace(".netstandard", "netstandard").replace(
        ".netcoreapp", "net")


def validate_target(value):
    """Allow modern .NET major TFMs and netstandard 2.0/2.1 only."""
    target = canonical(value)
    match = NET.fullmatch(target)
    if target in STANDARD:
        return target
    if match and int(match[1]) >= MIN_MODERN_NET:
        return target
    raise ValueError("framework must be net5.0 or newer, or netstandard2.x")


def modern_candidate(indexed, target):
    """Find the nearest earlier supported modern .NET group."""
    major = int(NET.fullmatch(target)[1])
    candidates = [name for name in indexed if NET.fullmatch(name)
                  and MIN_MODERN_NET <= int(NET.fullmatch(name)[1]) <= major]
    if candidates:
        return max(candidates, key=lambda name: int(NET.fullmatch(name)[1]))
    return next((name for name in STANDARD if name in indexed), None)


def fallback(indexed, target):
    """Apply the documented limited compatibility chain."""
    if NET.fullmatch(target):
        return modern_candidate(indexed, target)
    if target == "netstandard2.1" and "netstandard2.0" in indexed:
        return "netstandard2.0"
    return None


def select_group(groups, target):
    """Select a single compatible group, preserving an empty exact group."""
    target = validate_target(target)
    indexed = {canonical(g.get("targetFramework", "")): g for g in groups}
    if len(indexed) != len(groups):
        raise ValueError("Duplicate dependency framework group")
    if target in indexed:
        return indexed[target]
    candidate = fallback(indexed, target)
    if candidate:
        return indexed[candidate]
    if "" in indexed:
        return indexed[""]
    names = list(indexed)
    raise ValueError(f"No supported group for {target}; groups: {names}")
