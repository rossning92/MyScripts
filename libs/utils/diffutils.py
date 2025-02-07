from collections import defaultdict
from typing import Dict, List, Tuple


def extract_modified_files_and_line_ranges(
    diff_file: str,
) -> Dict[str, List[Tuple[int, int]]]:
    result = defaultdict(list)
    with open(diff_file, "r") as file:
        current_file = None
        for line in file:
            if line.startswith("diff --git"):
                parts = line.split()
                current_file = parts[-1].replace("b/", "", 1)  # Assumes 'b/' prefixing
            elif line.startswith("@@") and current_file:
                hunk_info = line.split(" ")[2]
                start_line, line_count = map(int, hunk_info[1:].split(","))
                result[current_file].append((start_line, start_line + line_count))
    return result
