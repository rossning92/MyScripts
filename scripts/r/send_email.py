import argparse

from utils.email import send_email


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--to", required=True)
    parser.add_argument("-s", "--subject", required=True)
    parser.add_argument("-b", "--body", required=True)
    parser.add_argument("--use-gmail-web", action="store_true")

    args = parser.parse_args()

    send_email(
        to=args.to,
        subject=args.subject,
        body=args.body,
        use_gmail_web=args.ues_gmail_web,
    )


if __name__ == "__main__":
    _main()
