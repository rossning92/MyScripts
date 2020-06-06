from _shutil import *
import chardet


cd(os.environ["CURRENT_FOLDER"])

EXT = [".cpp", ".c", ".java", ".py", ".h", ".cs", ".html", ".cshtml", ".jsp"]

txt = []

for file in glob.glob("**/*", recursive=True):
    file_name = file.replace("\\", "/")

    if os.path.splitext(file)[1] not in EXT:
        continue

    print(file_name)

    txt.append(file_name)
    txt.append("")

    with open(file, "rb") as f:
        rawdata = f.read()
        result = chardet.detect(rawdata)
        charenc = result["encoding"]

    with open(file, encoding=charenc, errors="replace") as f:
        s = f.read()

        txt.append("```")
        txt.append(s)
        txt.append("```")

lines = "\n".join(txt).splitlines()
print("total lines: %d" % len(lines))
with open("source.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
