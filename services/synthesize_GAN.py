# service_nrse_gan.py

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import pandas as pd
import os

# 引入 SDV 库中的 CTGAN 合成器和元数据定义
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata

# 复用之前的 faker 逻辑来生成“训练用的种子数据”
from faker import Faker
import numpy as np
import random

fake = Faker('zh_CN')
router = APIRouter(prefix="/nrse-gan", tags=["NRSE Data Synthesis (GAN)"])

# === 配置路径 ===
MODEL_PATH = "nrse_ctgan_model.pkl"
OUTPUT_DIR = "generated_data"  # 新增：生成的 CSV 保存目录
global_model = None  # 全局变量存储加载的模型

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# === 辅助：生成种子数据用于训练 (模拟从数据库取数) ===

# 定义 GAN 需要学习的特征列
FEATURE_COLUMNS = [
    "chain_stage",  # 产业链环节 (类别)
    "main_products",  # 主要产品 (类别)
    "revenue_2023",  # 营收 (数值)
    "domestic_market_share",  # 市场份额 (数值)
    "r_and_d_ratio",  # 研发占比 (数值)
    "sensitivity_level"  # 敏感等级 (类别)
]


def get_seed_data(file_path="insustry.csv"):
    """
    从 CSV 文件读取种子数据作为 GAN 的训练集。
    """
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"⚠️ 未找到文件 {file_path}，正在生成示例 CSV 文件...")
        _create_dummy_csv(file_path)

    try:
        # 2. 读取 CSV
        df = pd.read_csv(file_path)

        # 3. 校验列名
        missing_cols = [col for col in FEATURE_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"CSV 文件缺少以下必要列: {missing_cols}")

        # 4. 特征筛选与清洗
        df_train = df[FEATURE_COLUMNS]

        # 处理缺失值
        initial_count = len(df_train)
        df_train = df_train.dropna()
        dropped_count = initial_count - len(df_train)

        if dropped_count > 0:
            print(f"已丢弃 {dropped_count} 条包含空值的记录。")

        # 确保数值列类型正确
        df_train["revenue_2023"] = pd.to_numeric(df_train["revenue_2023"], errors='coerce')
        df_train["domestic_market_share"] = pd.to_numeric(df_train["domestic_market_share"], errors='coerce')
        df_train["r_and_d_ratio"] = pd.to_numeric(df_train["r_and_d_ratio"], errors='coerce')

        df_train = df_train.dropna()

        print(f"✅ 成功加载训练数据，有效样本数: {len(df_train)}")
        return df_train

    except Exception as e:
        raise RuntimeError(f"读取 CSV 数据失败: {str(e)}")


def _create_dummy_csv(path):
    """
    辅助函数：仅用于演示。生成虚拟的 CSV 文件。
    """
    data_list = []
    stages = ["上游-原材料", "上游-零部件", "中游-设备制造", "中游-系统集成", "下游-运营维护", "下游-能源服务"]
    products_pool = ["单晶硅片", "锂离子电池", "风力发电机组", "储能变流器", "氢燃料电池", "智能电网系统"]

    for _ in range(500):
        data_list.append({
            "id": _ + 1,
            "chain_stage": random.choice(stages),
            "main_products": random.choice(products_pool),
            "revenue_2023": round(abs(np.random.normal(5000, 2000)), 2),
            "domestic_market_share": round(np.random.beta(2, 10) * 50, 2),
            "r_and_d_ratio": round(np.random.normal(8, 3), 2),
            "sensitivity_level": np.random.choice(["低", "中", "高"]),
            "created_at": "2023-01-01"
        })

    pd.DataFrame(data_list).to_csv(path, index=False, encoding='utf-8-sig')
    print(f"已生成示例文件: {path}")


# === 核心逻辑：训练与加载模型 ===

def train_model():
    """训练 CTGAN 模型并保存"""
    print("正在准备训练数据...")
    df_train = get_seed_data()

    print("正在初始化元数据...")
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df_train)

    synthesizer = CTGANSynthesizer(metadata, epochs=100, verbose=True)

    print("开始训练 GAN 模型 (这可能需要几分钟)...")
    synthesizer.fit(df_train)

    print("模型训练完成，正在保存...")
    synthesizer.save(MODEL_PATH)
    return synthesizer


def load_model():
    """加载已训练的模型"""
    global global_model
    if os.path.exists(MODEL_PATH):
        global_model = CTGANSynthesizer.load(MODEL_PATH)
        print("已加载预训练模型。")
    else:
        print("未找到预训练模型，正在首次训练...")
        global_model = train_model()


# === API 定义 ===

class GenerationRequest(BaseModel):
    count: int = 100


@router.post("/train")
async def trigger_training():
    """手动触发模型重新训练"""
    global global_model
    global_model = train_model()
    return {"message": "Model retrained successfully", "model_path": MODEL_PATH}


@router.post("/generate", response_model=dict)
async def generate_nrse_data_gan(request: GenerationRequest):
    """
    API 入口：基于 GAN 生成统计特征逼真的数据，并保存为 CSV
    """
    if global_model is None:
        raise HTTPException(status_code=500, detail="Model is not loaded")

    # 1. 使用 GAN 采样
    synthetic_data = global_model.sample(num_rows=request.count)

    # 2. 后处理 (Post-processing)
    result_data = []
    records = synthetic_data.to_dict(orient="records")
    current_id_start = 5000

    for idx, row in enumerate(records):
        # 补全非统计类字段
        row["id"] = idx + 1
        row["enterprise_id"] = f"ENT_GAN_{str(current_id_start + idx).zfill(4)}"
        row["enterprise_name"] = fake.company() + " (合成)"
        row["headquarters"] = fake.province() + fake.city_name()
        row["data_source"] = "GAN模型合成"
        row["created_at"] = datetime.now()  # 注意：保存到CSV时，这里会变成完整的日期时间字符串

        # 数值修正
        row["revenue_2023"] = round(max(0, row["revenue_2023"]), 2)
        row["r_and_d_ratio"] = round(max(0, row["r_and_d_ratio"]), 2)
        row["core_customers"] = "混合生成客户"

        result_data.append(row)

    # === 新增逻辑：保存为 CSV ===

    # 将处理好的字典列表转换为 DataFrame
    df_result = pd.DataFrame(result_data)

    # 生成带有时间戳的文件名，防止覆盖
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"synthetic_nrse_{timestamp}.csv"
    file_path = os.path.join(OUTPUT_DIR, filename)

    # 保存文件 (使用 utf-8-sig 以便 Excel 正确打开中文)
    df_result.to_csv(file_path, index=False, encoding='utf-8-sig')

    print(f"✅ 生成数据已保存至: {file_path}")

    return {
        "count": request.count,
        "schema": "NRSE",
        "method": "Statistics-based (CTGAN)",
        "file_path": file_path,  # 返回保存路径
        "note": "数据已保存至服务器本地 CSV 文件",
        "data_preview": result_data[:5]  # 只返回前5条作为预览，避免响应体过大
    }


# === 主程序启动 ===
if __name__ == "__main__":
    import uvicorn

    load_model()

    app = FastAPI()
    app.include_router(router)
    print("GAN 数据服务已启动: http://127.0.0.1:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)