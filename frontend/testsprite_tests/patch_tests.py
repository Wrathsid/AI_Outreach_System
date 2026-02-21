import os
import glob
import re

def patch_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content

        # 1. Remove args from chromium.launch
        # We look for the pattern: browser = await pw.chromium.launch(headless=True, args=[...])
        # We want to replace it with: browser = await pw.chromium.launch(headless=True)
        
        if "args=[" in content and "--single-process" in content:
            # Regex that matches from `launch(` to the closing `)` provided it contains `args=[`
            # We use non-greedy match for content inside args
            pattern_full = r'browser = await pw\.chromium\.launch\s*\(\s*headless=True,\s*args=\[.*?\]\s*,?\s*\)'
            new_content = re.sub(pattern_full, 'browser = await pw.chromium.launch(headless=True)', new_content, flags=re.DOTALL)
        
        # 2. wait_until="networkidle" -> "domcontentloaded"
        if 'wait_until="networkidle"' in new_content:
            new_content = new_content.replace('wait_until="networkidle"', 'wait_until="domcontentloaded"')
        
        if content != new_content:
            print(f"Patching {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            print(f"Skipping {filepath} (no changes needed)")
            
    except Exception as e:
        print(f"Error patching {filepath}: {e}")

def main():
    test_files = glob.glob("TC*.py")
    for f in test_files:
        patch_file(f)

if __name__ == "__main__":
    main()
