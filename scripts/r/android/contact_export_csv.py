from _shutil import *
from collections import defaultdict
import csv

IGNORE_DEFAULT_GROUPS = ['My Contacts']


class Contact:
    def __init__(self):
        self.name = None
        self.phone = None
        self.groups = []


if __name__ == '__main__':
    cd('~/Desktop/exported_contact')

    print('Pull raw contacts data via `content query`...')
    call2('adb shell content query --uri content://com.android.contacts/raw_contacts > raw_contacts.txt')
    call2('adb shell content query --uri content://com.android.contacts/data > data.txt')
    call2('adb shell content query --uri content://com.android.contacts/groups > groups.txt')

    print('Export to csv...')

    # Groups
    groups = {}
    with open('groups.txt', encoding='utf-8') as f:
        lines = [line for line in f.readlines() if line.strip()]
    for line in lines:
        contact_id = re.search("\\b_id=(\\d+)", line).group(1)
        title = re.search("\\btitle=(.*?),", line).group(1)
        groups[contact_id] = title

    # Raw contacts
    contacts = defaultdict(Contact)
    with open('raw_contacts.txt', encoding='utf-8') as f:
        lines = [line for line in f.readlines() if line.strip()]
    for line in lines:
        contact_id = re.search("\\b_id=(.*?),", line).group(1)
        name = re.search("\\bdisplay_name=(.*?),", line).group(1)
        contacts[contact_id].name = name

    # Data / relationship
    with open('data.txt', encoding='utf-8') as f:
        lines = [line for line in f.readlines() if line.strip()]
    for line in lines:
        if 'mimetype=vnd.android.cursor.item/phone' in line:
            contact_id = re.search("\\braw_contact_id=(.*?),", line).group(1)
            phone = re.search("\\bdata1=(.*?),", line).group(1)
            contacts[contact_id].phone = phone

        elif 'mimetype=vnd.android.cursor.item/group_membership' in line:
            contact_id = re.search("\\braw_contact_id=(\d+)", line).group(1)
            group_id = re.search("\\bdata1=(\d+)", line).group(1)

            group_name = groups[group_id]
            if group_name not in IGNORE_DEFAULT_GROUPS:
                contacts[contact_id].groups.append(group_name)

    # Write to csv
    with open('contacts.csv', 'w', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile, lineterminator="\n")
        csvwriter.writerow(['Name', 'Phone', 'Groups'])
        for contact in contacts.values():
            csvwriter.writerow([contact.name, contact.phone, '|'.join(contact.groups)])

    call2('explorer .', check=False)
