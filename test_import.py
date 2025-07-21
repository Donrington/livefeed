
# test_imports.py (improved)
import sys
import os

def test_imports():
    print("🔍 Testing shared module imports...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    print(f"📁 Current directory: {current_dir}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Check if shared directory exists
    shared_path = os.path.join(current_dir, "shared")
    if not os.path.exists(shared_path):
        print(f"❌ shared directory not found at: {shared_path}")
        return False
    
    print(f"✅ shared directory found at: {shared_path}")
    
    # Check if base.py exists
    base_path = os.path.join(shared_path, "base.py")
    if not os.path.exists(base_path):
        print(f"❌ base.py not found at: {base_path}")
        return False
    
    print(f"✅ base.py found at: {base_path}")
    
    # Try the import
    try:
        print("🔄 Attempting import...")
        from shared.base import HTTPMetricsReporter, NullMetricsReporter, StreamComponent
        print("✅ SUCCESS! All imports working!")
        
        # Test object creation
        null_reporter = NullMetricsReporter()
        http_reporter = HTTPMetricsReporter("http://test.com")
        print("✅ Object creation successful!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 This usually means:")
        print("   1. shared/base.py is empty or has syntax errors")
        print("   2. shared/__init__.py is missing")
        print("   3. File permissions issue")
        return False
    except SyntaxError as e:
        print(f"❌ Syntax error in shared/base.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()