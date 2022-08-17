import os

if __name__ == "__main__":
    path = input("Custom path to the data directory: ")

    script_root = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(script_root + "/../../config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    with open(os.path.join(config_dir, "data_dir.txt"), "w") as f:
        f.write(path)
