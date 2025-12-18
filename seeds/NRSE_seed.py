import pandas as pd
from app import create_app, db
from models import NRSE
from datetime import datetime

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created!")


def safe_get(row, col_name, default=None):
    """
    安全获取 DataFrame 某列的值
    - 如果列不存在返回 default
    - 如果是 NaN 返回 None
    """
    if col_name not in row:
        return default
    val = row[col_name]
    if pd.isna(val):
        return None
    return val


def import_enterprises_from_csv(file_path):
    with app.app_context():
        print(f"读取 CSV 文件: {file_path} ...")

        # 自动识别编码并读取
        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            # 有些 CSV 可能是 gbk 编码
            df = pd.read_csv(file_path, encoding='gbk')

        print(f"数据预览:\n{df.head()}\n")
        print(f"开始插入 {len(df)} 条企业数据...\n")

        for _, row in df.iterrows():

            # 安全 float 解析（避免字符串等导致报错）
            def safe_float(v):
                if pd.isna(v):
                    return None
                try:
                    return float(v)
                except:
                    return None

            enterprise = NRSE(
                enterprise_id=safe_get(row, '企业ID'),
                enterprise_name=safe_get(row, '企业名称'),
                chain_stage=safe_get(row, '产业链环节'),
                main_products=safe_get(row, '主要产品/服务'),
                revenue_2023=safe_float(safe_get(row, '2023年预估营收(亿元)')),
                domestic_market_share=safe_float(safe_get(row, '国内市场份额(%)')),
                core_customers=safe_get(row, '核心客户'),
                r_and_d_ratio=safe_float(safe_get(row, '研发投入占比(%)')),
                key_technologies=safe_get(row, '关键技术布局'),
                headquarters=safe_get(row, '总部所在地'),
                sensitivity_level=safe_get(row, '敏感等级'),
                data_source=safe_get(row, '数据来源标签')
            )

            db.session.add(enterprise)

        db.session.commit()
        print(f"插入完成，共插入 {len(df)} 条企业数据。")


if __name__ == "__main__":
    file_path = '../industry.csv'  # 替换成你的 CSV 路径
    import_enterprises_from_csv(file_path)
