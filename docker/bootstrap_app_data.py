import csv
import logging
import os
import time

import pymysql
import redis
from pymilvus import MilvusClient

from integrated_qa_system.base.config import single_config as config
from integrated_qa_system.rag_qa.core import document_processor
from integrated_qa_system.rag_qa.core.vector_store import VectorStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
LOGGER = logging.getLogger("bootstrap")

FAQ_CSV_PATH = os.getenv(
    "FAQ_CSV_PATH",
    os.path.join("integrated_qa_system", "mysql_qa", "data", "药物配伍禁忌问答.csv"),
)
RAG_DATA_DIR = os.getenv(
    "RAG_DATA_DIR",
    os.path.join("integrated_qa_system", "rag_qa", "data", "ai_data"),
)
BOOTSTRAP_FAQ = (os.getenv("BOOTSTRAP_FAQ") or "true").lower() in {"1", "true", "yes"}
BOOTSTRAP_VECTOR_DATA = (os.getenv("BOOTSTRAP_VECTOR_DATA") or "true").lower() in {"1", "true", "yes"}


def _wait_for_mysql(max_attempts=60, delay_seconds=5):
    for attempt in range(1, max_attempts + 1):
        try:
            connection = pymysql.connect(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                charset="utf8mb4",
                connect_timeout=5,
                autocommit=True,
            )
            connection.close()
            LOGGER.info("MySQL is ready")
            return
        except Exception as exc:
            LOGGER.info("Waiting for MySQL (%s/%s): %s", attempt, max_attempts, exc)
            time.sleep(delay_seconds)
    raise RuntimeError("MySQL did not become ready in time")


def _wait_for_redis(max_attempts=60, delay_seconds=5):
    client = redis.StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSWORD,
        db=config.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    for attempt in range(1, max_attempts + 1):
        try:
            client.ping()
            LOGGER.info("Redis is ready")
            return
        except Exception as exc:
            LOGGER.info("Waiting for Redis (%s/%s): %s", attempt, max_attempts, exc)
            time.sleep(delay_seconds)
    raise RuntimeError("Redis did not become ready in time")


def _wait_for_milvus(max_attempts=60, delay_seconds=10):
    for attempt in range(1, max_attempts + 1):
        try:
            client = MilvusClient(
                uri=f"http://{config.MILVUS_HOST}:{config.MILVUS_PORT}",
                db_name=config.MILVUS_DATABASE_NAME,
            )
            client.list_collections()
            LOGGER.info("Milvus is ready")
            return
        except Exception as exc:
            LOGGER.info("Waiting for Milvus (%s/%s): %s", attempt, max_attempts, exc)
            time.sleep(delay_seconds)
    raise RuntimeError("Milvus did not become ready in time")


def _seed_mysql_faq():
    connection = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(f"USE `{config.MYSQL_DATABASE}`")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jpkb (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    subject_name VARCHAR(20),
                    question VARCHAR(1000),
                    answer VARCHAR(1000)
                )
                """
            )
            cursor.execute("SELECT COUNT(*) FROM jpkb")
            row_count = int(cursor.fetchone()[0])
            if row_count > 0:
                LOGGER.info("FAQ table already contains %s rows, skipping CSV import", row_count)
                return

            if not os.path.exists(FAQ_CSV_PATH):
                raise FileNotFoundError(f"FAQ CSV not found: {FAQ_CSV_PATH}")

            with open(FAQ_CSV_PATH, "r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                rows = [
                    (
                        row.get("类别", "").strip(),
                        row.get("问题", "").strip(),
                        row.get("答案", "").strip(),
                    )
                    for row in reader
                    if row.get("问题") and row.get("答案")
                ]

            cursor.executemany(
                "INSERT INTO jpkb (subject_name, question, answer) VALUES (%s, %s, %s)",
                rows,
            )
            LOGGER.info("Imported %s FAQ rows into MySQL", len(rows))
    finally:
        connection.close()


def _get_collection_row_count(store: VectorStore) -> int:
    try:
        stats = store.client.get_collection_stats(collection_name=store.collection_name)
        return int(stats.get("row_count", 0))
    except Exception as exc:
        LOGGER.warning("Unable to read Milvus collection stats: %s", exc)
        return 0


def _seed_milvus_vector_data(store: VectorStore):
    row_count = _get_collection_row_count(store)
    if row_count > 0:
        LOGGER.info("Milvus collection %s already contains %s rows, skipping bootstrap", store.collection_name, row_count)
        return

    if not os.path.isdir(RAG_DATA_DIR):
        raise FileNotFoundError(f"RAG data directory not found: {RAG_DATA_DIR}")

    documents = document_processor.process_documents(RAG_DATA_DIR)
    if not documents:
        raise RuntimeError("No documents were produced for Milvus bootstrap")

    store.add_documents(documents)
    LOGGER.info("Indexed %s document chunks into Milvus", len(documents))


def main():
    _wait_for_mysql()
    _wait_for_redis()

    if BOOTSTRAP_FAQ:
        _seed_mysql_faq()
    else:
        LOGGER.info("Skipping FAQ bootstrap")

    if BOOTSTRAP_VECTOR_DATA:
        _wait_for_milvus()
        store = VectorStore()
        _seed_milvus_vector_data(store)
    else:
        LOGGER.info("Skipping Milvus bootstrap")

    LOGGER.info("Bootstrap completed")


if __name__ == "__main__":
    main()
