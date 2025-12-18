"""
数据脱敏服务
实现多种数据脱敏算法
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import hashlib
import re

class DataMaskingService:
    """
    专门用于企业情报数据的脱敏服务
    针对字段：企业名称、核心客户列表、企业ID
    """

    def __init__(self, salt: str = "edu_demo_salt"):
        # 加盐（Salt）是为了防止彩虹表攻击，增加哈希破解难度
        self.salt = salt
        self.mask_char = "*"

    def hash_id(self, original_id: str) -> str:
        """
        对企业ID进行哈希处理 (SHA256)
        示例: ENT_001 -> a3f9...
        """
        if pd.isna(original_id) or original_id == "":
            return original_id

        # 将数据 + 盐 混合后进行哈希
        data = f"{str(original_id)}{self.salt}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def mask_company_name(self, name: str) -> str:
        """
        企业名称掩码处理
        规则：
        2字名 -> 这里的* (如: 百度 -> 百*)
        3字名 -> 头*尾 (如: 比亚迪 -> 比*迪)
        4字及以上 -> 头**尾 (如: 宁德时代 -> 宁**代)
        """
        if pd.isna(name) or name == "":
            return name

        name = str(name).strip()
        length = len(name)

        if length <= 1:
            return name
        elif length == 2:
            return name[0] + self.mask_char
        elif length == 3:
            return name[0] + self.mask_char + name[-1]
        else:
            # 4个字及以上，保留首尾，中间用两个星号代替（或者根据长度动态填充）
            # 为了美观，这里固定用两个星号，模拟常见的 "某**公司" 格式
            return name[0] + self.mask_char * 2 + name[-1]

    def mask_client_list(self, client_str: str) -> str:
        """
        处理包含多个客户的字段
        示例: "特斯拉中国、蔚来汽车" -> "特**国、蔚**车"
        难点: 需要识别分隔符，拆分处理后再合并
        """
        if pd.isna(client_str) or client_str == "":
            return client_str

        # 1. 识别分隔符（可能是中文顿号、中文逗号、英文逗号、空格）
        # 使用正则表达式进行分割
        separators = r'[、，, ]+'
        clients = re.split(separators, str(client_str))

        masked_clients = []
        for client in clients:
            if client.strip():
                # 复用上面的单名称脱敏逻辑
                masked_clients.append(self.mask_company_name(client))

        # 2. 将脱敏后的列表重新合并（这里统一用中文顿号连接，显得更整洁）
        return "、".join(masked_clients)

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        执行批量脱敏 (基于mask_batch的DataFrame封装)
        """
        print(">>> 开始执行脱敏操作...")

        # 定义默认脱敏规则
        field_rules = {
            '企业ID': 'hash_id',
            '企业名称': 'company_name',
            '核心客户': 'client_list'
        }

        # 转换为字典列表进行处理
        records = df.to_dict('records')
        masked_records = self.mask_batch(records, field_rules)

        print(">>> 脱敏完成！")
        return pd.DataFrame(masked_records)

    def calculate_masking_rate(self, original: str, masked: str) -> float:
        """
        计算脱敏率
        (原有函数名保持不变)
        """
        if not original or not masked:
            return 0.0

        # 转换为字符串防止报错
        original = str(original)
        masked = str(masked)

        if len(original) == 0:
            return 0.0

        masked_chars = sum(1 for c in masked if c == self.mask_char)
        return masked_chars / len(original)

    def mask_batch(self, data: List[Dict], field_rules: Dict[str, str]) -> List[Dict]:
        """
        批量脱敏 (针对 List[Dict] 结构)
        (原有函数名保持不变)

        Args:
            data: 数据列表 (通常由 df.to_dict('records') 转换而来)
            field_rules: {字段名: 脱敏类型}
                         支持类型: 'hash_id', 'company_name', 'client_list'
        """
        masked_data = []

        for record in data:
            masked_record = record.copy()

            for field, mask_type in field_rules.items():
                if field not in masked_record or pd.isna(masked_record[field]):
                    continue

                value = masked_record[field]

                # 这里根据 mask_type 路由到上面的原子方法
                if mask_type == 'hash_id':
                    masked_record[field] = self.hash_id(value)
                elif mask_type == 'company_name':
                    masked_record[field] = self.mask_company_name(value)
                elif mask_type == 'client_list':
                    masked_record[field] = self.mask_client_list(value)
                # 如果有其他通用类型，也可以保留，例如：
                elif mask_type == 'hash':
                    masked_record[field] = self.hash_id(value)

            masked_data.append(masked_record)

        return masked_data





