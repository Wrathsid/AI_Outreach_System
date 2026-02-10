import re

filepath = r'c:\Users\Siddharth\OneDrive\Desktop\Cold emailing\backend\routers\drafts.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix escaped quotes: \" -> "
content = content.replace('\\"', '"')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed escaped quotes in drafts.py")

# Verify
import py_compile
py_compile.compile(filepath, doraise=True)
print("OK: drafts.py compiles successfully")
