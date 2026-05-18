import os
import tempfile
import textwrap
import unittest
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

from integrated_qa_system.base.config import Config
from integrated_qa_system.base.path_utils import resolve_relative_path


def _load_users_module():
    module_path = Path(__file__).resolve().parents[1] / "Backend" / "app" / "db" / "users.py"
    spec = importlib.util.spec_from_file_location("backend_users_for_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    fake_pymysql = types.ModuleType("pymysql")
    fake_pymysql.Connection = object
    fake_passlib = types.ModuleType("passlib")
    fake_passlib_context = types.ModuleType("passlib.context")

    class _FakeCryptContext:
        def __init__(self, *args, **kwargs):
            pass

    fake_passlib_context.CryptContext = _FakeCryptContext

    with patch.dict(
        sys.modules,
        {
            "pymysql": fake_pymysql,
            "passlib": fake_passlib,
            "passlib.context": fake_passlib_context,
        },
        clear=False,
    ):
        spec.loader.exec_module(module)
    return module


class ContainerConfigTests(unittest.TestCase):
    def test_env_values_override_config_file(self):
        config_text = textwrap.dedent(
            """
            [mysql]
            host = file-mysql
            port = 3306
            user = file-user
            password = file-password
            database = file-db

            [redis]
            host = file-redis
            port = 6379
            password = file-redis-password
            db = 0

            [milvus]
            host = file-milvus
            port = 19530
            database_name = file-milvus-db
            collection_name = file-collection

            [llm]
            model = file-model
            dashscope_api_key = file-key
            dashscope_base_url = https://example.com/v1

            [retrieval]
            parent_chunk_size = 1200
            child_chunk_size = 300
            chunk_overlap = 50
            retrieval_k = 10
            candidate_m = 3

            [app]
            valid_sources = ["ai"]
            customer_service_phone = 12345678
            """
        )

        with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(config_text)
            config_path = temp_file.name

        try:
            with patch.dict(
                os.environ,
                {
                    "MYSQL_HOST": "docker-mysql",
                    "MYSQL_PORT": "3307",
                    "REDIS_HOST": "docker-redis",
                    "MILVUS_HOST": "docker-milvus",
                    "MILVUS_DATABASE_NAME": "default",
                    "DASHSCOPE_API_KEY": "env-key",
                },
                clear=False,
            ):
                conf = Config(config_file=config_path)

            self.assertEqual(conf.MYSQL_HOST, "docker-mysql")
            self.assertEqual(conf.MYSQL_PORT, 3307)
            self.assertEqual(conf.REDIS_HOST, "docker-redis")
            self.assertEqual(conf.MILVUS_HOST, "docker-milvus")
            self.assertEqual(conf.MILVUS_DATABASE_NAME, "default")
            self.assertEqual(conf.DASHSCOPE_API_KEY, "env-key")
        finally:
            os.unlink(config_path)

    def test_backend_user_settings_read_mysql_port_from_env(self):
        with patch.dict(
            os.environ,
            {
                "MYSQL_HOST": "mysql",
                "MYSQL_PORT": "3308",
                "MYSQL_USER": "root",
                "MYSQL_PASSWORD": "secret",
                "MYSQL_DATABASE": "rag_item",
            },
            clear=False,
        ):
            settings = _load_users_module().load_mysql_settings()

        self.assertEqual(settings.host, "mysql")
        self.assertEqual(settings.port, 3308)
        self.assertEqual(settings.user, "root")
        self.assertEqual(settings.password, "secret")
        self.assertEqual(settings.database, "rag_item")

    def test_resolve_relative_path_handles_relative_and_absolute_inputs(self):
        base_dir = os.path.join("app", "integrated_qa_system", "rag_qa")
        relative = resolve_relative_path(base_dir, "../models/bert_query_classifier")
        absolute = resolve_relative_path(base_dir, "/app/integrated_qa_system/rag_qa/models/bert_query_classifier")

        self.assertEqual(
            relative,
            os.path.normpath(os.path.join(base_dir, "..", "models", "bert_query_classifier")),
        )
        self.assertEqual(
            absolute,
            os.path.normpath("/app/integrated_qa_system/rag_qa/models/bert_query_classifier"),
        )


if __name__ == "__main__":
    unittest.main()
