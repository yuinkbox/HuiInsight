#!/usr/bin/env python3
"""
移除dynamicRoles.ts中的类型参数
"""

import os
import re

def remove_type_arguments(file_path):
    """移除文件中的类型参数"""
    print(f"🔧 修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除api.get<Type>中的类型参数
    patterns = [
        (r'api\.get<[^>]+>', 'api.get'),
        (r'api\.post<[^>]+>', 'api.post'),
        (r'api\.put<[^>]+>', 'api.put'),
        (r'api\.delete<[^>]+>', 'api.delete'),
    ]
    
    new_content = content
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, new_content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 修复完成: {file_path}")
    
    # 统计替换次数
    changes = 0
    for pattern, _ in patterns:
        changes += len(re.findall(pattern, content))
    
    print(f"📊 移除了 {changes} 个类型参数")

def main():
    file_path = "client/web/src/api/dynamicRoles.ts"
    
    if os.path.exists(file_path):
        remove_type_arguments(file_path)
    else:
        print(f"❌ 文件不存在: {file_path}")
    
    print("\n🎉 修复完成！")

if __name__ == "__main__":
    main()