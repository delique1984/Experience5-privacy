from flask import Blueprint

# 导入各个模块的蓝图
from .patent_routes import bp as patent_bp
from .nrse_routes import bp as nrse_bp
# 可以选择：导出所有蓝图的列表
blueprints = [
    patent_bp,
    nrse_bp
]

# 或者创建一个主蓝图，将其他蓝图注册到主蓝图下
def register_blueprints(app, api_prefix="/api/v1"):
    """注册所有蓝图到 Flask 应用"""
    for bp in blueprints:
        full_prefix = api_prefix + (bp.url_prefix or "")
        app.register_blueprint(bp, url_prefix=full_prefix)