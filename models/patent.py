# models.py
# 使用 Marshmallow 定义数据结构和字段校验规则
# 它让你的 API 自动检查输入是否合法，并把 Python 对象变成 JSON 格式。
from datetime import datetime
from extensions import db


# real
class Patent(db.Model):
    __tablename__ = "patents"  # 表名，使用复数形式通常是数据库规范

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键id，自动递增
    publication_number = db.Column(db.String(64), nullable=False, index=True)  # 公告号
    title = db.Column(db.Text, nullable=False)  # 标题，改为 Text，避免超长
    abstract = db.Column(db.Text, nullable=False)  # 摘要
    priority_country = db.Column(db.Text, nullable=True)  # 优先权国家/地区
    current_applicant = db.Column(db.Text, nullable=True)  # 当前申请人，改为 Text
    original_applicant = db.Column(db.Text, nullable=True)  # 原始申请人，改为 Text
    inventor = db.Column(db.Text, nullable=True)  # 发明人，改为 Text
    first_inventor = db.Column(db.String(256), nullable=True)  # 第一发明人
    simple_family = db.Column(db.Text, nullable=True)  # 简单同族，改为 Text
    simple_family_number = db.Column(db.String(256), nullable=True)  # 简单同族编号
    grant_date = db.Column(db.Date, nullable=True)  # 授权日期
    cited_patent = db.Column(db.Text, nullable=True)  # 被引用专利，改为 Text
    cited_patent_count = db.Column(db.Integer, nullable=True)  # 被引用专利数量
    citing_patent = db.Column(db.Text, nullable=True)  # 引用专利，改为 Text
    citing_patent_count = db.Column(db.Integer, nullable=True)  # 引用专利数量
    ipc_classification = db.Column(db.String(64), nullable=True)  # IPC 主分类号
    first_inventor_address = db.Column(db.String(256), nullable=True)  # 第一发明人地址
    region = db.Column(db.String(64), nullable=True)  # 地区
    topic_label = db.Column(db.Text, nullable=True)  # Topic Label，改为 Text

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # 创建时间

    def __repr__(self):
        return f"<Patent {self.id} {self.title}>"
