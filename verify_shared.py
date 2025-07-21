
import os

def verify_shared_directory():
    print("🔍 Checking shared directory structure...")
    
    # Check if shared directory exists
    if os.path.exists("shared"):
        print("✅ shared/ directory exists")
    else:
        print("❌ shared/ directory missing!")
        return False
    
    # Check if __init__.py exists
    if os.path.exists("shared/__init__.py"):
        print("✅ shared/__init__.py exists")
    else:
        print("❌ shared/__init__.py missing!")
        print("   Creating empty __init__.py...")
        with open("shared/__init__.py", "w") as f:
            f.write("# This file makes shared a Python package\n")
        print("✅ Created shared/__init__.py")
    
    # Check if base.py exists
    if os.path.exists("shared/base.py"):
        print("✅ shared/base.py exists")
        
        # Check if it has content
        with open("shared/base.py", "r") as f:
            content = f.read().strip()
            if content:
                print(f"✅ shared/base.py has content ({len(content)} characters)")
            else:
                print("❌ shared/base.py is empty!")
                return False
    else:
        print("❌ shared/base.py missing!")
        return False
    
    return True

def test_import():
    print("\n🧪 Testing import...")
    
    import sys
    import os
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        from shared.base import HTTPMetricsReporter, NullMetricsReporter, StreamComponent
        print("✅ Import successful!")
        
        # Test creating objects
        reporter = NullMetricsReporter()
        print("✅ NullMetricsReporter created")
        
        http_reporter = HTTPMetricsReporter("http://test.com")
        print("✅ HTTPMetricsReporter created")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SHARED MODULE VERIFICATION")
    print("=" * 50)
    
    if verify_shared_directory():
        test_import()
    else:
        print("\n❌ Please fix the shared directory structure first")