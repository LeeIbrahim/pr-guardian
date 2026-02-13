import os
import sys

# Add src to path manually for this check
sys.path.insert(0, os.path.abspath("src"))

try:
    import pr_guardian
    print("✅ Success: pr_guardian package found!")
    import pr_guardian.main
    print("✅ Success: pr_guardian.main module found!")
except ImportError as e:
    print(f"❌ Error: {e}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Contents of src: {os.listdir('src') if os.path.exists('src') else 'src folder missing'}")