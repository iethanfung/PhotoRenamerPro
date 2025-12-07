import os
import sys
from datetime import datetime


class OperationLogger:
    """操作日志记录器 - 为每次批量操作创建独立的日志文件"""
    
    def __init__(self):
        """初始化日志记录器，获取日志目录"""
        # 获取日志文件的存储路径（与 app.log 同目录）
        if getattr(sys, 'frozen', False):
            # 打包后，日志存在可执行文件同级目录下
            self.log_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境 - operation_logger.py 在 src/utils/ 下，需要向上3层到达项目根目录
            # __file__ -> src/utils/operation_logger.py
            # dirname 1 -> src/utils
            # dirname 2 -> src
            # dirname 3 -> 项目根目录
            self.log_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        self.current_log_file = None
        self.log_handle = None
    
    def create_new_log_file(self):
        """创建新的操作日志文件（每次批量操作时调用）"""
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"operation_log_{timestamp}.log"
        log_path = os.path.join(self.log_dir, log_filename)
        
        # 打开日志文件（使用 utf-8 编码）
        self.current_log_file = log_path
        self.log_handle = open(log_path, 'w', encoding='utf-8')
        
        # 写入文件头
        self._write_header()
        
        return log_path
    
    def _write_header(self):
        """写入日志文件头部信息"""
        if not self.log_handle:
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""{'=' * 80}
Photo Renamer Pro - 操作日志
操作时间: {now}
{'=' * 80}

"""
        self.log_handle.write(header)
        self.log_handle.flush()
    
    def log_rename_success(self, original_path, target_path, parse_result):
        """
        记录成功的重命名操作
        
        Args:
            original_path: 原始文件完整路径
            target_path: 目标文件完整路径
            parse_result: 解析结果字典
        """
        if not self.log_handle:
            return
        
        original_name = os.path.basename(original_path)
        target_name = os.path.basename(target_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 提取关键解析信息
        rel_no = parse_result.get('rel_no', 'N/A')
        std_cp = parse_result.get('std_cp', 'N/A')
        detail = parse_result.get('detail', 'N/A')
        photo_type = parse_result.get('type', 'Unknown')
        test = parse_result.get('unit_data', {}).get('Test', 'N/A')
        
        log_entry = f"""✅ [重命名成功] {now}
   原文件: {original_name}
   原位置: {original_path}
   新文件: {target_name}
   新位置: {target_path}
   解析信息: CP={std_cp} | 机台号={rel_no} | Test={test} | Detail={detail} | Type={photo_type}

"""
        self.log_handle.write(log_entry)
        self.log_handle.flush()
    
    def log_operation_skip(self, original_path, target_path, reason):
        """
        记录跳过的操作
        
        Args:
            original_path: 原始文件路径
            target_path: 目标文件路径
            reason: 跳过原因
        """
        if not self.log_handle:
            return
        
        original_name = os.path.basename(original_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"""⚠️ [操作跳过] {now}
   原文件: {original_name}
   原位置: {original_path}
   目标位置: {target_path}
   跳过原因: {reason}

"""
        self.log_handle.write(log_entry)
        self.log_handle.flush()
    
    def log_operation_error(self, original_path, error_message):
        """
        记录操作失败
        
        Args:
            original_path: 原始文件路径
            error_message: 错误信息
        """
        if not self.log_handle:
            return
        
        original_name = os.path.basename(original_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"""❌ [操作失败] {now}
   原文件: {original_name}
   原位置: {original_path}
   错误信息: {error_message}

"""
        self.log_handle.write(log_entry)
        self.log_handle.flush()
    
    def log_parse_failure(self, file_path, reason, status_msg):
        """
        记录解析失败的图片（未就绪的图片）
        
        Args:
            file_path: 文件路径
            reason: 失败原因
            status_msg: 状态消息
        """
        if not self.log_handle:
            return
        
        filename = os.path.basename(file_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"""⚪ [解析未就绪] {now}
   文件名: {filename}
   位置: {file_path}
   状态: {status_msg}
   原因: {reason}
   建议: 请检查文件名格式或手动修正后重试

"""
        self.log_handle.write(log_entry)
        self.log_handle.flush()
    
    def write_summary(self, total_count, success_count, skip_count, error_count, unready_count):
        """
        写入操作汇总信息
        
        Args:
            total_count: 总文件数
            success_count: 成功数量
            skip_count: 跳过数量
            error_count: 错误数量
            unready_count: 未就绪数量
        """
        if not self.log_handle:
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary = f"""{'=' * 80}
操作汇总 ({now})
{'=' * 80}
总计图片数: {total_count}
✅ 成功处理: {success_count}
⚠️ 跳过操作: {skip_count}
❌ 操作失败: {error_count}
⚪ 未就绪项: {unready_count}
{'=' * 80}
"""
        self.log_handle.write(summary)
        self.log_handle.flush()
    
    def close(self):
        """关闭日志文件"""
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None
            self.current_log_file = None


# 创建全局单例
_logger_instance = None

def get_operation_logger():
    """获取操作日志记录器的单例实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = OperationLogger()
    return _logger_instance
