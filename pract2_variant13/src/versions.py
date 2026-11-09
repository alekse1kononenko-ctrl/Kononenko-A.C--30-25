"""NuGet numeric versions, prereleases and interval constraints."""

import re

VERSION = re.compile(r"(\d+(?:\.\d+){0,3})(?:-([0-9A-Za-z.-]+))?")
COMPONENTS = 4
MIN_COMPONENTS = 3


def version_key(value):
    """Compare NuGet versions after padding release numbers with zeroes."""
    if not isinstance(value, str):
        raise ValueError("Version must be a string")
    match = VERSION.fullmatch(value.lower())
    if not match:
        raise ValueError(f"Unsupported NuGet version: {value}")
    release = tuple(int(part) for part in match[1].split("."))
    release += (0,) * (COMPONENTS - len(release))
    suffix = match[2]
    prerelease = tuple((0, int(p)) if p.isdigit() else (1, p)
                       for p in suffix.split(".")) if suffix else ()
    return release, suffix is None, prerelease


def normalize(value):
    """Normalize numeric components for flat-container URLs."""
    release, stable, _ = version_key(value)
    numbers = list(release)
    while len(numbers) > MIN_COMPONENTS and numbers[-1] == 0:
        numbers.pop()
    result = ".".join(map(str, numbers))
    return result if stable else result + "-" + value.split("-", 1)[1].lower()


def bounds(expression):
    """Parse exact versions, minimum versions and NuGet intervals."""
    if not expression:
        return "", "", False, False
    if expression.startswith("[") and expression.endswith("]"):
        if "," not in expression:
            exact = expression[1:-1]
            version_key(exact)
            return exact, exact, True, True
    if expression[0] not in "[(":
        version_key(expression)
        return expression, "", True, False
    if expression[-1] not in ")]" or expression.count(",") != 1:
        raise ValueError(f"Invalid version range: {expression}")
    low, high = (part.strip() for part in expression[1:-1].split(","))
    return interval(low, high, expression)


def satisfies(version, expression):
    """Check both ends of an interval, including open and closed bounds."""
    low, high, include_low, include_high = bounds(expression)
    key = version_key(version)
    if low:
        lower = version_key(low)
        if key < lower or (key == lower and not include_low):
            return False
    if high:
        upper = version_key(high)
        if key > upper or (key == upper and not include_high):
            return False
    return True


def choose(versions, expression):
    """Select the lowest matching version; opt into prereleases explicitly."""
    allow_prerelease = "-" in expression
    candidates = [v for v in versions
                  if (allow_prerelease or "-" not in v)
                  and satisfies(v, expression)]
    if not candidates:
        raise ValueError(f"No available version satisfies {expression!r}")
    return min(candidates, key=version_key)


def interval(low, high, expression):
    """Validate endpoints of a NuGet interval."""
    for value in (low, high):
        if value:
            version_key(value)
    if low and high and version_key(low) > version_key(high):
        raise ValueError("Reversed version interval")
    return low, high, expression[0] == "[", expression[-1] == "]"
