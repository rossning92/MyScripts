import subprocess
import sys
import xml.etree.ElementTree as ET


def format_node(node, level=0):
    attr = node.attrib
    text = attr.get("text", "")
    res_id = attr.get("resource-id", "").split("/")[-1]
    cls = attr.get("class", "").split(".")[-1]
    content_desc = attr.get("content-desc", "")

    info = []
    if text:
        info.append(f'text="{text}"')
    if content_desc:
        info.append(f'desc="{content_desc}"')
    if res_id:
        info.append(f'id="{res_id}"')

    if info:
        print("  " * level + f"{cls}: {' '.join(info)}")
        for child in node:
            format_node(child, level + 1)
    else:
        for child in node:
            format_node(child, level)


def run_adb():
    try:
        subprocess.run(
            ["adb", "shell", "uiautomator", "dump"], check=True, capture_output=True
        )
        result = subprocess.run(
            ["adb", "shell", "cat", "/sdcard/window_dump.xml"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running adb: {e}")
        sys.exit(1)


if __name__ == "__main__":
    xml_data = run_adb()
    try:
        root = ET.fromstring(xml_data)
        format_node(root)
    except Exception as e:
        print(f"Error parsing XML: {e}")
