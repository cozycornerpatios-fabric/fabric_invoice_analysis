#!/usr/bin/env python3
"""
Test script to verify PDF extractor setup
"""

def test_imports():
    """Test if all required packages can be imported"""
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import fitz
        print("✅ PyMuPDF imported successfully")
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"❌ PyPDF2 import failed: {e}")
        return False
    
    try:
        from supabase import create_client
        print("✅ Supabase imported successfully")
    except ImportError as e:
        print(f"❌ Supabase import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if supabase_url and supabase_url != 'your_supabase_url_here':
        print("✅ SUPABASE_URL is set")
    else:
        print("⚠️  SUPABASE_URL not configured (set to default value)")
    
    if supabase_key and supabase_key != 'your_supabase_anon_key_here':
        print("✅ SUPABASE_KEY is set")
    else:
        print("⚠️  SUPABASE_KEY not configured (set to default value)")
    
    return True

def test_files():
    """Test if required files exist"""
    import os
    
    required_files = [
        'app.py',
        'templates/index.html',
        'requirements.txt',
        'supabase_setup.sql',
        '.env'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🔍 Testing PDF Extractor Setup...\n")
    
    tests = [
        ("Package Imports", test_imports),
        ("Environment Variables", test_environment),
        ("Required Files", test_files)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"📋 Testing: {test_name}")
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All tests passed! Your setup is ready.")
        print("\n📝 Next steps:")
        print("1. Update your .env file with real Supabase credentials")
        print("2. Run the SQL commands in supabase_setup.sql in your Supabase dashboard")
        print("3. Add some fabric data to the fabrics_master table")
        print("4. Run: python app.py")
        print("5. Open http://localhost:5000 in your browser")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Troubleshooting tips:")
        print("- Run: pip install -r requirements.txt")
        print("- Check if all files are in the correct locations")
        print("- Verify your Python environment")

if __name__ == "__main__":
    main()
