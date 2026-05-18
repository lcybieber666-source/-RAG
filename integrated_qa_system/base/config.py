# base/config.py
# 导入配置解析库
# TODO python自带的，用于解析配置文件的包
import configparser
import os


class Config:
    # 初始化配置，加载 config.ini 文件
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "config.ini"))
        # 创建配置解析器
        self.config = configparser.ConfigParser()
        # 读取配置文件，指定UTF-8编码
        self.config.read(config_file, encoding='utf-8')

        def env_or_config(env_name, section, option, fallback=None):
            value = os.getenv(env_name)
            if value is not None:
                return value
            return self.config.get(section, option, fallback=fallback)

        def env_or_config_int(env_name, section, option, fallback=None):
            value = os.getenv(env_name)
            if value is not None:
                return int(value)
            return self.config.getint(section, option, fallback=fallback)

        # MySQL 配置
        # MySQL 主机地址
        # TODO config.get('mysql', 'host', fallback='localhost')
        # TODO mysql -> [mysql] ,  host -> host = localhost ,  fallback 默认值
        self.MYSQL_HOST = env_or_config('MYSQL_HOST', 'mysql', 'host', fallback='localhost')
        # MySQL 端口
        self.MYSQL_PORT = env_or_config_int('MYSQL_PORT', 'mysql', 'port', fallback=3306)
        # MySQL 用户名
        self.MYSQL_USER = env_or_config('MYSQL_USER', 'mysql', 'user', fallback='root')
        # MySQL 密码
        self.MYSQL_PASSWORD = env_or_config('MYSQL_PASSWORD', 'mysql', 'password', fallback='root')
        # MySQL 数据库名
        self.MYSQL_DATABASE = env_or_config('MYSQL_DATABASE', 'mysql', 'database', fallback='rag_item')

        # Redis 配置
        # Redis 主机地址
        self.REDIS_HOST = env_or_config('REDIS_HOST', 'redis', 'host', fallback='localhost')
        # Redis 端口
        self.REDIS_PORT = env_or_config_int('REDIS_PORT', 'redis', 'port', fallback=6379)
        # Redis 密码
        self.REDIS_PASSWORD = env_or_config('REDIS_PASSWORD', 'redis', 'password', fallback='1234')
        # Redis 数据库编号
        self.REDIS_DB = env_or_config_int('REDIS_DB', 'redis', 'db', fallback=0)
        # 日志文件路径
        self.LOG_FILE = os.getenv('LOG_FILE') or self.config.get('logger', 'log_file', fallback='logs/edu_rag.logs')

        # Milvus 配置
        # Milvus 主机地址
        self.MILVUS_HOST = env_or_config('MILVUS_HOST', 'milvus', 'host', fallback='localhost')
        # Milvus 端口
        self.MILVUS_PORT = env_or_config('MILVUS_PORT', 'milvus', 'port', fallback='19530')
        # Milvus 数据库名
        self.MILVUS_DATABASE_NAME = env_or_config('MILVUS_DATABASE_NAME', 'milvus', 'database_name', fallback='itcast')
        # Milvus 集合名
        self.MILVUS_COLLECTION_NAME = env_or_config('MILVUS_COLLECTION_NAME', 'milvus', 'collection_name', fallback='edurag_final')

        # LLM 配置
        # LLM 模型名
        self.LLM_MODEL = env_or_config('LLM_MODEL', 'llm', 'model', fallback='qwen3-max')
        # DashScope API 密钥
        self.DASHSCOPE_API_KEY = env_or_config('DASHSCOPE_API_KEY', 'llm', 'dashscope_api_key', fallback='')
        # DashScope API 地址
        self.DASHSCOPE_BASE_URL = env_or_config(
            'DASHSCOPE_BASE_URL',
            'llm',
            'dashscope_base_url',
            fallback='https://dashscope.aliyuncs.com/compatible-mode/v1',
        )

        # 检索参数
        # 父块大小
        self.PARENT_CHUNK_SIZE = self.config.getint('retrieval', 'parent_chunk_size', fallback=1200)
        # 子块大小
        self.CHILD_CHUNK_SIZE = self.config.getint('retrieval', 'child_chunk_size', fallback=300)
        # 块重叠大小
        self.CHUNK_OVERLAP = self.config.getint('retrieval', 'chunk_overlap', fallback=50)
        # 检索返回数量
        self.RETRIEVAL_K = self.config.getint('retrieval', 'retrieval_k', fallback=5)
        # 最终候选数量
        self.CANDIDATE_M = self.config.getint('retrieval', 'candidate_m', fallback=2)

        # 应用配置
        # 有效来源列表
        self.VALID_SOURCES = eval(
            self.config.get('app', 'valid_sources', fallback='["ai", "java", "test", "ops", "bigdata"]'))
        # 客服电话
        self.CUSTOMER_SERVICE_PHONE = self.config.get('app', 'customer_service_phone', fallback='12345678')
        # 日志文件路径
        self.LOG_FILE = os.getenv('LOG_FILE') or self.config.get('logger', 'log_file', fallback='logs/edu_rag.log')

single_config = Config()
conf = Config()

if __name__ == '__main__':
    conf = Config()
    print(conf.MYSQL_USER)
    print(conf.MILVUS_COLLECTION_NAME)
