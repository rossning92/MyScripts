from _shutil import *


cd("~/Projects/p5_hello")

zip = download("https://github.com/processing/p5.js/releases/download/1.1.9/p5.zip")

unzip(zip)
# shell_open()

shell_open("http://localhost:8000/empty-example/index.html")
call_echo("python -m http.server")

