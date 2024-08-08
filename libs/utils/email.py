import webbrowser
from urllib.parse import quote


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
