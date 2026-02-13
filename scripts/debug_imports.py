import os
import sys
from pathlib import Path

# Force the 'src' directory onto the path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

print(f"PYTHONPATH: {sys.path[0]}")
print(f"Looking for 'pr_guardian' in: {src_path}")

if os.path.exists(os.path.join(src_path, "pr_guardian")):
    print("✅ Folder 'src/pr_guardian' exists.")
    if os.path.exists(os.path.join(src_path, "pr_guardian", "__init__.py")):
        print("✅ '__init__.py' exists inside the folder.")
    else:
        print("❌ '__init__.py' is MISSING inside 'src/pr_guardian'.")
else:
    print("❌ Folder 'src/pr_guardian' NOT FOUND. Check spelling/location.")

try:
    import pr_guardian
    print("✅ SUCCESS: Package imported!")
    from pr_guardian import main
    print("✅ SUCCESS: Main module imported!")
except ImportError as e:
    print(f"❌ IMPORT FAILED: {e}")