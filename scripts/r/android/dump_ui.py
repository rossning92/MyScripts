import subprocess
import sys
import xml.etree.ElementTree as ET

from utils.termux import is_in_termux


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


def dump_ui():
    def run_cmd(args, text=False):
        if is_in_termux():
            return subprocess.run(
                ["su", "-c", " ".join(args)], check=True, capture_output=True, text=text
            )
        else:
            return subprocess.run(
                ["adb", "shell"] + args, check=True, capture_output=True, text=text
            )

    try:
        run_cmd(["uiautomator", "dump"])
        result = run_cmd(["cat", "/sdcard/window_dump.xml"], text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    xml_data = dump_ui()
    try:
        root = ET.fromstring(xml_data)
        format_node(root)
    except Exception as e:
        print(f"Error parsing XML: {e}")
