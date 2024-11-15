import os
import xml.etree.ElementTree as ET

from _shutil import start_process

host_name = os.environ["NX_HOST"]
session_file = os.path.expanduser(f"~/NoMachine/{host_name}.nxs")


def update_xml(session_file):
    settings = {
        "Advanced": {
            "Grab keyboard input": "true",
        },
        "General": {
            "Connection service": "nx",
            "NoMachine daemon port": os.environ.get("NX_PORT", "4000"),
            "Physical desktop resize mode": "viewport",
            "Remember password": "true",
            "Remember username": "true",
            "Server host": host_name,
            "Session window state": "fullscreen",
            # Skip messages
            "Show remote audio alert message": "false",
            "Show remote desktop view mode message": "false",
            "Show remote display resize message": "false",
            # Screen resolution
            "Use custom resolution": "true",
            "Resolution height": "1080",
            "Resolution width": "1920",
        },
        "Login": {
            "Last selected user login": "system user",
            "Always use selected user login": "true",
            "Server authentication method": "system",
            "User": os.environ["NX_USER"],
            "NX login method": "password",
        },
    }

    # Create file if does not exist
    if not os.path.exists(session_file):
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        root = ET.Element("NXClientSettings", version="2.2", application="nxclient")
    else:
        tree = ET.parse(session_file)
        root = tree.getroot()

    # Update or insert groups and options
    for group_name, options in settings.items():
        group = root.find(f"group[@name='{group_name}']")
        if group is None:
            group = ET.SubElement(root, "group", name=group_name)
        for key, value in options.items():
            option = group.find(f"option[@key='{key}']")
            if option is None:
                ET.SubElement(group, "option", key=key, value=value)
            else:
                option.set("value", value)

    xml_string = ET.tostring(root, encoding="unicode")
    xml_string_with_doctype = "<!DOCTYPE NXClientSettings>\n" + xml_string
    with open(session_file, "w", encoding="utf-8") as file:
        file.write(xml_string_with_doctype)


if __name__ == "__main__":
    update_xml(session_file)
    start_process(["/usr/NX/bin/nxplayer", "--session", session_file])
