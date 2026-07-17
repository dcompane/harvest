from collections import defaultdict
from collections.abc import Mapping
from fnmatch import fnmatch
from typing import Any, Dict, Optional, Iterable, Tuple, List



debug = False
isSaaS = False
harvest_version = "v0.1.1"

colors = {
    "blue": "FF1F4E78",
    "red": "FFFF0000",
    "green": "FF00FF00",
    "yellow": "FFFFFF00",
    "orange": "FFFFA500",
    "purple": "FF800080",
    "gray": "FF808080",
    "light_blue": "FFADD8E6",
    "light_red": "FFFFAFAF",
    "light_green": "FF90EE90",
    "light_yellow": "FFFFFFE0",
    "light_orange": "FFFFE5B4",
    "light_purple": "FFE6E6FA",
    "light_gray": "FFD3D3D3",
    }

BSD_3_license = [
    "BSD 3-Clause License",
    " ",
    "Copyright (c) 2026, Daniel Companeetz",
    " ",
    "Redistribution and use in source and binary forms, with or without",
    "modification, are permitted provided that the following conditions are met:",
    " ",
    "1. Redistributions of source code must retain the above copyright notice, this",
    "   list of conditions and the following disclaimer.",
    " ",
    "2. Redistributions in binary form must reproduce the above copyright notice,",
    "   this list of conditions and the following disclaimer in the documentation",
    "   and/or other materials provided with the distribution.",
    " ",
    "3. Neither the name of the copyright holder nor the names of its",
    "   contributors may be used to endorse or promote products derived from",
    "   this software without specific prior written permission.",
    " ",
    "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\"",
    "AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE",
    "IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE",
    "DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE",
    "FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL",
    "DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR",
    "SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER",
    "CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,",
    "OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE",
    "OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.",
    " ",
    "# SPDX-License-Identifier: BSD-3-Clause",
    "# For information on SDPX, https://spdx.org/licenses/BSD-3-Clause.html"
]

# =============================================================================
# Utility
# =============================================================================

def parse_include(val: str):
    """Parse the --include argument into a set of valid options."""
    allowed = {"deploy", "config", "auth", "provision"}
    parts = {p.strip().lower() for p in val.split(",") if p.strip()}
    unknown = parts - allowed
    if unknown:
        raise ValueError(f"Invalid --include value(s): {','.join(unknown)}")
    return parts or allowed

def str_to_bool(value: str) -> bool:
    """Convert a string to a boolean value."""
    return value.strip().lower() == "true"

def print_debug(string: str, de_bug: bool = debug):
    """Print debug information if debug mode is enabled."""
    if de_bug:
        print(string)


def count_key_value_matches(
    obj: Any,
    key_pattern: str,
    value_pattern: str,
    parent_key_pattern: Optional[str] = None
) -> Tuple[int, int]:
    """
    Recursively count occurrences of keys matching `key_pattern`
    whose values match `value_pattern`, and return the deepest level
    at which such a key was found.

    Args:
        obj: The input object (dict, list, or scalar).
        key_pattern: Glob pattern for matching keys.
        value_pattern: Glob pattern for matching string values.
        parent_key_pattern: Optional glob pattern for immediate parent key.

    Returns:
        (count, deepest_level)
        deepest_level will be -1 if no matches are found.
    """

    def _recurse(current: Any, parent_key: Optional[str], depth: int) -> Tuple[int, int]:
        count = 0
        max_depth = -1

        if isinstance(current, dict):
            for k, v in current.items():
                # Check key match
                if fnmatch(str(k), key_pattern):
                    parent_ok = (
                        parent_key_pattern is None
                        or (parent_key is not None and fnmatch(str(parent_key), parent_key_pattern))
                    )

                    if parent_ok and isinstance(v, str) and fnmatch(v, value_pattern):
                        count += 1
                        max_depth = max(max_depth, depth)

                # Recurse deeper
                sub_count, sub_depth = _recurse(v, k, depth + 1)
                count += sub_count
                max_depth = max(max_depth, sub_depth)

        elif isinstance(current, list):
            for item in current:
                sub_count, sub_depth = _recurse(item, parent_key, depth + 1)
                count += sub_count
                max_depth = max(max_depth, sub_depth)

        return int(count), int(max_depth)

    return _recurse(obj, None, 0)

###############################################################################

def extract_key_paths(data, keys):
    """Extracts the values for a sequence of keys from nested dictionaries and lists.
    Args:
        data: The nested data structure (dicts and lists).
        keys: A list of keys to extract from each dictionary.

    Returns:
        A list of dictionaries containing the extracted key-value pairs.
    """
    results = []
    # set()  # use a set for uniqueness

    def walk(node):
        if isinstance(node, dict):
            # Process current node
            first_key = keys[0]
            if first_key in node:
                path = {}
                for key in keys:
                    if key in node:
                        path[key] = node[key]
                    # else:
                    #     break
                results.append(path)  # store as tuple for uniqueness
            # Recurse all values generically
            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    # Convert back to list of lists
    return results

##############################################################################
#HERE

def count_job_combinations(
    data,
    key_order,
    count_key_pattern: Optional[str] = None,
    count_value_pattern: Optional[str] = None,
):
    counts = defaultdict(int)

    def key_match(k):
        return fnmatch(k, count_key_pattern) if count_key_pattern else True

    def val_match(v):
        return fnmatch(str(v), count_value_pattern) if count_value_pattern else True

    def matches_pattern(node):
        """
        Matching rules:
        - No patterns → always match
        - Only key pattern → any key matches
        - Only value pattern → any value matches
        - Both → SAME key/value pair must match
        """
        if not isinstance(node, dict):
            return False

        if not count_key_pattern and not count_value_pattern:
            return True

        for k, v in node.items():
            k_ok = key_match(k)
            v_ok = val_match(v)

            if count_key_pattern and count_value_pattern:
                if k_ok and v_ok:
                    return True
            elif count_key_pattern:
                if k_ok:
                    return True
            elif count_value_pattern:
                if v_ok:
                    return True

        return False

    def walk(node, context):
        new_context = context.copy()

        if isinstance(node, dict):
            # inherit context
            for k in key_order:
                if k in node:
                    new_context[k] = node[k]

            node_type = node.get("Type", "")

            if isinstance(node_type, str) and node_type.startswith("Job"):
                if matches_pattern(node):
                    values = []
                    for k in key_order:
                        values.append(new_context.get(k))
                        if all(values):
                            counts[tuple(values)] += 1

            # recurse generically
            for v in node.values():
                walk(v, new_context)

        elif isinstance(node, list):
            for item in node:
                walk(item, context)

    walk(data, {})

    # Normalize output (all keys always present)
    result = []
    for combo, count in counts.items():
        entry = {
            key: combo[i] if i < len(combo) else ""
            for i, key in enumerate(key_order)
        }
        entry["count"] = count
        result.append(entry)

    return result

#################################################################################

def count_job_types(obj, type_counts, debug=False):
    """
    Recursively count job types in a nested Control-M data structure.
    # type_counts = defaultdict(int)
    # count_job_types(data_dict, type_counts, debug=True)
    """
    if not isinstance(obj, dict):
        return

    # If this dictionary looks like a job definition
    if "Type" in obj and isinstance(obj["Type"], str):
        job_type = obj["Type"]
        if debug:
            print_debug(f"Type:{job_type}", debug)
            type_counts[job_type] += 1
            # Important: don't descend into a job
            return

    # Otherwise, keep traversing (folder / container)
    for value in obj.values():
        count_job_types(value, type_counts, debug)




def key_value_exists(d, target_key, target_value):
    """
    Recursively checks if a dictionary contains a given key-value pair at any depth.
    """
    if not isinstance(d, Mapping):
        return False

    for key, value in d.items():
        # Direct match
        if key == target_key and value == target_value:
            return True
        # If value is another dictionary, search deeper
        if isinstance(value, Mapping) and key_value_exists(value, target_key, target_value):
            return True
        # If value is a list, search inside each element
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and key_value_exists(item, target_key, target_value):
                    return True
    return False


def count_dicts_with_key_value(dict_list, target_key, target_value):
    """
    Counts how many dictionaries in the list contain the target key-value pair at any depth.
    # # Example usage:
    # data = [
    #     {"name": "Alice", "details": {"city": "NY", "age": 25}},
    #     {"name": "Bob", "details": {"city": "LA", "age": 30}},
    #     {"name": "Charlie", "info": {"location": {"city": "NY"}}},
    #     {"name": "David", "city": "NY"},
    #     {"name": "Eve", "details": {"hobbies": [{"type": "sport", "name": "tennis"}]}}
    # ]

    # # Count dictionaries where city == "NY" at any depth
    # result = count_dicts_with_key_value(data, "city", "NY")
    # print(f"Number of dictionaries with city='NY': {result}")
    """
    if not isinstance(dict_list, list):
        raise TypeError("First argument must be a list of dictionaries.")

    count = 0
    for d in dict_list:
        if isinstance(d, Mapping) and key_value_exists(d, target_key, target_value):
            count += 1
    return count


def get_values_for_key(data, key, include_none=False):
    """
    Extracts values for a given key from a list of dictionaries.

    :param data: List containing dictionaries (and possibly other types)
    :param key: Key to search for in each dictionary
    :return: List of values
    """
    if not isinstance(data, list):
        raise TypeError("Data must be a list.")

    values = []
    for item in data:
        if isinstance(item, dict):
            if key in item:
                values.append(item[key])

    return values




# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    assert "You should not see this message" == "This file is not meant to be run directly."