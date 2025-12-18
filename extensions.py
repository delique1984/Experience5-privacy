"""
Flask 扩展初始化
"""
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# 初始化扩展（不绑定到app）
db = SQLAlchemy()
ma = Marshmallow()