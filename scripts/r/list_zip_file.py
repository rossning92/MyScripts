import argparse
import zipfile

from utils.fileutils import human_readable_size


def list_files_in_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zipf:
        file_list = [(info.filename, info.file_size) for info in zipf.infolist()]
        sorted_files = sorted(file_list, key=lambda x: x[1], reverse=True)
        for filename, size in sorted_files:
            print(f"{human_readable_size(size)} {filename}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=str)
    args = parser.parse_args()
    list_files_in_zip(args.zip_path)


if __name__ == "__main__":
    main()
