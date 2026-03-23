#!/usr/bin/env python3
"""
批量格式化Python文件脚本
用于修复GitHub Actions code-scan失败问题
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """运行命令并打印结果"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} 失败")
            print(f"错误输出: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} 异常: {e}")
        return False

def main():
    print("🚀 开始批量格式化Python文件")
    print("=" * 60)
    
    # 需要格式化的文件列表（根据之前的错误日志）
    files_to_format = [
        "server/core/database.py",
        "server/alembic/env.py",
        "server/db/init_db.py",
        "server/constants/roles.py",
        "server/api/logs.py",
        "server/api/auth.py",
        "shared/patterns/room_id.py",
        "server/db/init_dynamic_roles.py",
        "server/main.py",
        "shared/schemas/audit.py",
        "server/constants/permissions.py",
        "server/api/permissions.py",
        "server/db/models.py",
        "server/api/violation.py",
        "server/db/models_extended.py",
        "server/services/dispatch.py",
        "server/api/tasks.py",
        "server/core/config.py",
        "server/schemas/__init__.py",
        "server/api/team.py",
        "server/api/users.py",
        "server/api/dynamic_roles.py"
    ]
    
    # 检查文件是否存在
    existing_files = []
    for file_path in files_to_format:
        if os.path.exists(file_path):
            existing_files.append(file_path)
        else:
            print(f"⚠️  文件不存在: {file_path}")
    
    print(f"\n📁 找到 {len(existing_files)} 个需要格式化的文件")
    
    # 使用black格式化每个文件
    success_count = 0
    for file_path in existing_files:
        print(f"\n📝 格式化: {file_path}")
        if run_command(f'python -m black "{file_path}"', f"格式化 {os.path.basename(file_path)}"):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 格式化结果: {success_count}/{len(existing_files)} 个文件成功")
    
    # 运行isort排序导入
    print(f"\n{'='*60}")
    print("📋 运行isort排序导入...")
    
    # 格式化server目录
    run_command('python -m isort server/', "排序server目录导入")
    
    # 格式化shared目录
    run_command('python -m isort shared/', "排序shared目录导入")
    
    # 运行flake8检查
    print(f"\n{'='*60}")
    print("🧹 运行flake8代码检查...")
    
    flake8_cmd = 'python -m flake8 server/ shared/ --max-line-length=120 --ignore=E501,W503 --exclude=server/alembic/versions/'
    run_command(flake8_cmd, "flake8代码检查")
    
    print(f"\n{'='*60}")
    print("🎉 批量格式化完成！")
    print("请运行以下命令验证修复效果:")
    print("python -m black --check server/ shared/ --exclude=server/alembic/versions/")
    print("python -m isort --check-only server/ shared/ --skip=server/alembic/versions/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())