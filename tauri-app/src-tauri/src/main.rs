/**
 * 徽鉴HuiInsight - 审核部门中台系统
 * Tauri应用主入口
 * @author xuyu
 */

// 预导入模块
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::Manager;
use huijian::{init_app, AppState, commands};

/// 主函数
fn main() {
    // 初始化日志
    env_logger::init();
    
    // 创建Tauri应用
    tauri::Builder::default()
        .setup(|app| {
            // 初始化应用状态
            let handle = app.handle();
            tauri::async_runtime::block_on(async {
                match init_app().await {
                    Ok(app_state) => {
                        // 将应用状态存储到Tauri状态管理
                        handle.manage(app_state);
                        println!("应用初始化成功");
                    }
                    Err(e) => {
                        eprintln!("应用初始化失败: {}", e);
                        std::process::exit(1);
                    }
                }
            });
            
            Ok(())
        })
        // 注册Tauri Commands
        .invoke_handler(tauri::generate_handler![
            commands::login,
            commands::logout,
            commands::verify_token,
            commands::check_permission,
            commands::get_current_user,
            commands::get_or_create_today_task,
            commands::start_audit_task,
            commands::update_task_progress,
            commands::complete_audit_task,
            commands::get_user_tasks,
        ])
        .run(tauri::generate_context!())
        .expect("运行Tauri应用失败");
}