"""
Deploy code for handling folder and job traversal.
"""

from collections import defaultdict
import Utility
from Utility import print_debug

def build_server_index(config_servers):
    """
    Builds a lookup map keyed by server/host name.
    """
    index = {}

    for server in config_servers:
        name = server.get("name")
        ostype = server.get("OSType", "")

        platform = "MF" if ostype.strip().lower() == "z/os" else "DS"

        if name:
            index[name] = platform

    return index


def is_job(obj):
    """Check if the given object is a Control-M job."""
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("Type"), str)
        and obj["Type"].startswith("Job:")
    )

def walk_folder(
    node,
    path,
    result,
    config_servers,
    inherited=None
):
    """Recursively walk a Control-M folder structure, counting job types and emitting rows."""
    if not isinstance(node, dict):
        return defaultdict(int)

    platforms = build_server_index(config_servers)

    # Inherit metadata downward
    inherited = inherited or {}
    application = node.get("Application", inherited.get("Application"))
    sub_application = node.get("SubApplication", inherited.get("SubApplication"))
    server = node.get("ControlmServer", inherited.get("ControlmServer"))
    platform = platforms[server] if server in platforms else "Unknown"

    local_counts = defaultdict(int)

    # Count direct jobs
    for job in node.get("Jobs", []):
        if is_job(job):
            local_counts[job["Type"]] += 1

    # Recurse into subfolders
    for sub in node.get("SubFolders", []):
        name = sub.get("Name", "<unnamed>")
        child_path = f"{path}/{name}"
        child_counts = walk_folder(
            sub,
            child_path,
            result,
            config_servers,
            {
                "Application": application,
                "SubApplication": sub_application,
                "ControlmServer": server
            }
        )
        for jt, c in child_counts.items():
            local_counts[jt] += c

    # Emit rows for this folder path
    for job_type, count in local_counts.items():
        key = (
            application,
            sub_application,
            server,
            platform,
            path,
            job_type
        )
        result[key] += count

    return local_counts

if __name__ == "__main__":
    print_debug("This file is not meant to be run directly.", Utility.debug)
    assert "You should not see this message" == "This file is not meant to be run directly."
