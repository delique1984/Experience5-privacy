from flask import Flask, jsonify
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, API_PREFIX
from extensions import db,ma
from flask_cors import CORS  # 导入 CORS
def create_app():
    # 创建 Flask 应用实例
    app = Flask(__name__)

    # 配置数据库
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

    # 初始化数据库
    db.init_app(app)
    ma.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    # 注册路由
    from routes import register_blueprints
    register_blueprints(app, api_prefix="/api/v1")

    # 主页路由
    # @app.route("/")
    # def index():
    #     return jsonify({"msg": "Data Platform API", "version": "v1"}), 200
    #
    # return app

    @app.route("/")
    def index():
        return jsonify({
            "name": "Privacy Protection Data Platform",
            "version": "v1.0",
            "description": "基于Flask的隐私数据保护平台",
            "features": [
                "数据脱敏 (Data Masking)",
                "K-匿名处理 (K-Anonymity)",
                "差分隐私 (Differential Privacy)"
            ],
            "endpoints": {
                "data_masking": f"{API_PREFIX}/privacy/masking",
                "k_anonymity": f"{API_PREFIX}/privacy/k-anonymity",
                "differential_privacy": f"{API_PREFIX}/privacy/differential-privacy",
                "logs": f"{API_PREFIX}/privacy/logs"
            }
        }), 200

    # 健康检查
    @app.route("/health")
    def health():
        try:
            # 测试数据库连接
            db.session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        return jsonify({
            "status": "running",
            "database": db_status
        }), 200

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "code": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "internal server error"
        }), 500

    return app


if __name__ == "__main__":
    app = create_app()

    # 创建数据库表
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

    # 运行应用
    app.run(host="0.0.0.0", port=5000, debug=True)