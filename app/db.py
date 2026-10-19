
import os

from dotenv import load_dotenv
from pymongo import MongoClient

# 加载项目根目录中的 .env 配置
load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017",
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "survey_system",
)

# 创建 MongoDB 客户端
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
)

# 选择本项目专用数据库
db = client[MONGO_DB_NAME]


def test_connection():
    """检查 MongoDB 是否能够连接。"""
    client.admin.command("ping")
    return True
