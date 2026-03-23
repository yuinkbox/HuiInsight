# -*- coding: utf-8 -*-
"""
增强版网络客户端 - 包含优雅的探活机制和详细错误诊断

功能：
1. 详细的连接错误诊断（超时、DNS解析失败、端口拒绝等）
2. 健康检查端点探测
3. 自动重试和退避机制
4. 连接状态监控

Author : AHDUNYI
Version: 9.1.0
"""

import time
import socket
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import NewConnectionError, MaxRetryError

logger = logging.getLogger(__name__)


class ConnectionErrorType(Enum):
    """连接错误类型枚举"""
    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_RESOLUTION_FAILED = "dns_resolution_failed"
    NETWORK_UNREACHABLE = "network_unreachable"
    SSL_ERROR = "ssl_error"
    UNKNOWN = "unknown"
    HTTP_ERROR = "http_error"


class DetailedNetworkError(Exception):
    """详细的网络错误异常"""
    
    def __init__(
        self,
        message: str,
        error_type: ConnectionErrorType,
        status_code: int = 0,
        detail: str = "",
        url: str = "",
        original_exception: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.status_code = status_code
        self.detail = detail
        self.url = url
        self.original_exception = original_exception
        
    def __str__(self) -> str:
        base = f"{self.error_type.value}: {super().__str__()}"
        if self.url:
            base += f" (URL: {self.url})"
        if self.status_code:
            base += f" (HTTP {self.status_code})"
        return base


class EnhancedNetworkClient:
    """增强版网络客户端"""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        max_retries: int = 2,
        backoff_factor: float = 0.5
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = self._build_session(max_retries, backoff_factor)
        self._token: Optional[str] = None
        self._last_health_check: Optional[float] = None
        self._health_check_cache_ttl = 30  # 健康检查缓存时间（秒）
        
    # ------------------------------------------------------------------
    # 配置方法
    # ------------------------------------------------------------------
    
    def set_token(self, token: str) -> None:
        """设置Bearer token"""
        self._token = token
        self._session.headers.update({"Authorization": f"Bearer {token}"})
        logger.debug("Bearer token已更新")
        
    def clear_token(self) -> None:
        """清除Bearer token"""
        self._token = None
        self._session.headers.pop("Authorization", None)
        logger.debug("Bearer token已清除")
        
    # ------------------------------------------------------------------
    # 健康检查方法
    # ------------------------------------------------------------------
    
    def health_check(self, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        执行健康检查
        
        Args:
            force: 是否强制检查（忽略缓存）
            
        Returns:
            (是否健康, 错误信息)
        """
        # 检查缓存
        if not force and self._last_health_check:
            elapsed = time.time() - self._last_health_check
            if elapsed < self._health_check_cache_ttl:
                logger.debug("使用缓存的健康检查结果")
                return True, None
                
        try:
            response = self._session.get(
                f"{self._base_url}/health",
                timeout=self._timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self._last_health_check = time.time()
                    logger.info("健康检查成功: %s", self._base_url)
                    return True, None
                else:
                    error_msg = f"服务器状态异常: {data.get('status')}"
                    logger.warning(error_msg)
                    return False, error_msg
            else:
                error_msg = f"健康检查失败: HTTP {response.status_code}"
                logger.warning(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_type, error_msg = self._analyze_connection_error(e, "/health")
            logger.warning("健康检查失败: %s", error_msg)
            return False, error_msg
            
    def check_connectivity(self) -> Dict[str, Any]:
        """
        检查连接性（详细诊断）
        
        Returns:
            包含详细连接信息的字典
        """
        result = {
            "server_url": self._base_url,
            "reachable": False,
            "error_type": None,
            "error_message": None,
            "response_time_ms": None,
            "dns_resolved": False,
            "port_open": False,
            "http_accessible": False
        }
        
        # 1. DNS解析检查
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self._base_url)
            hostname = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            
            # DNS解析
            start_time = time.time()
            ip_address = socket.gethostbyname(hostname)
            dns_time = time.time() - start_time
            
            result["dns_resolved"] = True
            result["dns_resolution_time_ms"] = round(dns_time * 1000, 2)
            result["resolved_ip"] = ip_address
            
            # 2. 端口检查
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                start_time = time.time()
                connection_result = sock.connect_ex((ip_address, port))
                port_time = time.time() - start_time
                sock.close()
                
                result["port_check_time_ms"] = round(port_time * 1000, 2)
                result["port_open"] = (connection_result == 0)
                
            except Exception as port_error:
                result["port_check_error"] = str(port_error)
                
        except socket.gaierror as dns_error:
            result["error_type"] = ConnectionErrorType.DNS_RESOLUTION_FAILED.value
            result["error_message"] = f"DNS解析失败: {dns_error}"
            return result
        except Exception as e:
            result["error_type"] = ConnectionErrorType.UNKNOWN.value
            result["error_message"] = f"连接检查失败: {e}"
            return result
            
        # 3. HTTP可访问性检查
        try:
            start_time = time.time()
            healthy, error_msg = self.health_check(force=True)
            http_time = time.time() - start_time
            
            result["response_time_ms"] = round(http_time * 1000, 2)
            result["http_accessible"] = healthy
            result["reachable"] = healthy
            
            if not healthy:
                result["error_message"] = error_msg
                result["error_type"] = ConnectionErrorType.HTTP_ERROR.value
                
        except Exception as http_error:
            result["error_type"] = ConnectionErrorType.UNKNOWN.value
            result["error_message"] = f"HTTP检查失败: {http_error}"
            
        return result
        
    # ------------------------------------------------------------------
    # HTTP方法（增强错误处理）
    # ------------------------------------------------------------------
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """发送GET请求"""
        return self._request("GET", path, params=params)
        
    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """发送POST请求"""
        return self._request("POST", path, json=json)
        
    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """发送HTTP请求（增强错误处理）"""
        url = f"{self._base_url}{path}"
        
        try:
            start_time = time.time()
            response = self._session.request(
                method, url, timeout=self._timeout, **kwargs
            )
            response_time = time.time() - start_time
            
            # 记录请求日志
            logger.debug(
                "HTTP %s %s - %d (%.2fms)",
                method, path, response.status_code, response_time * 1000
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as exc:
            error_type, error_msg = self._analyze_connection_error(exc, url)
            raise DetailedNetworkError(
                error_msg,
                error_type=error_type,
                url=url,
                original_exception=exc
            ) from exc
            
        except requests.exceptions.ConnectionError as exc:
            error_type, error_msg = self._analyze_connection_error(exc, url)
            raise DetailedNetworkError(
                error_msg,
                error_type=error_type,
                url=url,
                original_exception=exc
            ) from exc
            
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else 0
            try:
                detail = exc.response.json().get("detail", "") if exc.response else ""
            except Exception:
                detail = ""
                
            raise DetailedNetworkError(
                f"HTTP错误: {exc}",
                error_type=ConnectionErrorType.HTTP_ERROR,
                status_code=status_code,
                detail=detail,
                url=url,
                original_exception=exc
            ) from exc
            
        except Exception as exc:
            raise DetailedNetworkError(
                f"未知错误: {exc}",
                error_type=ConnectionErrorType.UNKNOWN,
                url=url,
                original_exception=exc
            ) from exc
            
    def _analyze_connection_error(
        self, 
        exception: Exception, 
        url: str
    ) -> Tuple[ConnectionErrorType, str]:
        """分析连接错误类型"""
        # 超时错误
        if isinstance(exception, requests.exceptions.Timeout):
            return ConnectionErrorType.TIMEOUT, f"请求超时 ({self._timeout}s): {url}"
            
        # 连接被拒绝
        if isinstance(exception, requests.exceptions.ConnectionError):
            # 检查是否是DNS解析失败
            if isinstance(exception.args[0], socket.gaierror):
                return ConnectionErrorType.DNS_RESOLUTION_FAILED, f"DNS解析失败: {url}"
                
            # 检查是否是连接被拒绝
            if "Connection refused" in str(exception):
                return ConnectionErrorType.CONNECTION_REFUSED, f"连接被拒绝: {url}"
                
            # 检查是否是网络不可达
            if "Network is unreachable" in str(exception):
                return ConnectionErrorType.NETWORK_UNREACHABLE, f"网络不可达: {url}"
                
            # 其他连接错误
            return ConnectionErrorType.CONNECTION_REFUSED, f"连接错误: {exception}"
            
        # SSL错误
        if "SSL" in str(exception) or "certificate" in str(exception):
            return ConnectionErrorType.SSL_ERROR, f"SSL错误: {exception}"
            
        # 未知错误
        return ConnectionErrorType.UNKNOWN, f"连接失败: {exception}"
        
    @staticmethod
    def _build_session(max_retries: int, backoff_factor: float) -> requests.Session:
        """构建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AHDUNYI-Terminal-PRO/9.1.0"
        })
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
        
    # ------------------------------------------------------------------
    # 属性访问器
    # ------------------------------------------------------------------
    
    @property
    def base_url(self) -> str:
        """获取基础URL"""
        return self._base_url
        
    @property
    def timeout(self) -> int:
        """获取超时时间"""
        return self._timeout
        
    @property
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self._token is not None


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def create_enhanced_network_client(
    base_url: str,
    timeout: int = 10,
    max_retries: int = 2,
    token: Optional[str] = None
) -> EnhancedNetworkClient:
    """
    创建增强版网络客户端
    
    Args:
        base_url: 服务器基础URL
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        token: 可选的Bearer token
        
    Returns:
        配置好的EnhancedNetworkClient实例
    """
    client = EnhancedNetworkClient(base_url, timeout=timeout, max_retries=max_retries)
    if token:
        client.set_token(token)
    return client


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def test_server_connectivity(server_url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    测试服务器连接性（独立函数）
    
    Args:
        server_url: 服务器URL
        timeout: 超时时间
        
    Returns:
        连接测试结果
    """
    client = EnhancedNetworkClient(server_url, timeout=timeout)
    return client.check_connectivity()


def format_connectivity_result(result: Dict[str, Any]) -> str:
    """
    格式化连接测试结果为可读字符串
    
    Args:
        result: check_connectivity()返回的结果
        
    Returns:
        格式化的字符串
    """
    lines = []
    lines.append(f"服务器: {result['server_url']}")
    lines.append(f"可达性: {'✅ 可达' if result['reachable'] else '❌ 不可达'}")
    
    if result['dns_resolved']:
        lines.append(f"DNS解析: ✅ 成功 ({result.get('resolved_ip', '未知')})")
        if 'dns_resolution_time_ms' in result:
            lines.append(f"DNS解析时间: {result['dns_resolution_time_ms']}ms")
    else:
        lines.append("DNS解析: ❌ 失败")
        
    if 'port_open' in result:
        lines.append(f"端口检查: {'✅ 开放' if result['port_open'] else '❌ 关闭'}")
        if 'port_check_time_ms' in result:
            lines.append(f"端口检查时间: {result['port_check_time_ms']}ms")
            
    if 'http_accessible' in result:
        lines.append(f"HTTP访问: {'✅ 成功' if result['http_accessible'] else '❌ 失败'}")
        if 'response_time_ms' in result:
            lines.append(f"响应时间: {result['response_time_ms']}ms")
            
    if result['error_message']:
        lines.append(f"错误信息: {result['error_message']}")
        
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试代码
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试连接性检查
    test_url = "http://122.51.72.36:8002"
    print(f"测试服务器连接性: {test_url}")
    
    result = test_server_connectivity(test_url)
    print(format_connectivity_result(result))