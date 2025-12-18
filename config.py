# config.py
import os

# 从环境变量读取 DB 配置，方便上线/本地换配置
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "zzy050706")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "pro")

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False

# API 前缀（可统一）
API_PREFIX = "/api/v1"

# 隐私保护配置
PRIVACY_CONFIG = {
    # 数据脱敏配置
    "masking": {
        "phone_mask_char": "*",  # 手机号脱敏字符
        "email_mask_char": "*",  # 邮箱脱敏字符
        "id_card_mask_char": "*",  # 身份证脱敏字符
        "keep_first": 3,  # 保留前几位
        "keep_last": 4,  # 保留后几位
    },

    # K-匿名配置
    "k_anonymity": {
        "default_k": 5,  # 默认 K 值
        "max_k": 100,  # 最大 K 值
        "quasi_identifiers": [  # 准标识符字段
            "age", "region", "job"
        ],
        "sensitive_attributes": [  # 敏感属性
            "inventor", "first_inventor"
        ]
    },

    # 差分隐私配置
    "differential_privacy": {
        "default_epsilon": 1.0,  # 默认隐私预算
        "min_epsilon": 0.1,  # 最小隐私预算
        "max_epsilon": 10.0,  # 最大隐私预算
        "sensitivity": 1.0,  # 全局敏感度
        "noise_mechanism": "laplace"  # 噪声机制: laplace 或 gaussian
    }
}

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "privacy_platform.log"