def parse_yaml(yaml_str: str) -> dict:
    data = {}
    current_key = None
    for line in yaml_str.splitlines():
        line = line.split("#", 1)[0]
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_key:
                if not isinstance(data.get(current_key), list):
                    data[current_key] = []
                data[current_key].append(stripped[2:].strip())
        elif ":" in stripped:
            key, value = stripped.split(":", 1)
            current_key = key.strip()
            data[current_key] = value.strip()
    return data
