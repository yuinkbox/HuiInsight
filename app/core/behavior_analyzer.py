"""
语境审计引擎 - 多维行为分析系统
基于业务语境的风险判定，替代单维时长判定

设计原则：
1. 多维校验替代单维时长判定
2. 业务语境优先于机械规则
3. 自动豁免减少误报
4. 内存缓存保证性能
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any
from enum import Enum
import logging

# 轻量级缓存库
try:
    from cachetools import TTLCache
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    TTLCache = None

logger = logging.getLogger(__name__)


class AuditStatus(Enum):
    """审计状态枚举"""
    NORMAL = "normal"               # 正常状态
    SUSPICIOUS = "suspicious"       # 可疑状态（需人工复核）
    SUDDEN_ISSUE = "sudden_issue"   # 突发问题（举报频发）
    RISK_TRACKING = "risk_tracking" # 风险追踪（监控名单）
    EXEMPTED = "exempted"           # 自动豁免（业务合理）


class AuditResult:
    """审计结果封装类"""
    
    def __init__(self, status: AuditStatus, reason: str, checks: List[Dict[str, Any]]):
        """
        初始化审计结果
        
        Args:
            status: 审计状态
            reason: 原因描述
            checks: 校验链详情
        """
        self.status = status
        self.reason = reason
        self.checks = checks
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "reason": self.reason,
            "checks": self.checks
        }


class MemoryCache:
    """
    内存缓存管理器（替代Redis）
    
    实现要点：
    1. 使用TTLCache实现自动过期
    2. 线程安全访问
    3. 性能目标：查询延迟 < 10ms
    """
    
    def __init__(self):
        """初始化内存缓存"""
        if CACHETOOLS_AVAILABLE:
            # 高风险名单缓存：5分钟TTL
            self.risk_list_cache = TTLCache(maxsize=1000, ttl=300)
            # 举报统计缓存：1分钟TTL，滑动窗口
            self.report_cache = TTLCache(maxsize=5000, ttl=60)
            # 房间状态缓存：30秒TTL
            self.room_cache = TTLCache(maxsize=2000, ttl=30)
        else:
            # 降级方案：使用字典+时间戳
            self.risk_list_cache = {}
            self.report_cache = {}
            self.room_cache = {}
            self._cache_timestamps = {}
        
        self._lock = threading.RLock()
    
    def get_risk_list(self) -> List[int]:
        """获取高风险人员名单"""
        with self._lock:
            if CACHETOOLS_AVAILABLE:
                return self.risk_list_cache.get("risk_list", [])
            else:
                data = self.risk_list_cache.get("risk_list")
                timestamp = self._cache_timestamps.get("risk_list", 0)
                # 检查是否过期（5分钟）
                if time.time() - timestamp > 300:
                    return []
                return data or []
    
    def set_risk_list(self, risk_list: List[int]):
        """设置高风险人员名单"""
        with self._lock:
            if CACHETOOLS_AVAILABLE:
                self.risk_list_cache["risk_list"] = risk_list
            else:
                self.risk_list_cache["risk_list"] = risk_list
                self._cache_timestamps["risk_list"] = time.time()
    
    def get_report_count(self, room_id: str, time_window: int) -> int:
        """
        获取房间在时间窗口内的举报次数
        
        Args:
            room_id: 房间ID
            time_window: 时间窗口（秒）
            
        Returns:
            举报次数
        """
        cache_key = f"report_{room_id}_{time_window}"
        with self._lock:
            if CACHETOOLS_AVAILABLE:
                return self.report_cache.get(cache_key, 0)
            else:
                data = self.report_cache.get(cache_key)
                timestamp = self._cache_timestamps.get(cache_key, 0)
                # 检查是否过期（1分钟）
                if time.time() - timestamp > 60:
                    return 0
                return data or 0
    
    def set_report_count(self, room_id: str, time_window: int, count: int):
        """设置房间举报次数"""
        cache_key = f"report_{room_id}_{time_window}"
        with self._lock:
            if CACHETOOLS_AVAILABLE:
                self.report_cache[cache_key] = count
            else:
                self.report_cache[cache_key] = count
                self._cache_timestamps[cache_key] = time.time()
    
    def get_room_status(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取房间状态"""
        with self._lock:
            if CACHETOOLS_AVAILABLE:
                return self.room_cache.get(room_id)
            else:
                data = self.room_cache.get(room_id)
                timestamp = self._cache_timestamps.get(f"room_{room_id}", 0)
                # 检查是否过期（30秒）
                if time.time() - timestamp > 30:
                    return None
                return data
    
    def set_room_status(self, room_id: str, status: Dict[str, Any]):
        """设置房间状态"""
        with self._lock:
            if CACHETOOLS_AVAILABLE:
                self.room_cache[room_id] = status
            else:
                self.room_cache[room_id] = status
                self._cache_timestamps[f"room_{room_id}"] = time.time()


class DataSyncThread(threading.Thread):
    """
    数据同步守护线程
    
    实现要点：
    1. 60秒定时拉取
    2. 异常静默处理
    3. 避免心跳中直接查库
    """
    
    def __init__(self, cache: MemoryCache, db_session_factory):
        """
        初始化数据同步线程
        
        Args:
            cache: 内存缓存实例
            db_session_factory: 数据库会话工厂
        """
        super().__init__(daemon=True)
        self.cache = cache
        self.db_factory = db_session_factory
        self._running = False
        self._sync_interval = 60  # 60秒同步间隔
    
    def run(self):
        """主同步循环"""
        self._running = True
        logger.info("数据同步线程启动，间隔60秒")
        
        while self._running:
            try:
                self._sync_cycle()
                time.sleep(self._sync_interval)
            except Exception as e:
                logger.error(f"数据同步异常: {e}")
                time.sleep(self._sync_interval * 2)  # 异常时延长等待
    
    def stop(self):
        """停止同步线程"""
        self._running = False
        logger.info("数据同步线程停止")
    
    def _sync_cycle(self):
        """单次同步周期"""
        start_time = time.time()
        
        try:
            # 创建数据库会话
            db = self.db_factory()
            
            try:
                # 1. 同步高风险人员名单
                self._sync_risk_list(db)
                
                # 2. 同步近期高频举报房间
                self._sync_report_stats(db)
                
                logger.debug(f"数据同步完成，耗时: {(time.time() - start_time)*1000:.1f}ms")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"同步周期异常: {e}")
            # Fail-Open：静默记录错误，不影响主流程
    
    def _sync_risk_list(self, db):
        """同步高风险人员名单"""
        try:
            # 这里需要根据实际的数据模型查询高风险人员
            # 示例：查询最近7天有违规记录的用户
            from datetime import datetime, timedelta
            from sqlalchemy import and_
            
            # 假设有ViolationRecord模型
            # risk_users = db.query(ViolationRecord.user_id).filter(
            #     ViolationRecord.created_at >= datetime.utcnow() - timedelta(days=7)
            # ).distinct().all()
            
            # 示例数据
            risk_users = [101, 102, 103]  # 高风险用户ID列表
            
            self.cache.set_risk_list(risk_users)
            logger.debug(f"同步高风险名单: {len(risk_users)}人")
            
        except Exception as e:
            logger.error(f"同步高风险名单失败: {e}")
    
    def _sync_report_stats(self, db):
        """同步举报统计数据"""
        try:
            # 这里需要根据实际的举报数据模型查询
            # 示例：查询最近10分钟各房间举报次数
            from datetime import datetime, timedelta
            
            # 假设有ReportRecord模型
            # recent_reports = db.query(
            #     ReportRecord.room_id,
            #     func.count(ReportRecord.id).label('count')
            # ).filter(
            #     ReportRecord.created_at >= datetime.utcnow() - timedelta(minutes=10)
            # ).group_by(ReportRecord.room_id).all()
            
            # 示例数据
            report_stats = {
                "123456": 15,  # 房间ID: 举报次数
                "789012": 8,
                "345678": 3
            }
            
            # 更新缓存
            for room_id, count in report_stats.items():
                self.cache.set_report_count(room_id, 600, count)  # 10分钟窗口
            
            logger.debug(f"同步举报统计: {len(report_stats)}个房间")
            
        except Exception as e:
            logger.error(f"同步举报统计失败: {e}")


class ContextualAuditEngine:
    """
    语境审计引擎 - 核心判定逻辑
    
    性能目标：
    1. 查询延迟 < 10ms（内存缓存）
    2. 60秒数据同步间隔
    3. Fail-Open降级策略
    """
    
    def __init__(self, db_session_factory):
        """
        初始化审计引擎
        
        Args:
            db_session_factory: 数据库会话工厂
        """
        self.db_factory = db_session_factory
        
        # 配置参数
        self.REPORT_SPIKE_THRESHOLD = 10  # 10次/10分钟
        self.REPORT_TIME_WINDOW = 600     # 10分钟（秒）
        self.MAX_STAY_DURATION = 300      # 5分钟（秒），超过此时长触发分析
        self.HOPPING_THRESHOLD = 20       # 10分钟内切换房间数阈值（疑似刷量）
        self.HOPPING_TIME_WINDOW = 600    # 10分钟（秒）
        self.QUERY_TIMEOUT = 0.1          # 100ms查询超时
        
        # 初始化缓存
        self.cache = MemoryCache()
        
        # 用户房间历史缓存（用于Hop-Brushing检测）
        # 格式: {user_id: [(room_id, timestamp), ...]}
        self.user_room_history = TTLCache(maxsize=1000, ttl=self.HOPPING_TIME_WINDOW)
        
        # 启动数据同步线程
        self.sync_thread = DataSyncThread(self.cache, db_session_factory)
        self.sync_thread.start()
        
        # 监控统计
        self.stats = {
            "total_checks": 0,
            "normal_count": 0,
            "suspicious_count": 0,
            "exempted_count": 0,
            "error_count": 0,
            "hopping_detected": 0,  # 新增：频繁跳房检测次数
            "avg_response_time": 0.0
        }
        
        logger.info("ContextualAuditEngine初始化完成")
    
    def analyze_behavior(self, user_id: int, room_id: str, stay_duration: int) -> AuditResult:
        """
        分析用户行为 - 主路由逻辑
        
        执行顺序：
        1. 检查是否触发"频繁跳房"（Hop-Brushing检测）
        2. 检查停留时长是否超限（> 300秒）
        3. 若超限，进入自动豁免校验链
        
        Args:
            user_id: 用户ID
            room_id: 房间ID
            stay_duration: 停留时长（秒）
            
        Returns:
            AuditResult: 审计结果
        """
        start_time = time.time()
        self.stats["total_checks"] += 1
        
        try:
            # Step 1: 检查是否触发"频繁跳房"（Hop-Brushing检测）
            hopping_result = self._check_hopping_behavior(user_id, room_id)
            if hopping_result:
                self.stats["hopping_detected"] += 1
                self.stats["suspicious_count"] += 1
                return hopping_result
            
            # Step 2: 检查停留时长是否超限（> 300秒）
            if stay_duration <= self.MAX_STAY_DURATION:
                result = AuditResult(
                    status=AuditStatus.NORMAL,
                    reason="停留时长在正常范围内",
                    checks=[{"check": "duration", "result": "normal", "duration": stay_duration}]
                )
                self.stats["normal_count"] += 1
                return result
            
            # Step 3: 停留超限，进入自动豁免校验链
            status, reason, checks = self._execute_exemption_chain(user_id, room_id, stay_duration)
            
            result = AuditResult(status=status, reason=reason, checks=checks)
            
            # 更新统计
            if status == AuditStatus.NORMAL:
                self.stats["normal_count"] += 1
            elif status == AuditStatus.SUSPICIOUS:
                self.stats["suspicious_count"] += 1
            elif status in [AuditStatus.SUDDEN_ISSUE, AuditStatus.RISK_TRACKING, AuditStatus.EXEMPTED]:
                self.stats["exempted_count"] += 1
            
        except Exception as e:
            # Fail-Open策略：系统异常时返回正常状态
            logger.error(f"行为分析异常: {e}")
            self.stats["error_count"] += 1
            
            result = AuditResult(
                status=AuditStatus.NORMAL,
                reason="系统检测异常，默认正常状态",
                checks=[{"check": "system_error", "result": "fail_open", "error": str(e)}]
            )
        
        # 更新响应时间统计
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        self._update_avg_response_time(response_time)
        
        return result
    
    def _execute_exemption_chain(self, user_id: int, room_id: str, duration: int) -> Tuple[AuditStatus, str, List[Dict[str, Any]]]:
        """
        执行自动豁免校验链
        
        校验顺序：
        1. ReportSpikeCheck - 举报频发检测
        2. RiskTargetSync - 风险人员轨迹匹配
        3. BusinessContextCheck - 业务语境分析
        
        Args:
            user_id: 用户ID
            room_id: 房间ID
            duration: 停留时长
            
        Returns:
            (状态, 原因描述, 校验详情)
        """
        checks = []
        
        # 1. 举报频发检测
        report_spike_result = self._check_report_spike(room_id)
        checks.append({
            "check": "report_spike",
            "result": "matched" if report_spike_result else "passed",
            "room_id": room_id
        })
        
        if report_spike_result:
            return (
                AuditStatus.SUDDEN_ISSUE,
                f"房间{room_id}近期举报频发（{self.REPORT_SPIKE_THRESHOLD}次/{self.REPORT_TIME_WINDOW//60}分钟）",
                checks
            )
        
        # 2. 风险人员轨迹匹配
        risk_target_result = self._check_risk_target_sync(user_id, room_id)
        checks.append({
            "check": "risk_target",
            "result": "matched" if risk_target_result else "passed",
            "user_id": user_id
        })
        
        if risk_target_result:
            return (
                AuditStatus.RISK_TRACKING,
                f"用户{user_id}在高风险监控名单中，房间{room_id}轨迹重合",
                checks
            )
        
        # 3. 业务语境分析（示例：特殊时间段豁免）
        business_context_result = self._check_business_context(user_id, room_id, duration)
        checks.append({
            "check": "business_context",
            "result": "exempted" if business_context_result else "normal",
            "duration": duration
        })
        
        if business_context_result:
            return (
                AuditStatus.EXEMPTED,
                "业务语境分析：特殊时间段或任务类型豁免",
                checks
            )
        
        # 所有豁免检查通过，标记为可疑
        return (
            AuditStatus.SUSPICIOUS,
            f"长时间停留异常（{duration}秒），无业务语境豁免",
            checks
        )
    
    def _check_report_spike(self, room_id: str) -> bool:
        """
        检查房间在时间窗口内是否举报频发
        
        性能要求：
        - 使用缓存存储最近举报数据
        - 查询延迟 < 10ms
        - 阈值：10次/10分钟
        
        Args:
            room_id: 房间ID
            
        Returns:
            True: 举报频发，需要豁免
            False: 举报正常
        """
        try:
            # 从缓存获取举报次数
            report_count = self.cache.get_report_count(room_id, self.REPORT_TIME_WINDOW)
            
            # 检查是否超过阈值
            return report_count >= self.REPORT_SPIKE_THRESHOLD
            
        except Exception as e:
            # Fail-Open：缓存异常时返回False（不触发豁免）
            logger.error(f"举报频发检查异常: {e}")
            return False
    
    def _check_risk_target_sync(self, user_id: int, room_id: str) -> bool:
        """
        检查员工ID与高风险监控名单轨迹重合
        
        实现要点：
        - 高风险名单缓存更新策略
        - 轨迹重合算法（时间窗口匹配）
        - 缓存失效机制
        
        Args:
            user_id: 用户ID
            room_id: 房间ID
            
        Returns:
            True: 风险人员轨迹重合
            False: 非风险人员
        """
        try:
            # 从缓存获取高风险名单
            risk_list = self.cache.get_risk_list()
            
            # 检查用户是否在风险名单中
            return user_id in risk_list
            
        except Exception as e:
            # Fail-Open：缓存异常时返回False（不触发豁免）
            logger.error(f"风险人员检查异常: {e}")
            return False
    
    def _check_hopping_behavior(self, user_id: int, room_id: str) -> Optional[AuditResult]:
        """
        检查频繁跳房行为（Hop-Brushing检测）
        
        判定规则：
        - 检查该user_id在过去10分钟内访问的不重复房间数
        - 如果超过20个（HOPPING_THRESHOLD），判定为疑似刷量
        
        Args:
            user_id: 用户ID
            room_id: 当前房间ID
            
        Returns:
            AuditResult: 如果触发频繁跳房则返回结果，否则返回None
        """
        try:
            current_time = time.time()
            
            # 获取用户房间历史
            if user_id not in self.user_room_history:
                self.user_room_history[user_id] = []
            
            history = self.user_room_history[user_id]
            
            # 添加当前房间记录
            history.append((room_id, current_time))
            
            # 清理过期记录（10分钟窗口）
            cutoff_time = current_time - self.HOPPING_TIME_WINDOW
            history[:] = [(r, t) for r, t in history if t >= cutoff_time]
            
            # 计算不重复房间数
            unique_rooms = set(room for room, _ in history)
            unique_count = len(unique_rooms)
            
            logger.debug(f"用户{user_id} 10分钟内访问{unique_count}个不重复房间: {list(unique_rooms)[:5]}...")
            
            # 检查是否超过阈值
            if unique_count >= self.HOPPING_THRESHOLD:
                return AuditResult(
                    status=AuditStatus.SUSPICIOUS,
                    reason=f"10分钟内频繁切换房间超{self.HOPPING_THRESHOLD}次（实际{unique_count}次），疑似刷量",
                    checks=[
                        {"check": "hopping_detection", "result": "triggered", "unique_rooms": unique_count},
                        {"check": "hopping_threshold", "result": f"{unique_count}/{self.HOPPING_THRESHOLD}"}
                    ]
                )
            
            return None
            
        except Exception as e:
            # Fail-Open：检测异常时返回None（不触发拦截）
            logger.error(f"频繁跳房检测异常: {e}")
            return None
    
    def _check_business_context(self, user_id: int, room_id: str, duration: int) -> bool:
        """
        业务语境分析
        
        示例豁免场景：
        1. 特殊时间段（如：凌晨审核班次）
        2. 特殊任务类型（如：深度调查任务）
        3. 系统维护时段
        
        Args:
            user_id: 用户ID
            room_id: 房间ID
            duration: 停留时长
            
        Returns:
            True: 业务语境豁免
            False: 无特殊业务语境
        """
        try:
            current_hour = datetime.utcnow().hour
            
            # 示例豁免规则1：凌晨时段（0-6点）豁免
            if 0 <= current_hour < 6:
                logger.debug(f"业务语境豁免：凌晨时段（{current_hour}时）")
                return True
            
            # 示例豁免规则2：深度调查任务豁免
            # 这里可以根据实际业务逻辑扩展
            # 例如：检查用户是否有深度调查任务
            
            # 示例豁免规则3：系统维护时段豁免
            # 可以配置维护时间窗口
            
            return False
            
        except Exception as e:
            # Fail-Open：异常时返回False（不触发豁免）
            logger.error(f"业务语境检查异常: {e}")
            return False
    
    def _update_avg_response_time(self, new_time: float):
        """更新平均响应时间统计"""
        total_time = self.stats["avg_response_time"] * (self.stats["total_checks"] - 1)
        self.stats["avg_response_time"] = (total_time + new_time) / self.stats["total_checks"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return self.stats.copy()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        risk_list = self.cache.get_risk_list()
        return {
            "risk_list_count": len(risk_list),
            "cache_tools_available": CACHETOOLS_AVAILABLE,
            "stats": self.stats
        }
    
    def shutdown(self):
        """关闭引擎，清理资源"""
        logger.info("正在关闭ContextualAuditEngine...")
        self.sync_thread.stop()
        self.sync_thread.join(timeout=5)
        logger.info("ContextualAuditEngine已关闭")


# 工厂函数
def create_audit_engine(db_session_factory) -> ContextualAuditEngine:
    """
    创建审计引擎实例
    
    Args:
        db_session_factory: 数据库会话工厂
        
    Returns:
        ContextualAuditEngine实例
    """
    return ContextualAuditEngine(db_session_factory)


# 测试函数
def test_audit_engine():
    """审计引擎测试函数"""
    print("=== ContextualAuditEngine 测试 ===")
    
    # 模拟数据库会话工厂
    class MockDBSession:
        def close(self):
            pass
    
    def mock_db_factory():
        return MockDBSession()
    
    # 创建引擎
    engine = create_audit_engine(mock_db_factory)
    
    try:
        print("1. 测试频繁跳房检测（Hop-Brushing）")
        test_user_id = 1000
        
        # 模拟用户频繁切换房间
        for i in range(25):  # 超过20次阈值
            room_id = f"room_{i:03d}"
            result = engine.analyze_behavior(test_user_id, room_id, 30)  # 30秒停留
            if result.status == AuditStatus.SUSPICIOUS and "频繁切换房间" in result.reason:
                print(f"✅ 频繁跳房检测触发: {result.reason}")
                break
        
        print("\n2. 测试正常停留")
        result1 = engine.analyze_behavior(1001, "123456", 180)  # 3分钟
        print(f"测试1 - 正常停留: {result1.status.value} - {result1.reason}")
        
        print("\n3. 测试超长停留（无豁免）")
        result2 = engine.analyze_behavior(1002, "789012", 600)  # 10分钟
        print(f"测试2 - 超长停留: {result2.status.value} - {result2.reason}")
        
        print("\n4. 测试高风险人员豁免")
        engine.cache.set_risk_list([1003])
        result3 = engine.analyze_behavior(1003, "345678", 400)  # 6分40秒
        print(f"测试3 - 高风险人员: {result3.status.value} - {result3.reason}")
        
        print("\n5. 测试举报频发豁免")
        # 设置房间举报次数超过阈值
        engine.cache.set_report_count("999999", 600, 15)  # 15次/10分钟
        result4 = engine.analyze_behavior(1004, "999999", 400)  # 6分40秒
        print(f"测试4 - 举报频发: {result4.status.value} - {result4.reason}")
        
        print("\n6. 测试业务语境豁免（凌晨时段）")
        # 注意：这个测试需要在0-6点运行才有效
        current_hour = datetime.utcnow().hour
        if 0 <= current_hour < 6:
            result5 = engine.analyze_behavior(1005, "111111", 400)  # 6分40秒
            print(f"测试5 - 业务语境豁免: {result5.status.value} - {result5.reason}")
        else:
            print(f"测试5 - 跳过（当前时间{current_hour}时，非凌晨时段）")
        
        # 显示统计信息
        print(f"\n=== 引擎统计 ===")
        stats = engine.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        print(f"\n=== 缓存信息 ===")
        cache_info = engine.get_cache_info()
        for key, value in cache_info.items():
            print(f"{key}: {value}")
        
    finally:
        engine.shutdown()


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    test_audit_engine()