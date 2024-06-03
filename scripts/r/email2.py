import argparse
import webbrowser
from urllib.parse import quote


def email(*, to: str, subject: str, body: str):
    mailto = f"mailto:{to}?subject={quote(subject)}&body={quote(body, safe='')}"
    webbrowser.open(mailto)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--to", required=True)
    parser.add_argument("-s", "--subject", required=True)
    parser.add_argument("-b", "--body", required=True)

    args = parser.parse_args()

    email(to=args.to, subject=args.subject, body=args.body)


if __name__ == "__main__":
    _main()
