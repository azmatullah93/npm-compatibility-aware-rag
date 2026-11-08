"""Resolve the actual target npm package version from a lockfile when available."""
import re

EXACT=re.compile(r'^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')


def resolve_version(package, package_json, lock_json=None):
    """Avoid silently treating caret/tilde ranges as resolved exact versions.
    Supports package-lock v2/v3 `packages.node_modules/<name>.version` entries.
    """
    if lock_json:
        pkg=lock_json.get('packages',{}).get('node_modules/'+package,{})
        version=pkg.get('version')
        if version:
            if not EXACT.match(version):
                raise ValueError('invalid resolved lockfile version')
            return version
    requested=package_json.get('dependencies',{}).get(package)
    if requested is None:
        requested=package_json.get('devDependencies',{}).get(package)
    if requested is None:
        raise ValueError('package not present in dependency manifest')
    if not EXACT.match(requested):
        raise ValueError('version range cannot be resolved without lockfile')
    return requested
