#!/usr/bin/env python3
"""
独立的主管大屏启动器 - 与后端API解耦
避免在后端服务器中导入PyQt6 GUI库
"""

import sys
import json
import argparse
from pathlib import Path

def main():
    """主函数 - 独立GUI启动器"""
    parser = argparse.ArgumentParser(description='AHDUNYI 主管大屏启动器')
    parser.add_argument('--config', type=str, required=True, help='配置文件路径')
    parser.add_argument('--api-url', type=str, help='API地址（覆盖配置）')
    parser.add_argument('--token', type=str, help='访问令牌（覆盖配置）')
    parser.add_argument('--role', type=str, help='用户角色（覆盖配置）')
    
    args = parser.parse_args()
    
    # 加载配置
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}")
        sys.exit(1)
    
    # 使用命令行参数覆盖配置
    api_url = args.api_url or config.get('api_url', 'http://127.0.0.1:8000')
    access_token = args.token or config.get('access_token', '')
    user_role = args.role or config.get('user_role', 'SUPERVISOR')
    
    print(f"启动主管大屏:")
    print(f"  API地址: {api_url}")
    print(f"  用户角色: {user_role}")
    
    # 动态导入GUI模块（只在需要时导入）
    try:
        from .supervisor_dashboard import launch_supervisor_dashboard
        
        launch_supervisor_dashboard(
            api_url=api_url,
            access_token=access_token,
            user_role=user_role
        )
    except ImportError as e:
        print(f"导入GUI模块失败: {e}")
        print("请确保已安装PyQt6: pip install PyQt6")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()