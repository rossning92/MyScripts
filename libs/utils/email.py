import webbrowser
from typing import Optional
from urllib.parse import quote

from utils.template import render_template


def send_email(
    *, to: str = "", subject: str = "", body: str = "", cc: str = "", gmail=False
):
    subject = quote(subject)
    body = quote(body, safe="")
    if gmail:
        url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={subject}&body={body}&bcc={cc}"
    else:
        url = f"mailto:{to}?subject={subject}&body={quote(body, safe='')}"
    webbrowser.open(url)


def send_email_md(file_path: str, to: str = "", context=None):
    with open(file_path, "r", encoding="utf-8") as f:
        s = f.read()
        content = render_template(s, context=context)

    subject = ""
    cc = ""
    gmail = False
    body = ""

    i = 0
    lines = content.splitlines()
    if lines[0] == "---":
        i = 1
        while lines[i] != "---":
            k, v = lines[i].split(":", maxsplit=2)
            if k.lower() == "cc" or k.lower() == "bcc":
                cc = v.strip()
            elif k.lower() == "subject":
                subject = v.strip()
            elif k.lower() == "to":
                if not to:
                    to = v.strip()
            elif k.lower() == "gmail":
                gmail = True
            i += 1
        i += 1

    while lines[i].strip() == "":  # skip empty lines
        i += 1

    while i < len(lines):
        body += lines[i] + "\n"
        i += 1

    send_email(
        body=body,
        cc=cc,
        gmail=gmail,
        subject=subject,
        to=to,
    )
