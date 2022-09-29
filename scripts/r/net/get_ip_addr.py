from _shutil import get_ip_addresses

if __name__ == "__main__":
    for ip in get_ip_addresses():
        print(ip)
