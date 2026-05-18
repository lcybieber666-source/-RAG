import configparser
import os
from dataclasses import dataclass
from typing import Optional, Tuple

import pymysql
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class MySQLSettings:
    host: str
    port: int
    user: str
    password: str
    database: str


def load_mysql_settings() -> MySQLSettings:
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "integrated_qa_system", "config.ini")
    )
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")

    host = os.getenv("MYSQL_HOST") or parser.get("mysql", "host", fallback="localhost")
    port = int(os.getenv("MYSQL_PORT") or parser.get("mysql", "port", fallback="3306"))
    user = os.getenv("MYSQL_USER") or parser.get("mysql", "user", fallback="root")
    password = os.getenv("MYSQL_PASSWORD") or parser.get("mysql", "password", fallback="root")
    database = os.getenv("MYSQL_DATABASE") or parser.get("mysql", "database", fallback="rag_item")

    return MySQLSettings(host=host, port=port, user=user, password=password, database=database)


def _connect_admin(settings: MySQLSettings) -> pymysql.Connection:
    return pymysql.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        charset="utf8mb4",
        autocommit=True,
    )


def _connect_db(settings: MySQLSettings) -> pymysql.Connection:
    return pymysql.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        db=settings.database,
        charset="utf8mb4",
        autocommit=True,
    )


def init_users_table(settings: Optional[MySQLSettings] = None) -> None:
    settings = settings or load_mysql_settings()
    connection = _connect_admin(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(f"USE `{settings.database}`")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
    finally:
        connection.close()


def _fetch_user_row_by_username(connection: pymysql.Connection, username: str) -> Optional[Tuple[int, str, str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s LIMIT 1",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return int(row[0]), str(row[1]), str(row[2])


def create_user(username: str, password: str) -> Optional[int]:
    settings = load_mysql_settings()
    init_users_table(settings)
    password_hash = _pwd_context.hash(password)

    connection = _connect_db(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
            return int(cursor.lastrowid)
    except pymysql.IntegrityError:
        return None
    finally:
        connection.close()


def verify_user(username: str, password: str) -> bool:
    settings = load_mysql_settings()
    connection = _connect_db(settings)
    try:
        row = _fetch_user_row_by_username(connection, username)
        if not row:
            return False
        return _pwd_context.verify(password, row[2])
    finally:
        connection.close()


def get_user_by_username(username: str) -> Optional[Tuple[int, str]]:
    settings = load_mysql_settings()
    connection = _connect_db(settings)
    try:
        row = _fetch_user_row_by_username(connection, username)
        if not row:
            return None
        return row[0], row[1]
    finally:
        connection.close()
