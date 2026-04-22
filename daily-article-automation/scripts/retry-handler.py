#!/usr/bin/env python3
"""
Retry Handler - 重试处理脚本

处理失败任务的重试逻辑
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        delay_seconds: int = 60,
        exponential_backoff: bool = True,
        max_delay_seconds: int = 600
    ):
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self.exponential_backoff = exponential_backoff
        self.max_delay_seconds = max_delay_seconds


class RetryHandler:
    """重试处理器"""

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.retry_log: list[dict] = []

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        on_retry: Callable[[int, Exception], None] = None,
        on_success: Callable[[Any], None] = None,
        on_failure: Callable[[Exception], None] = None,
        **kwargs
    ) -> tuple[bool, Any]:
        """
        执行函数并重试

        Args:
            func: 要执行的函数
            args: 位置参数
            on_retry: 重试回调 (attempt, exception)
            on_success: 成功回调 (result)
            on_failure: 失败回调 (exception)
            kwargs: 关键字参数

        Returns:
            (success, result_or_none)
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.info(f"执行尝试 {attempt}/{self.config.max_attempts}")

                result = func(*args, **kwargs)

                # 成功
                if on_success:
                    on_success(result)

                self.retry_log.append({
                    "func": func.__name__,
                    "attempts": attempt,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                })

                return True, result

            except Exception as e:
                last_exception = e
                logger.error(f"尝试 {attempt} 失败：{e}")

                # 重试回调
                if on_retry:
                    on_retry(attempt, e)

                self.retry_log.append({
                    "func": func.__name__,
                    "attempt": attempt,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

                # 如果还有重试机会，等待一段时间
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)

        # 所有重试失败
        if on_failure:
            on_failure(last_exception)

        return False, None

    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟时间（支持指数退避）"""
        if self.config.exponential_backoff:
            # 指数退避：delay * 2^(attempt-1)
            delay = self.config.delay_seconds * (2 ** (attempt - 1))
        else:
            delay = self.config.delay_seconds

        return min(delay, self.config.max_delay_seconds)

    def get_retry_log(self) -> list[dict]:
        """获取重试日志"""
        return self.retry_log

    def save_retry_log(self, log_path: str = None) -> str:
        """保存重试日志到文件"""
        if log_path is None:
            log_path = f"retry_log_{datetime.now().strftime('%Y%m%d')}.json"

        import json
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.retry_log, f, ensure_ascii=False, indent=2)

        logger.info(f"Retry log saved to: {log_path}")
        return log_path


def retry_decorator(
    max_attempts: int = 3,
    delay_seconds: int = 60,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器

    Usage:
        @retry_decorator(max_attempts=3, delay_seconds=60)
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            handler = RetryHandler(RetryConfig(
                max_attempts=max_attempts,
                delay_seconds=delay_seconds
            ))

            success, result = handler.execute_with_retry(
                func, *args, **kwargs,
                exceptions=exceptions
            )

            if not success:
                raise handler.retry_log[-1].get("error", "Unknown error")

            return result

        return wrapper
    return decorator


def main():
    """测试重试功能"""
    import argparse

    parser = argparse.ArgumentParser(description="重试处理器测试")
    parser.add_argument("--fail-times", type=int, default=2,
                        help="失败次数")
    parser.add_argument("--log-path", help="日志保存路径")

    args = parser.parse_args()

    fail_count = [0]

    def flaky_function():
        fail_count[0] += 1
        if fail_count[0] <= args.fail_times:
            raise ValueError(f"故意失败 (第{fail_count[0]}次)")
        return "Success!"

    handler = RetryHandler()

    success, result = handler.execute_with_retry(
        flaky_function,
        on_retry=lambda attempt, e: print(f"  重试回调：attempt={attempt}, error={e}"),
        on_success=lambda r: print(f"  成功回调：{r}"),
        on_failure=lambda e: print(f"  失败回调：{e}")
    )

    print(f"\n结果：success={success}, result={result}")

    if args.log_path:
        handler.save_retry_log(args.log_path)


if __name__ == "__main__":
    main()
