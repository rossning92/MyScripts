from _script import get_all_scripts, get_script_config_file

if __name__ == "__main__":
    for file in get_all_scripts():
        print("File: %s" % file)
        script_config_file = get_script_config_file(file)
        if script_config_file:
            print("  Config: %s" % script_config_file)
