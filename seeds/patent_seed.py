import pandas as pd
from app import create_app, db
from models.patent import Patent
from datetime import datetime

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created!")

def safe_get(row, col_name, default=None):
    """
    安全获取 DataFrame 某列的值
    - 如果列不存在返回 default
    - 如果是 NaT/NaN 返回 None
    """
    if col_name not in row:
        return default
    val = row[col_name]
    if pd.isna(val):
        return None
    return val

def import_patents_from_excel(file_path, sheet_name='Sheet2'):
    with app.app_context():
        print(f"读取 Excel 文件中的工作表: {sheet_name} ...")
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        print(f"数据预览:\n{df.head()}")

        # 遍历每行数据并插入数据库
        print(f"开始插入 {len(df)} 条专利数据...")

        for _, row in df.iterrows():
            grant_date_raw = safe_get(row, '授权日')
            grant_date = pd.to_datetime(grant_date_raw, errors='coerce')
            if pd.isna(grant_date):
                grant_date = None
            patent = Patent(
                publication_number=safe_get(row, '公开(公告)号'),
                title=safe_get(row, '标题(译)(简体中文)'),
                abstract=safe_get(row, '摘要(译)(简体中文)'),
                priority_country=safe_get(row, '优先权国家/地区'),
                current_applicant=safe_get(row, '[标]当前申请(专利权)人'),
                original_applicant=safe_get(row, '[标]原始申请(专利权)人'),
                inventor=safe_get(row, '发明人'),
                first_inventor=safe_get(row, '第一发明人'),
                simple_family=safe_get(row, '简单同族'),
                simple_family_number=safe_get(row, '简单同族编号'),
                grant_date=grant_date,  # NaT 自动转 None
                cited_patent=safe_get(row, '被引用专利'),
                cited_patent_count=safe_get(row, '被引用专利数量'),
                citing_patent=safe_get(row, '引用专利'),
                citing_patent_count=safe_get(row, '引用专利数量'),
                ipc_classification=safe_get(row, 'IPC主分类号'),
                first_inventor_address=safe_get(row, '第一发明人地址'),
                region=safe_get(row, '地区'),
                topic_label=safe_get(row, 'Topic_Label')
            )

            db.session.add(patent)

        db.session.commit()
        print(f"插入完成，共插入 {len(df)} 条专利数据。")

if __name__ == "__main__":
    file_path = 'data.clean_patents1_with_topics.XLSX'  # 替换为你的 Excel 文件路径
    import_patents_from_excel(file_path, sheet_name='clear')  # 指定工作表
