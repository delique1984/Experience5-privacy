"""
NRSE 差分隐私服务
专门针对新能源和半导体企业数据的差分隐私保护
基于拉普拉斯机制和高斯机制
"""
import numpy as np
from typing import List, Dict, Any, Tuple
import math


class DifferentialPrivacyService:
    """NRSE 差分隐私服务类"""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        初始化差分隐私服务

        Args:
            epsilon: 隐私预算（越小隐私保护越强）
                    推荐值：0.5-2.0
            delta: 失败概率（用于高斯机制）
                   推荐值：1e-5
        """
        self.epsilon = epsilon
        self.delta = delta

        # NRSE 数值字段的典型边界
        self.field_bounds = {
            'revenue_2023': (0.0, 1000.0),           # 营收范围：0-1000亿
            'domestic_market_share': (0.0, 100.0),   # 市场份额：0-100%
            'r_and_d_ratio': (0.0, 30.0),            # 研发占比：0-30%
        }

        # 字段敏感度配置
        self.field_sensitivity = {
            'revenue_2023': 1000.0,          # 高敏感度
            'domestic_market_share': 100.0,  # 高敏感度
            'r_and_d_ratio': 30.0,           # 中等敏感度
        }

    def laplace_mechanism(
        self,
        true_value: float,
        sensitivity: float,
        epsilon: float = None
    ) -> float:
        """
        拉普拉斯机制
        为真实值添加拉普拉斯噪声

        Args:
            true_value: 真实值
            sensitivity: 全局敏感度
            epsilon: 隐私预算（如果不指定则使用默认值）

        Returns:
            添加噪声后的值
        """
        epsilon = epsilon or self.epsilon

        # 计算拉普拉斯分布的 scale 参数
        scale = sensitivity / epsilon

        # 生成拉普拉斯噪声
        noise = np.random.laplace(0, scale)

        return true_value + noise

    def gaussian_mechanism(
        self,
        true_value: float,
        sensitivity: float,
        epsilon: float = None,
        delta: float = None
    ) -> float:
        """
        高斯机制
        为真实值添加高斯噪声

        Args:
            true_value: 真实值
            sensitivity: 全局敏感度
            epsilon: 隐私预算
            delta: 失败概率

        Returns:
            添加噪声后的值
        """
        epsilon = epsilon or self.epsilon
        delta = delta or self.delta

        # 计算高斯分布的标准差
        # sigma = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon
        sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon

        # 生成高斯噪声
        noise = np.random.normal(0, sigma)

        return true_value + noise

    def add_noise_to_field(
        self,
        value: float,
        field_name: str,
        mechanism: str = 'laplace'
    ) -> float:
        """
        为特定字段添加噪声
        根据字段类型自动选择合适的敏感度

        Args:
            value: 原始值
            field_name: 字段名
            mechanism: 噪声机制

        Returns:
            添加噪声后的值
        """
        if value is None:
            return None

        # 获取字段的敏感度
        sensitivity = self.field_sensitivity.get(field_name, 1.0)

        # 添加噪声
        if mechanism == 'laplace':
            noisy_value = self.laplace_mechanism(value, sensitivity)
        elif mechanism == 'gaussian':
            noisy_value = self.gaussian_mechanism(value, sensitivity)
        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

        # 裁剪到有效范围
        bounds = self.field_bounds.get(field_name)
        if bounds:
            min_val, max_val = bounds
            noisy_value = max(min_val, min(max_val, noisy_value))

        return noisy_value

    def privatize_enterprise_data(
        self,
        data: List[Dict],
        numeric_fields: List[str],
        mechanism: str = 'laplace',
        custom_bounds: Dict[str, Tuple[float, float]] = None
    ) -> Tuple[List[Dict], Dict]:
        """
        对企业数据集进行差分隐私处理

        Args:
            data: 原始企业数据
            numeric_fields: 需要添加噪声的数值字段
            mechanism: 噪声机制 ('laplace' 或 'gaussian')
            custom_bounds: 自定义边界 {field: (min, max)}

        Returns:
            (隐私化后的数据, 统计信息)
        """
        if not data:
            return [], {"error": "No data provided"}

        # 更新边界（如果提供了自定义边界）
        if custom_bounds:
            self.field_bounds.update(custom_bounds)
            # 同时更新敏感度
            for field, (min_val, max_val) in custom_bounds.items():
                self.field_sensitivity[field] = max_val - min_val

        privatized_data = []
        field_changes = {field: [] for field in numeric_fields}

        for record in data:
            private_record = record.copy()

            for field in numeric_fields:
                if field not in record or record[field] is None:
                    continue

                original_value = float(record[field])

                # 添加噪声
                noisy_value = self.add_noise_to_field(
                    original_value,
                    field,
                    mechanism
                )

                private_record[field] = noisy_value

                # 记录变化用于统计
                field_changes[field].append({
                    'original': original_value,
                    'noisy': noisy_value,
                    'difference': abs(noisy_value - original_value)
                })

            privatized_data.append(private_record)

        # 计算统计信息
        stats = self._compute_statistics(field_changes, mechanism)

        return privatized_data, stats

    def _compute_statistics(
        self,
        field_changes: Dict[str, List[Dict]],
        mechanism: str
    ) -> Dict:
        """计算隐私化统计信息"""
        stats = {
            "epsilon": self.epsilon,
            "mechanism": mechanism,
            "field_metrics": {}
        }

        for field, changes in field_changes.items():
            if not changes:
                continue

            original_values = [c['original'] for c in changes]
            noisy_values = [c['noisy'] for c in changes]
            differences = [c['difference'] for c in changes]

            # 计算误差指标
            mae = np.mean(differences)
            mse = np.mean([d ** 2 for d in differences])
            rmse = np.sqrt(mse)

            # 相对误差
            relative_errors = []
            for orig, noisy in zip(original_values, noisy_values):
                if orig != 0:
                    relative_errors.append(abs((noisy - orig) / orig))

            avg_relative_error = np.mean(relative_errors) if relative_errors else 0

            stats["field_metrics"][field] = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "relative_error": round(avg_relative_error, 4),
                "max_difference": round(max(differences), 4),
                "min_difference": round(min(differences), 4),
                "sensitivity": self.field_sensitivity.get(field, 1.0)
            }

        return stats

    # ==================== 统计查询相关方法 ====================

    def query_count(
        self,
        data: List[Dict],
        filter_condition: Dict[str, Any] = None,
        mechanism: str = 'laplace'
    ) -> Tuple[int, Dict]:
        """
        差分隐私计数查询

        Args:
            data: 数据列表
            filter_condition: 过滤条件 {field: value}
            mechanism: 噪声机制

        Returns:
            (带噪声的计数, 查询信息)
        """
        # 应用过滤条件
        if filter_condition:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in filter_condition.items())
            ]
        else:
            filtered_data = data

        true_count = len(filtered_data)
        sensitivity = 1  # 计数查询的敏感度为1

        # 添加噪声
        if mechanism == 'laplace':
            noisy_count = self.laplace_mechanism(true_count, sensitivity)
        else:
            noisy_count = self.gaussian_mechanism(true_count, sensitivity)

        noisy_count = max(0, round(noisy_count))

        query_info = {
            "query_type": "count",
            "true_count": true_count,
            "noisy_count": noisy_count,
            "noise": noisy_count - true_count,
            "mechanism": mechanism,
            "epsilon": self.epsilon
        }

        return noisy_count, query_info

    def query_sum(
        self,
        data: List[Dict],
        field: str,
        filter_condition: Dict[str, Any] = None,
        mechanism: str = 'laplace'
    ) -> Tuple[float, Dict]:
        """
        差分隐私求和查询

        Args:
            data: 数据列表
            field: 求和的字段
            filter_condition: 过滤条件
            mechanism: 噪声机制

        Returns:
            (带噪声的和, 查询信息)
        """
        # 应用过滤条件
        if filter_condition:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in filter_condition.items())
            ]
        else:
            filtered_data = data

        # 提取字段值
        values = [
            float(record[field])
            for record in filtered_data
            if field in record and record[field] is not None
        ]

        if not values:
            return 0.0, {"error": "No valid data"}

        true_sum = sum(values)

        # 获取敏感度
        sensitivity = self.field_sensitivity.get(field, max(values) - min(values))

        # 添加噪声
        if mechanism == 'laplace':
            noisy_sum = self.laplace_mechanism(true_sum, sensitivity)
        else:
            noisy_sum = self.gaussian_mechanism(true_sum, sensitivity)

        query_info = {
            "query_type": "sum",
            "field": field,
            "true_sum": round(true_sum, 4),
            "noisy_sum": round(noisy_sum, 4),
            "count": len(values),
            "mechanism": mechanism,
            "epsilon": self.epsilon,
            "sensitivity": sensitivity
        }

        return noisy_sum, query_info

    def query_average(
        self,
        data: List[Dict],
        field: str,
        filter_condition: Dict[str, Any] = None,
        mechanism: str = 'laplace'
    ) -> Tuple[float, Dict]:
        """
        差分隐私平均值查询

        Args:
            data: 数据列表
            field: 求平均的字段
            filter_condition: 过滤条件
            mechanism: 噪声机制

        Returns:
            (带噪声的平均值, 查询信息)
        """
        # 应用过滤条件
        if filter_condition:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in filter_condition.items())
            ]
        else:
            filtered_data = data

        # 提取字段值
        values = [
            float(record[field])
            for record in filtered_data
            if field in record and record[field] is not None
        ]

        if not values:
            return 0.0, {"error": "No valid data"}

        true_avg = sum(values) / len(values)
        count = len(values)

        # 平均值的敏感度 = 范围 / n
        field_range = self.field_sensitivity.get(field, max(values) - min(values))
        sensitivity = field_range / count

        # 添加噪声
        if mechanism == 'laplace':
            noisy_avg = self.laplace_mechanism(true_avg, sensitivity)
        else:
            noisy_avg = self.gaussian_mechanism(true_avg, sensitivity)

        # 裁剪到有效范围
        bounds = self.field_bounds.get(field)
        if bounds:
            min_val, max_val = bounds
            noisy_avg = max(min_val, min(max_val, noisy_avg))

        query_info = {
            "query_type": "average",
            "field": field,
            "true_average": round(true_avg, 4),
            "noisy_average": round(noisy_avg, 4),
            "count": count,
            "mechanism": mechanism,
            "epsilon": self.epsilon,
            "sensitivity": sensitivity
        }

        return noisy_avg, query_info

    def query_histogram(
        self,
        data: List[Dict],
        field: str,
        bins: List[Any] = None,
        mechanism: str = 'laplace'
    ) -> Tuple[Dict[Any, int], Dict]:
        """
        差分隐私直方图查询

        Args:
            data: 数据列表
            field: 统计的字段
            bins: 分箱（如果为None则使用唯一值）
            mechanism: 噪声机制

        Returns:
            (带噪声的直方图, 查询信息)
        """
        # 提取字段值
        values = [
            record[field]
            for record in data
            if field in record and record[field] is not None
        ]

        if not values:
            return {}, {"error": "No valid data"}

        # 确定分箱
        if bins is None:
            bins = sorted(list(set(values)))

        # 计算真实直方图
        true_histogram = {bin_val: 0 for bin_val in bins}
        for value in values:
            if value in true_histogram:
                true_histogram[value] += 1

        # 为每个 bin 添加噪声
        noisy_histogram = {}
        sensitivity = 1  # 每个 bin 的计数敏感度为1

        for bin_val, count in true_histogram.items():
            if mechanism == 'laplace':
                noisy_count = self.laplace_mechanism(count, sensitivity)
            else:
                noisy_count = self.gaussian_mechanism(count, sensitivity)

            noisy_count = max(0, round(noisy_count))
            noisy_histogram[bin_val] = noisy_count

        query_info = {
            "query_type": "histogram",
            "field": field,
            "bins": len(bins),
            "total_count": sum(true_histogram.values()),
            "mechanism": mechanism,
            "epsilon": self.epsilon
        }

        return noisy_histogram, query_info

    def query_percentile(
        self,
        data: List[Dict],
        field: str,
        percentiles: List[float] = [25, 50, 75],
        mechanism: str = 'laplace'
    ) -> Tuple[Dict[float, float], Dict]:
        """
        差分隐私分位数查询

        Args:
            data: 数据列表
            field: 字段名
            percentiles: 分位数列表 [25, 50, 75]
            mechanism: 噪声机制

        Returns:
            (带噪声的分位数, 查询信息)
        """
        # 提取字段值
        values = [
            float(record[field])
            for record in data
            if field in record and record[field] is not None
        ]

        if not values:
            return {}, {"error": "No valid data"}

        values = sorted(values)

        # 计算真实分位数
        true_percentiles = {}
        for p in percentiles:
            idx = int(len(values) * p / 100)
            idx = min(idx, len(values) - 1)
            true_percentiles[p] = values[idx]

        # 为分位数添加噪声
        noisy_percentiles = {}
        sensitivity = self.field_sensitivity.get(field, max(values) - min(values))

        for p, value in true_percentiles.items():
            if mechanism == 'laplace':
                noisy_value = self.laplace_mechanism(value, sensitivity)
            else:
                noisy_value = self.gaussian_mechanism(value, sensitivity)

            # 裁剪到有效范围
            bounds = self.field_bounds.get(field)
            if bounds:
                min_val, max_val = bounds
                noisy_value = max(min_val, min(max_val, noisy_value))

            noisy_percentiles[p] = round(noisy_value, 4)

        query_info = {
            "query_type": "percentile",
            "field": field,
            "percentiles": percentiles,
            "count": len(values),
            "mechanism": mechanism,
            "epsilon": self.epsilon
        }

        return noisy_percentiles, query_info

    def evaluate_privacy_budget(self, num_queries: int) -> Dict:
        """
        评估隐私预算消耗

        Args:
            num_queries: 查询次数

        Returns:
            隐私预算评估报告
        """
        total_epsilon = self.epsilon * num_queries

        # 评估隐私级别
        if total_epsilon < 1.0:
            privacy_level = "强隐私保护"
        elif total_epsilon < 5.0:
            privacy_level = "中等隐私保护"
        else:
            privacy_level = "弱隐私保护"

        # 计算剩余查询次数（假设总预算为10.0）
        total_budget = 10.0
        remaining_queries = int((total_budget - total_epsilon) / self.epsilon)

        return {
            "epsilon_per_query": self.epsilon,
            "num_queries": num_queries,
            "total_epsilon_consumed": round(total_epsilon, 4),
            "privacy_level": privacy_level,
            "remaining_budget": max(0, round(total_budget - total_epsilon, 4)),
            "remaining_queries": max(0, remaining_queries),
            "recommendation": self._get_privacy_recommendation(total_epsilon)
        }

    def _get_privacy_recommendation(self, total_epsilon: float) -> str:
        """获取隐私保护建议"""
        if total_epsilon < 1.0:
            return "隐私预算充足，可以继续查询"
        elif total_epsilon < 5.0:
            return "隐私预算适中，建议谨慎进行后续查询"
        elif total_epsilon < 10.0:
            return "隐私预算较低，建议减少查询频率或提高epsilon值"
        else:
            return "隐私预算耗尽，不建议继续查询，考虑重新评估隐私需求"
