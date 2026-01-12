
import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import google
    print(f"Google module path: {google.__path__}")
except ImportError:
    print("Could not import google")

try:
    from google import genai
    print("Successfully imported genai")
except ImportError as e:
    print(f"Failed to import genai: {e}")
    # List contents of google module path
    if 'google' in sys.modules:
        for path in google.__path__:
            try:
                print(f"Contents of {path}: {os.listdir(path)}")
            except Exception as e:
                print(f"Could not list {path}: {e}")
