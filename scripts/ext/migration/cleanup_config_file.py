import glob
import os

from _script import get_script_default_config, load_script_config, save_script_config
from _shutil import cd, print2


DRY_RUN = False

if __name__ == "__main__":
    cd("../../")

    default = get_script_default_config()

    for f in glob.glob("**/*.yaml", recursive=True):
        f = f.replace("\\", "/")

        if f.endswith(".config.yaml"):
            continue

        data = load_script_config(f)

        # Check if the config file is valid.
        valid = False
        for k in default.keys():
            if k in data:
                valid = True
                break
        if not valid:
            continue

        # Rename the meta file
        new_file = f.replace(".yaml", ".config.yaml")
        print2("Rename %s => %s" % (f, new_file), color="cyan")
        if not DRY_RUN:
            os.rename(f, new_file)
            f = new_file

        # Remove default values
        new_config = {}
        for k, v in data.items():
            if k not in default:
                continue

            assert k in default
            if v != default[k]:
                new_config[k] = v

        if len(new_config) == 0:
            print2("Remove config: %s" % f, color="red")
            if not DRY_RUN:
                os.remove(f)

        elif new_config != data:
            print("Updating config file: %s: %s" % (f, str(new_config)))
            if not DRY_RUN:
                save_script_config(new_config, f)