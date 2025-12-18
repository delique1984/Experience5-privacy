from datetime import datetime
from extensions import db


class NRSE(db.Model):
    __tablename__ = "NRSE"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键 ID

    enterprise_id = db.Column(db.String(64), nullable=False, index=True)  # 企业ID（如 ENT_001）
    enterprise_name = db.Column(db.String(256), nullable=False)  # 企业名称
    chain_stage = db.Column(db.String(128), nullable=True)  # 产业链环节（如 上游-原材料）
    main_products = db.Column(db.Text, nullable=True)  # 主要产品/服务
    revenue_2023 = db.Column(db.Float, nullable=True)  # 2023年预估营收(亿元)
    domestic_market_share = db.Column(db.Float, nullable=True)  # 国内市场份额(%)
    core_customers = db.Column(db.Text, nullable=True)  # 核心客户（多个用逗号拼接）
    r_and_d_ratio = db.Column(db.Float, nullable=True)  # 研发投入占比(%)
    key_technologies = db.Column(db.Text, nullable=True)  # 关键技术布局
    headquarters = db.Column(db.String(128), nullable=True)  # 总部所在地
    sensitivity_level = db.Column(db.String(64), nullable=True)  # 敏感等级（如 高/中/低）
    data_source = db.Column(db.String(128), nullable=True)  # 数据来源标签（如 行业报告）

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # 创建时间

    def __repr__(self):
        return f"<Enterprise {self.enterprise_id} {self.enterprise_name}>"
