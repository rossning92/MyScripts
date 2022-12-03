import argparse
import subprocess
import xml.etree.ElementTree as ET
from collections import namedtuple
from pprint import pprint

Host = namedtuple("Host", "ipv4 mac vendor")


def scan_network(vendor=None):
    result = []
    out = subprocess.check_output(
        ["nmap", "-sn", "192.168.0.1/24", "-oX", "-"], universal_newlines=True
    )
    root = ET.fromstring(out)

    for host in root.findall("host"):
        # Get ipv4
        ipv4_addr = host.find("./address[@addrtype='ipv4']")
        if ipv4_addr is None:
            continue
        ipv4 = ipv4_addr.attrib["addr"]

        # Get MAC addr
        mac_addr = host.find("./address[@addrtype='mac']")
        if mac_addr is None:
            continue
        mac = mac_addr.attrib["addr"]

        # Get vendor
        if "vendor" in mac_addr.attrib:
            vendor_ = mac_addr.attrib["vendor"]
        else:
            vendor_ = None
        # Filter by vendor
        if vendor is not None:
            if vendor_ is None or vendor not in vendor_:
                continue

        result.append(Host(ipv4, mac, vendor_))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vendor",
        default=None,
        type=str,
    )
    parser.add_argument("--show_ipv4", action="store_true")
    args = parser.parse_args()

    result = scan_network(vendor=args.vendor)
    if args.show_ipv4:
        for host in result:
            print(host.ipv4)
    else:
        pprint(result)
