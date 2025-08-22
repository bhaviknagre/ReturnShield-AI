import glob

# Go through all HTML files inside templates directory
for file in glob.glob("app/templates/*.html"):
    with open(file, "rb") as f:
        content = f.read()

    try:
        # Try decoding as UTF-8 first
        text = content.decode("utf-8")
        print(f"✅ {file} is already UTF-8")
    except UnicodeDecodeError:
        # If it fails, decode as Windows-1252 (common issue) and re-save as UTF-8
        text = content.decode("cp1252")
        with open(file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"🔧 Fixed encoding and saved {file} as UTF-8")
