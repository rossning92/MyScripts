from _shutil import *
import pandas as pd

print2('Clear all contacts...', color='red')
call2('adb shell pm clear com.android.providers.contacts')

f = r"C:\Users\rossning92\Downloads\contacts.csv"

contact_id = 1
next_group_id = 7
group_id_dict = {}

df = pd.read_csv(f)
for index, row in df.iterrows():
    print('(%d / %d) Import %s...' % (index + 1, df.shape[0], row["Name"]))

    call2(f'adb shell content insert'
          f' --uri content://com.android.contacts/raw_contacts'
          f' --bind account_type:s: --bind account_name:s:')

    call2(f'adb shell content insert'
          f' --uri content://com.android.contacts/data'
          f' --bind raw_contact_id:i:{contact_id}'
          f' --bind mimetype:s:vnd.android.cursor.item/name'
          f' --bind data1:s:{row["Name"]}')

    call2(f'adb shell content insert'
          f' --uri content://com.android.contacts/data'
          f' --bind raw_contact_id:i:{contact_id}'
          f' --bind mimetype:s:vnd.android.cursor.item/phone_v2'
          f' --bind data1:s:{row["Phone"]}')

    # Group membership
    group_name = row['Groups']
    if group_name in group_id_dict:
        group_id = group_id_dict[group_name]

    else:  # Add new group
        call2(f'adb shell content insert'
              f' --uri content://com.android.contacts/groups'
              f' --bind title:s:{group_name}')

        group_id = next_group_id
        group_id_dict[group_name] = next_group_id
        next_group_id += 1

    call2(f'adb shell content insert'
          f' --uri content://com.android.contacts/data'
          f' --bind raw_contact_id:i:{contact_id}'
          f' --bind mimetype:s:vnd.android.cursor.item/group_membership'
          f' --bind data1:s:{group_id}')

    contact_id += 1

    # if contact_id > 3:
    #     break
