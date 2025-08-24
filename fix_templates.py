import glob

for file in glob.glob("app/templates/*.html"):
    with open(file, "rb") as f:
        content = f.read()

    try:
        text = content.decode("utf-8")
        print(f"✅ {file} is already UTF-8")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
        with open(file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"🔧 Fixed encoding and saved {file} as UTF-8")
