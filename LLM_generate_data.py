from zai import ZhipuAiClient
import pandas as pd
import time
import io

# 设置API密钥
# 请注意：这里的 API Key 是示例，您需要确保您的实际 key 是正确的。
client = ZhipuAiClient(api_key="9c7aceb4e5134f6eb7139e72dc381772.RWdlYup10F8AqhrZ")

# 设置生成数据的总条数
TOTAL_RECORDS = 100

# 1. 修改Prompt：强制要求 CSV 格式，不要 Markdown
core_prompt = f"""
【角色设定】
你是一个专业的商业情报数据生成助手，专门负责生成用于教学（数据脱敏与匿名化课程）的模拟数据。

【任务目标】
生成一批“新能源汽车动力电池产业链”的企业级情报数据。数据需模拟商业咨询机构的行业分析报告，覆盖产业链上游（原材料）、中游（制造）、下游（整车）及回收环节。

【数据结构】
请严格包含以下 12 个字段，字段间用逗号分隔：
企业ID, 企业名称, 产业链环节, 主要产品/服务, 2023年预估营收(亿元), 国内市场份额(%), 核心客户, 研发投入占比(%), 关键技术布局, 总部所在地, 敏感等级, 数据来源标签

【字段生成规则】
1. 企业ID：虚构的唯一代码，格式如 "ENT_XXX"。
2. 企业名称：必须是虚构但听起来真实的行业名称，例如"华夏锂业"、"东海电池科技"，不要使用真实存在的公司名（如宁德时代）。
3. 产业链环节：从"上游-原材料"、"中游-电芯制造"、"中游-电池PACK"、"下游-整车"、"回收"中随机分布。
4. 数值数据：营收和市场份额需符合行业头部、腰部、尾部的分布规律；研发占比通常在 3%-15% 之间。
5. 核心客户：列出 1-2 家下游客户，如"北极汽车"。
6. 敏感等级：随机分布为"高"、"中"、"低"。
7. 总部所在地：使用真实的中国城市名称。

【输出格式要求】
1. 直接输出 CSV 格式的纯文本。
2. 第一行为表头。
3. 不要包含 markdown 标记（如 ```csv），不要包含任何解释性文字。
4. 确保每行数据完整，不要换行。
"""


def generate_data(record_count):
    """一次性生成指定条数的数据"""
    print(f"开始调用API，请求生成 {record_count} 条数据...")

    # 构建最终的 Prompt
    prompt = f"{core_prompt}\n\n请严格生成 {record_count} 条数据。"

    try:
        start_time = time.time()

        # 调用智谱 AI 客户端
        response = client.chat.completions.create(
            model="glm-4.5-air",
            messages=[
                {"role": "system", "content": "你是一个严格的数据生成机器，只输出CSV格式文本，并严格遵守用户要求的行数。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,  # 保持一定的创造性和多样性
        )

        end_time = time.time()
        print(f"API 调用完成，耗时 {end_time - start_time:.2f} 秒。")

        content = response.choices[0].message.content

        # 数据清洗：移除 Markdown 标记
        content = content.replace("```csv", "").replace("```", "").strip()

        return content

    except Exception as e:
        print(f"生成数据时出错: {e}")
        return None


# ==================== 主程序 ====================

csv_text = generate_data(TOTAL_RECORDS)

if csv_text:
    try:
        # 将文本数据转换为 DataFrame
        df_final = pd.read_csv(io.StringIO(csv_text))

        # 清理空格和空行
        df_final = df_final.dropna(how='all')

        # 统计最终条数
        final_count = len(df_final)

        # 保存为 CSV 文件
        output_file = "industry.csv"
        df_final.to_csv(output_file, index=False, encoding="utf-8-sig")

        print(f"\n任务成功！")
        print(f"原始请求条数: {TOTAL_RECORDS}")
        print(f"实际获取并成功解析的记录条数: {final_count}")
        print(f"文件已保存为: {output_file}")

        # 打印前几行看看
        print("\n数据预览:")
        print(df_final.head())

        if final_count != TOTAL_RECORDS:
            print(f"\n【警告】实际生成的条数 ({final_count}) 与请求条数 ({TOTAL_RECORDS}) 不符，请检查 AI 输出内容。")

    except Exception as e:
        print(f"\n数据格式解析失败。错误: {e}")
        print("--- 原始返回内容 (用于调试) ---")
        print(csv_text)
        print("--------------------------------")
else:
    print("未能生成有效数据。")