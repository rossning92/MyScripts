import os
import subprocess

import pandas as pd


def main():
    input("Press enter to delete all contacts. Caution: this action is dangerous!")
    print("Clear all contacts...")
    subprocess.check_call(
        ["adb", "shell", "pm", "clear", "com.android.providers.contacts"]
    )

    csv_file = os.environ["CONTACT_CSV_FILE"]

    contact_id = 1
    next_group_id = 1
    group_id_dict = {}

    df = pd.read_csv(csv_file)
    for index, row in df.iterrows():
        print("(%d / %d) Import %s..." % (index + 1, df.shape[0], row["Name"]))

        subprocess.check_call(
            [
                "adb",
                "shell",
                "content",
                "insert",
                "--uri",
                "content://com.android.contacts/raw_contacts",
                "--bind",
                "account_type:s:",
                "--bind",
                "account_name:s:",
            ]
        )

        subprocess.check_call(
            [
                "adb",
                "shell",
                "content",
                "insert",
                "--uri",
                "content://com.android.contacts/data",
                "--bind",
                f"raw_contact_id:i:{contact_id}",
                "--bind",
                "mimetype:s:vnd.android.cursor.item/name",
                "--bind",
                f'data1:s:{row["Name"]}',
            ]
        )

        subprocess.check_call(
            [
                "adb",
                "shell",
                "content",
                "insert",
                "--uri",
                "content://com.android.contacts/data",
                "--bind",
                f"raw_contact_id:i:{contact_id}",
                "--bind",
                "mimetype:s:vnd.android.cursor.item/phone_v2",
                "--bind",
                f'data1:s:{row["Phone"]}',
            ]
        )

        # Group membership
        group_name = row["Groups"]
        if group_name in group_id_dict:
            group_id = group_id_dict[group_name]

        else:  # Add new group
            subprocess.check_call(
                [
                    "adb",
                    "shell",
                    "content",
                    "insert",
                    "--uri",
                    "content://com.android.contacts/groups",
                    "--bind",
                    f"title:s:{group_name}",
                ]
            )

            group_id = next_group_id
            group_id_dict[group_name] = next_group_id
            next_group_id += 1

        subprocess.check_call(
            [
                "adb",
                "shell",
                "content",
                "insert",
                "--uri",
                "content://com.android.contacts/data",
                "--bind",
                f"raw_contact_id:i:{contact_id}",
                "--bind",
                "mimetype:s:vnd.android.cursor.item/group_membership",
                "--bind",
                f"data1:s:{group_id}",
            ]
        )

        contact_id += 1


if __name__ == "__main__":
    main()
