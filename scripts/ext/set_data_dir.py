import os

if __name__ == "__main__":
    script_root = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(script_root + "/../../config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    config_file = os.path.join(config_dir, "data_dir.txt")

    cur_path = None
    if os.path.exists(config_file):
        with open(config_file) as f:
            cur_path = f.read()

    path = input("Enter new data dir (current: %s): " % cur_path)

    with open(config_file, "w") as f:
        f.write(path)
