import logging
import os

from integrated_qa_system.base.path_utils import get_project_root

# 获取当前文件所在目录的绝对路径
this_dir = os.getenv("LOG_FILE") or os.path.join(get_project_root(), 'integrated_qa_system', 'logs', 'edu-rag.log')


def setup_logger(name='edu-rag', log_file=this_dir):
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置最低级别

    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 定义日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(filename)s - Line:%(lineno)d - %(message)s')

        # 设置处理器格式
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加处理器（避免重复添加）
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


single_logger = setup_logger('edu-rag')
