# service_nrse_specific.py

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
from faker import Faker
import random
import pandas as pd  # 新增：用于处理表格数据
import os  # 新增：用于路径管理

# 初始化 Faker，使用中文语料
fake = Faker('zh_CN')

# === 新增配置：CSV 保存路径 ===
OUTPUT_DIR = "generated_data_rule"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

router = APIRouter(prefix="/nrse", tags=["NRSE Data Synthesis"])


# 定义响应的 Pydantic 模型
class NRSEDataModel(BaseModel):
    id: int
    enterprise_id: str
    enterprise_name: str
    chain_stage: str
    main_products: str
    revenue_2023: Optional[float]
    domestic_market_share: Optional[float]
    core_customers: Optional[str]
    r_and_d_ratio: Optional[float]
    key_technologies: Optional[str]
    headquarters: Optional[str]
    sensitivity_level: Optional[str]
    data_source: Optional[str]
    created_at: datetime


class GenerationRequest(BaseModel):
    count: int = 100  # 默认生成 100 条


# === 核心逻辑：针对 NRSE 的定制化生成规则 ===
def generate_nrse_record(index: int) -> dict:
    """
    生成单条符合 NRSE 业务逻辑的合成数据
    """

    # 1. 规则生成 (Rule-based)
    ent_id = f"ENT_{str(index + 1000).zfill(4)}"

    stages = ["上游-原材料", "上游-零部件", "中游-设备制造", "中游-系统集成", "下游-运营维护", "下游-能源服务"]
    products_pool = ["单晶硅片", "锂离子电池", "风力发电机组", "储能变流器", "氢燃料电池", "智能电网系统", "核电阀门"]
    tech_pool = ["柔性电子技术", "固态电池技术", "超临界CO2发电", "钙钛矿电池", "智能微网控制", "深海风电技术"]
    customers_pool = ["国家电网", "南方电网", "特斯拉", "比亚迪", "宁德时代", "中核集团", "西门子能源"]
    sources = ["行业白皮书", "2023企业年报", "公开招投标数据", "第三方咨询报告"]

    # 2. 统计生成 (Statistics-based)
    revenue = round(np.random.lognormal(mean=3.0, sigma=1.0) * 10, 2)
    market_share = round(np.random.beta(a=2, b=10) * 50, 2)
    rd_ratio = round(np.random.normal(loc=8, scale=3), 2)
    rd_ratio = max(0.5, min(rd_ratio, 30.0))  # 截断异常值

    # 3. 组装数据
    return {
        "id": index,
        "enterprise_id": ent_id,
        "enterprise_name": fake.company(),
        "chain_stage": random.choice(stages),
        "main_products": ",".join(random.sample(products_pool, k=random.randint(1, 3))),
        "revenue_2023": abs(revenue),
        "domestic_market_share": market_share,
        "core_customers": ",".join(random.sample(customers_pool, k=random.randint(1, 4))),
        "r_and_d_ratio": rd_ratio,
        "key_technologies": ",".join(random.sample(tech_pool, k=random.randint(1, 3))),
        "headquarters": fake.province() + fake.city_name(),
        "sensitivity_level": np.random.choice(["低", "中", "高"], p=[0.6, 0.3, 0.1]),
        "data_source": random.choice(sources),
        "created_at": fake.date_time_between(start_date="-1y", end_date="now")
    }


@router.post("/generate", response_model=dict)
async def generate_nrse_data(request: GenerationRequest):
    """
    API 入口：批量生成 NRSE 数据，并保存为 CSV
    """
    data = []

    # 生成数据循环
    for i in range(1, request.count + 1):
        record = generate_nrse_record(i)
        data.append(record)

    # === 新增逻辑：保存 CSV ===
    try:
        # 1. 转换为 DataFrame
        df = pd.DataFrame(data)

        # 2. 生成文件名 (包含时间戳，防止覆盖)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rule_based_nrse_{timestamp}.csv"
        file_path = os.path.join(OUTPUT_DIR, filename)

        # 3. 保存文件
        # encoding='utf-8-sig' 是为了防止 Excel 打开中文乱码
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

        print(f"✅ 基于规则的生成数据已保存至: {file_path}")

    except Exception as e:
        print(f"⚠️ 保存 CSV 失败: {e}")
        file_path = "Save Failed"

    return {
        "count": request.count,
        "schema": "NRSE",
        "method": "Rule-based + Statistical Hybrid",
        "file_path": file_path,  # 返回文件路径
        "data": data
    }


# === 主程序启动 ===
if __name__ == "__main__":
    import uvicorn

    app = FastAPI()
    app.include_router(router)
    print("服务已启动: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)