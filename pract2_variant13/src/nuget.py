"""Retrieve NuGet V3 manifests using standard HTTP and XML modules only."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as element_tree

from src.config import http_url, PACKAGE
from src.frameworks import select_group
from src.versions import choose, normalize

TIMEOUT = 30
MAX_RESPONSE = 8 * 1024 * 1024


def fetch(url):
    """Read a bounded HTTP response and translate network failures."""
    http_url(url)
    request = Request(url, headers={"User-Agent": "NuGetGraph/1.0"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            data = response.read(MAX_RESPONSE + 1)
    except HTTPError as error:
        raise ValueError(f"HTTP {error.code}: {url}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ValueError(f"Network error: {url}: {error}") from error
    if len(data) > MAX_RESPONSE:
        raise ValueError("Server response exceeds size limit")
    return data


def json_object(data):
    """Require a JSON object from the repository."""
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def service_resources(data):
    """Validate the shape of a V3 service index before resource discovery."""
    resources = json_object(data).get("resources")
    if not isinstance(resources, list):
        raise ValueError("Service index resources must be a list")
    if not all(isinstance(resource, dict) for resource in resources):
        raise ValueError("Malformed service resource")
    return resources


def manifest(data):
    """Parse namespace-qualified nuspec XML without entities."""
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("DTD and XML entities are forbidden")
    root = element_tree.fromstring(data)
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    if root.tag != "package" or root.find("metadata") is None:
        raise ValueError("Invalid nuspec metadata")
    return root.find("metadata")


class NuGetRepository:
    """Resolve direct dependencies for a particular package and framework."""

    def __init__(self, url, framework, reader=fetch):
        """Discover the flat-container resource from the configured index."""
        self.reader = reader
        self.framework = framework
        self.version_cache = {}
        self.dependency_cache = {}
        resources = service_resources(reader(url))
        matches = [r.get("@id", "") for r in resources
                   if r.get("@type") == "PackageBaseAddress/3.0.0"]
        if not matches:
            raise ValueError("Service index has no PackageBaseAddress/3.0.0")
        self.base = http_url(matches[0]).rstrip("/") + "/"

    def versions(self, package):
        """Get all versions from this repository, caching repeated requests."""
        if not PACKAGE.fullmatch(package):
            raise ValueError("Invalid dependency package ID")
        key = package.lower()
        if key not in self.version_cache:
            data = json_object(self.reader(self.base + key + "/index.json"))
            values = data.get("versions")
            if not isinstance(values, list) or not values:
                raise ValueError(f"Missing versions for {package}")
            if not all(isinstance(value, str) for value in values):
                raise ValueError("Version list contains a non-string")
            self.version_cache[key] = values
        return self.version_cache[key]

    def resolve(self, package, expression):
        """Select the lowest available version in a dependency interval."""
        return choose(self.versions(package), expression)

    def dependencies(self, node):
        """Fetch the exact requested nuspec and return resolved dependencies."""
        package, version = node
        key = (package.lower(), normalize(version))
        if key in self.dependency_cache:
            return self.dependency_cache[key]
        available = {normalize(v) for v in self.versions(package)}
        if key[1] not in available:
            raise ValueError(f"Version not available: {package}@{version}")
        url = f"{self.base}{key[0]}/{key[1]}/{key[0]}.nuspec"
        metadata = manifest(self.reader(url))
        if metadata.findtext("id", "").lower() != key[0]:
            raise ValueError("Server returned a different package ID")
        if normalize(metadata.findtext("version", "")) != key[1]:
            raise ValueError("Server returned a different package version")
        result = self.read_dependencies(metadata)
        self.dependency_cache[key] = result
        return result

    def read_dependencies(self, metadata):
        """Extract one selected group and resolve its dependency ranges."""
        dependencies = metadata.find("dependencies")
        if dependencies is None:
            return []
        groups = dependencies.findall("group")
        if groups and dependencies.findall("dependency"):
            raise ValueError("Mixed grouped and ungrouped dependencies")
        selected = select_group(groups, self.framework) if groups else None
        elements = dependencies if selected is None else selected
        result = []
        for element in elements:
            package = element.get("id", "")
            if element.tag != "dependency" or not PACKAGE.fullmatch(package):
                raise ValueError("Malformed dependency element")
            version = self.resolve(package, element.get("version", ""))
            result.append((package.lower(), normalize(version)))
        return result
