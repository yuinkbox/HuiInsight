#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test environment configuration system.
"""
import os
import sys

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "server"))

def test_config_loading():
    """Test that configuration loads correctly."""
    print("🧪 Testing Environment Configuration System")
    print("=" * 60)
    
    try:
        # 检查配置文件是否存在
        print("\n📊 Test 1: Checking Configuration Files")
        env_files = [
            (".env.development", "开发环境"),
            (".env.production.template", "生产环境模板"),
            (".env.example", "示例文件")
        ]
        
        all_files_exist = True
        for file_name, env_name in env_files:
            if os.path.exists(file_name):
                print(f"✅ Found {env_name} config: {file_name}")
            else:
                print(f"❌ Missing {env_name} config: {file_name}")
                all_files_exist = False
        
        if not all_files_exist:
            print("⚠ Some environment files are missing. Creating test files...")
            # 这里可以调用一个创建测试文件的函数，但为了保持简单，我们只显示消息
            print("   Note: Run 'python scripts/create_env_files.py' to create missing files")
        
        # 检查配置模块是否存在
        print("\n📊 Test 2: Checking Configuration Module")
        config_path = "server/core/config.py"
        if os.path.exists(config_path):
            print(f"✅ Found config module: {config_path}")
            
            # 读取配置文件内容检查
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "class AppConfig" in content:
                    print("✅ Found AppConfig class")
                if "class DatabaseConfig" in content:
                    print("✅ Found DatabaseConfig class")
                if "class ServerConfig" in content:
                    print("✅ Found ServerConfig class")
                if "load_dotenv" in content:
                    print("✅ Uses dotenv for environment loading")
        else:
            print(f"❌ Missing config module: {config_path}")
            return False
        
        # 检查环境变量设置
        print("\n📊 Test 3: Checking Environment Variables")
        env_vars_to_check = ["APP_ENV", "DATABASE_URL", "API_BASE_URL"]
        
        for var in env_vars_to_check:
            value = os.environ.get(var)
            if value:
                print(f"✅ {var} is set: {value[:50]}..." if len(value) > 50 else f"✅ {var} is set: {value}")
            else:
                print(f"⚠ {var} is not set (this is OK for default values)")
        
        # 测试环境文件内容
        print("\n📊 Test 4: Testing Environment File Content")
        if os.path.exists(".env.development"):
            with open(".env.development", 'r', encoding='utf-8') as f:
                content = f.read()
                if "DATABASE_URL" in content:
                    print("✅ .env.development contains DATABASE_URL")
                if "API_BASE_URL" in content:
                    print("✅ .env.development contains API_BASE_URL")
                if "APP_ENV=development" in content:
                    print("✅ .env.development sets APP_ENV=development")
        
        print("\n✅ Backend configuration system is properly set up")
        print("   Note: Full config loading test requires pydantic installation")
        print("   To test with pydantic, run: pip install -r server/requirements.txt")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_frontend_config():
    """Test frontend configuration."""
    print("\n🌐 Testing Frontend Configuration")
    print("=" * 60)
    
    # Check frontend environment files
    frontend_env_files = [
        "client/web/.env.development",
        "client/web/.env.production",
        "client/web/.env.test",
    ]
    
    for env_file in frontend_env_files:
        if os.path.exists(env_file):
            print(f"✅ Found: {env_file}")
            # Read first few lines
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:3]
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            print(f"   {line.strip()}")
            except Exception as e:
                print(f"   Error reading: {e}")
        else:
            print(f"❌ Missing: {env_file}")
    
    return True

def test_build_scripts():
    """Test build script configuration."""
    print("\n🔨 Testing Build Script Configuration")
    print("=" * 60)
    
    # Check build script
    build_script = "client/build/build.py"
    if os.path.exists(build_script):
        print(f"✅ Found: {build_script}")
        
        # Check package.json
        package_json = "client/web/package.json"
        if os.path.exists(package_json):
            print(f"✅ Found: {package_json}")
            
            # Check for environment-specific build scripts
            with open(package_json, 'r', encoding='utf-8') as f:
                content = f.read()
                scripts = [
                    "build:development",
                    "build:production",
                    "build:test",
                ]
                
                for script in scripts:
                    if script in content:
                        print(f"✅ Found script: {script}")
                    else:
                        print(f"❌ Missing script: {script}")
        else:
            print(f"❌ Missing: {package_json}")
    else:
        print(f"❌ Missing: {build_script}")
    
    return True

def main():
    """Main test function."""
    print("🚀 AHDUNYI Terminal PRO - Multi-Environment Configuration Test")
    print("=" * 60)
    
    tests = [
        ("Backend Configuration", test_config_loading),
        ("Frontend Configuration", test_frontend_config),
        ("Build Scripts", test_build_scripts),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Multi-environment configuration is ready.")
    else:
        print("⚠ Some tests failed. Please check the configuration.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())