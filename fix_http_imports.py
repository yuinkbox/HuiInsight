#!/usr/bin/env python3
"""
修复dynamicRoles.ts中的http导入问题
"""

import os
import re

def fix_http_imports(file_path):
    """修复文件中的http导入"""
    print(f"🔧 修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有http.为api.
    new_content = content.replace('http.', 'api.')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 修复完成: {file_path}")
    
    # 统计替换次数
    http_count = content.count('http.')
    api_count = new_content.count('api.')
    print(f"📊 替换统计: {http_count} 个 http. → {api_count} 个 api.")

def main():
    file_path = "client/web/src/api/dynamicRoles.ts"
    
    if os.path.exists(file_path):
        fix_http_imports(file_path)
    else:
        print(f"❌ 文件不存在: {file_path}")
    
    print("\n🎉 修复完成！")

if __name__ == "__main__":
    main()