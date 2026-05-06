from collections import defaultdict
from collections.abc import Mapping

debug = False
isSaaS = False

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

def print_debug(string: str, debug):
    """Print debug information if debug mode is enabled."""
    if debug:
        print(string)

def count_key_value_matches(data_list, key, prefix):
    """
    Counts how many dictionaries in the list have the given key with the specified value.
    
    Args:
        data_list (list): List of dictionaries.
        key (str): Key to check.
        value: Value to match.
    
    Returns:
        int: Number of matching dictionaries.
    """

    prefix = prefix[:3]  # Ensure only first 3 letters are used

    if not isinstance(data_list, list):
        raise TypeError("data_list must be a list of dictionaries.")

    count = 0

    for item in data_list:
        if not isinstance(item, dict):
            continue  # Skip non-dictionary items safely
        value = item.get(key)
        print_debug(f"{key}:{value}", debug)
        if isinstance(value, str) and value.lower().startswith(prefix):
            count += 1

    return count


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





# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    assert "You should not see this message" == "This file is not meant to be run directly."