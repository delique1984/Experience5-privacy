"""
NRSE K-匿名处理服务
专门针对新能源和半导体企业数据的隐私保护
基于改进的 KACA 算法
"""
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import numpy as np
import re

class KAnonymityService:
    """NRSE K-匿名服务类"""

    def __init__(self, k: int = 5):
        """
        初始化 K-匿名服务

        Args:
            k: K值，每个等价类至少包含 k 条记录
        """
        self.k = k

        # 产业链环节层级定义
        self.chain_hierarchy = {
            '上游': ['上游-原材料', '上游-设备', '上游-零部件'],
            '中游': ['中游-制造', '中游-封装', '中游-组装'],
            '下游': ['下游-应用', '下游-销售', '下游-服务']
        }

        # 地区层级定义（省-市-区）
        self.region_hierarchy = self._build_region_hierarchy()

    def _build_region_hierarchy(self) -> Dict[str, List[str]]:
        """构建地区层级结构"""
        return {
            '华北': ['北京市', '天津市', '河北省', '山西省', '内蒙古自治区'],
            '华东': ['上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省'],
            '华南': ['广东省', '广西壮族自治区', '海南省'],
            '华中': ['河南省', '湖北省', '湖南省'],
            '西南': ['重庆市', '四川省', '贵州省', '云南省', '西藏自治区'],
            '西北': ['陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区'],
            '东北': ['辽宁省', '吉林省', '黑龙江省']
        }

    def generalize_revenue(self, revenue: float, level: int = 1) -> str:
        """
        营收泛化

        Args:
            revenue: 营收(亿元)
            level: 泛化级别 (1=细粒度, 2=中等, 3=粗粒度)

        Returns:
            泛化后的营收区间
        """
        if revenue is None:
            return "未知"
        try:
            revenue = float(revenue)
        except (TypeError, ValueError):
            return "未知"
        # 根据级别定义不同的区间
        if level == 1:
            # 细粒度区间
            bins = [0, 1, 5, 10, 50, 100, 500, float('inf')]
            labels = ['1亿以下', '1-5亿', '5-10亿', '10-50亿', '50-100亿', '100-500亿', '500亿以上']
        elif level == 2:
            # 中等粒度
            bins = [0, 10, 50, 100, float('inf')]
            labels = ['10亿以下', '10-50亿', '50-100亿', '100亿以上']
        else:
            # 粗粒度
            bins = [0, 50, 100, float('inf')]
            labels = ['50亿以下', '50-100亿', '100亿以上']

        for i in range(len(bins) - 1):
            if bins[i] <= revenue < bins[i + 1]:
                return labels[i]

        return "未知"

    def generalize_market_share(self, share: float, level: int = 1) -> str:
        """
        市场份额泛化

        Args:
            share: 市场份额(%)
            level: 泛化级别

        Returns:
            泛化后的市场份额区间
        """
        if share is None:
            return "未知"

        if level == 1:
            # 细粒度
            if share < 1:
                return "1%以下"
            elif share < 5:
                return "1-5%"
            elif share < 10:
                return "5-10%"
            elif share < 20:
                return "10-20%"
            elif share < 50:
                return "20-50%"
            else:
                return "50%以上"
        elif level == 2:
            # 中等粒度
            if share < 5:
                return "5%以下"
            elif share < 20:
                return "5-20%"
            elif share < 50:
                return "20-50%"
            else:
                return "50%以上"
        else:
            # 粗粒度
            if share < 10:
                return "10%以下"
            elif share < 50:
                return "10-50%"
            else:
                return "50%以上"

    def generalize_rd_ratio(self, ratio: float, level: int = 1) -> str:
        """
        研发投入占比泛化

        Args:
            ratio: 研发投入占比(%)
            level: 泛化级别

        Returns:
            泛化后的研发占比区间
        """
        if ratio is None:
            return "未知"

        if level == 1:
            if ratio < 5:
                return "低投入(5%以下)"
            elif ratio < 10:
                return "中等投入(5-10%)"
            elif ratio < 15:
                return "较高投入(10-15%)"
            else:
                return "高投入(15%以上)"
        elif level == 2:
            if ratio < 10:
                return "中低投入(10%以下)"
            else:
                return "中高投入(10%以上)"
        else:
            if ratio < 15:
                return "一般投入"
            else:
                return "高投入"

    def generalize_chain_stage(self, stage: str, level: int = 1) -> str:
        """
        产业链环节泛化

        Args:
            stage: 产业链环节
            level: 泛化级别 (1=保留细节, 2=泛化到大类)

        Returns:
            泛化后的产业链环节
        """
        if not stage:
            return "未知"

        if level == 1:
            return stage
        elif level == 2:
            # 泛化到大类
            for category, stages in self.chain_hierarchy.items():
                if any(s in stage for s in stages):
                    return category
            # 如果没有匹配，提取主要类别
            if '上游' in stage:
                return '上游'
            elif '中游' in stage:
                return '中游'
            elif '下游' in stage:
                return '下游'
            return stage
        else:
            # 最粗粒度：只保留上中下游
            return "产业链企业"

    def _build_city_mapping(self) -> Dict[str, str]:
        """
        构建常用城市到省份的映射
        注意：实际生产环境中，建议从数据库或完整行政区划表加载
        这里列举了新能源与半导体产业集聚的主要城市
        """
        mapping = {
            # 直辖市
            '北京': '北京市', '上海': '上海市', '天津': '天津市', '重庆': '重庆市',

            # 江苏 (半导体/光伏重镇)
            '苏州': '江苏省', '南京': '江苏省', '无锡': '江苏省', '常州': '江苏省',
            '南通': '江苏省', '徐州': '江苏省', '扬州': '江苏省', '盐城': '江苏省',

            # 广东 (电子/电池重镇)
            '深圳': '广东省', '广州': '广东省', '东莞': '广东省', '佛山': '广东省',
            '惠州': '广东省', '珠海': '广东省',

            # 浙江
            '杭州': '浙江省', '宁波': '浙江省', '温州': '浙江省', '嘉兴': '浙江省',
            '绍兴': '浙江省',

            # 安徽 (新能源车/显示)
            '合肥': '安徽省', '芜湖': '安徽省', '滁州': '安徽省',

            # 四川 & 重庆
            '成都': '四川省', '宜宾': '四川省', '绵阳': '四川省',

            # 陕西 (光伏/半导体)
            '西安': '陕西省', '咸阳': '陕西省',

            # 湖南 (电池材料)
            '长沙': '湖南省', '株洲': '湖南省',

            # 湖北
            '武汉': '湖北省', '宜昌': '湖北省',

            # 福建 (电池)
            '宁德': '福建省', '福州': '福建省', '厦门': '福建省',

            # 山东
            '青岛': '山东省', '济南': '山东省', '烟台': '山东省',

            # 江西 (锂电)
            '宜春': '江西省', '南昌': '江西省', '赣州': '江西省',

            # 其它省会及重要城市
            '郑州': '河南省', '石家庄': '河北省', '太原': '山西省',
            '沈阳': '辽宁省', '大连': '辽宁省', '长春': '吉林省', '哈尔滨': '黑龙江省',
            '贵阳': '贵州省', '昆明': '云南省', '兰州': '甘肃省', '银川': '宁夏回族自治区',
            '乌鲁木齐': '新疆维吾尔自治区', '呼和浩特': '内蒙古自治区'
        }
        return mapping


    def generalize_headquarters(self, location: str, level: int = 1) -> str:
        """
        总部地址泛化 (适配仅含市名的数据，如"北京", "长沙")

        Args:
            location: 总部所在地 (如 "长沙")
            level: 泛化级别 (1=市级, 2=省级, 3=大区级)

        Returns:
            泛化后的地址
        """
        if not location:
            return "未知"

        # 去除可能存在的空格
        city_name = location.strip()

        # Level 1: 保持市级 (Level 1)
        # 直接返回原始市名，或者加上"市"字标准化
        if level == 1:
            return city_name

        city_to_province = self._build_city_mapping()
        # 获取对应的省份名 (用于 Level 2 和 Level 3)
        # 如果字典里找不到，这就属于"未知省份"
        province_name = city_to_province.get(city_name)

        if not province_name:
            # 如果映射表中没有这个城市，无法进行更高级别的泛化
            # 策略：返回"其他"或者保持原样但标记未知
            return "其他地区"

        # Level 2: 泛化到省级
        if level == 2:
            return province_name

        # Level 3: 泛化到大区级
        if level == 3:
            for region, provinces in self.region_hierarchy.items():
                if province_name in provinces:
                    return region
            return "中国"  # 如果在省份列表里找不到（比如港澳台）

        return "未知"

    def generalize_sensitivity_level(self, level: str, generalize_level: int = 1) -> str:
        """
        敏感等级泛化

        Args:
            level: 敏感等级
            generalize_level: 泛化级别

        Returns:
            泛化后的敏感等级
        """
        if not level:
            return "未知"

        if generalize_level == 1:
            return level
        else:
            # 泛化为二分类
            if level in ['高', '较高']:
                return "高敏感"
            else:
                return "低敏感"

    def suppress_enterprise_info(self, value: Any) -> str:
        """
        企业信息抑制
        对无法泛化的唯一标识信息进行抑制
        """
        return "*"

    def apply_generalization(
        self,
        record: Dict,
        quasi_identifiers: List[str],
        generalization_levels: Dict[str, int]
    ) -> Dict:
        """
        对单条记录应用泛化规则

        Args:
            record: 原始记录
            quasi_identifiers: 准标识符列表
            generalization_levels: 各字段的泛化级别

        Returns:
            泛化后的记录
        """
        generalized_record = record.copy()

        for field in quasi_identifiers:
            if field not in record:
                continue

            value = record[field]
            level = generalization_levels.get(field, 1)

            # 根据字段名选择泛化方法
            if field == 'revenue_2023':
                generalized_record[field] = self.generalize_revenue(value, level)

            elif field == 'domestic_market_share':
                generalized_record[field] = self.generalize_market_share(value, level)

            elif field == 'r_and_d_ratio':
                generalized_record[field] = self.generalize_rd_ratio(value, level)

            elif field == 'chain_stage':
                generalized_record[field] = self.generalize_chain_stage(value, level)

            elif field == 'headquarters':
                generalized_record[field] = self.generalize_headquarters(value, level)

            elif field == 'sensitivity_level':
                generalized_record[field] = self.generalize_sensitivity_level(value, level)

            else:
                # 默认泛化：字符串截断
                if isinstance(value, str) and len(value) > 3:
                    if level == 1:
                        generalized_record[field] = value
                    elif level == 2:
                        generalized_record[field] = value[:len(value)//2] + "*" * (len(value) - len(value)//2)
                    else:
                        generalized_record[field] = "*"

        return generalized_record

    def build_equivalence_classes(
        self,
        data: List[Dict],
        quasi_identifiers: List[str]
    ) -> Dict[Tuple, List[Dict]]:
        """
        构建等价类

        Args:
            data: 数据列表
            quasi_identifiers: 准标识符字段列表

        Returns:
            等价类字典
        """
        equivalence_classes = defaultdict(list)

        for record in data:
            # 提取准标识符值作为分组键
            key = tuple(str(record.get(qi, "")) for qi in quasi_identifiers)
            equivalence_classes[key].append(record)

        return dict(equivalence_classes)

    def validate_k_anonymity(
        self,
        equivalence_classes: Dict[Tuple, List[Dict]]
    ) -> Tuple[bool, int, int]:
        """
        验证是否满足 K-匿名

        Returns:
            (是否满足K-匿名, 最小类大小, 不满足的类数量)
        """
        if not equivalence_classes:
            return False, 0, 0

        class_sizes = [len(records) for records in equivalence_classes.values()]
        min_class_size = min(class_sizes)
        violated_classes = sum(1 for size in class_sizes if size < self.k)

        is_k_anonymous = min_class_size >= self.k

        return is_k_anonymous, min_class_size, violated_classes

    def handle_small_classes(
        self,
        data: List[Dict],
        equivalence_classes: Dict[Tuple, List[Dict]],
        quasi_identifiers: List[str],
        generalization_levels: Dict[str, int]
    ) -> List[Dict]:
        """
        处理小于 K 的等价类
        策略：进一步提升泛化级别或抑制

        Args:
            data: 数据列表
            equivalence_classes: 等价类字典
            quasi_identifiers: 准标识符列表
            generalization_levels: 当前泛化级别

        Returns:
            处理后的数据
        """
        # 分离满足和不满足 K-匿名的类
        valid_classes = {k: v for k, v in equivalence_classes.items() if len(v) >= self.k}
        invalid_classes = {k: v for k, v in equivalence_classes.items() if len(v) < self.k}

        result = []

        # 添加满足条件的记录
        for records in valid_classes.values():
            result.extend(records)

        # 处理不满足条件的记录
        invalid_records = []
        for records in invalid_classes.values():
            invalid_records.extend(records)

        if not invalid_records:
            return result

        # 策略1: 如果总数满足 K，进一步泛化后合并
        if len(invalid_records) >= self.k:
            # 提升泛化级别
            enhanced_levels = {k: min(v + 1, 3) for k, v in generalization_levels.items()}

            # 重新泛化
            re_generalized = []
            for record in invalid_records:
                re_gen_record = self.apply_generalization(
                    record,
                    quasi_identifiers,
                    enhanced_levels
                )
                re_generalized.append(re_gen_record)

            result.extend(re_generalized)
        else:
            # 策略2: 总数不足 K，抑制准标识符
            for record in invalid_records:
                suppressed_record = record.copy()
                for qi in quasi_identifiers:
                    if qi in suppressed_record:
                        suppressed_record[qi] = self.suppress_enterprise_info(suppressed_record[qi])
                result.append(suppressed_record)

        return result

    def anonymize(
        self,
        data: List[Dict],
        quasi_identifiers: List[str],
        sensitive_attributes: List[str] = None,
        generalization_levels: Dict[str, int] = None,
        max_iterations: int = 3
    ) -> Tuple[List[Dict], Dict]:
        """
        执行 K-匿名处理

        Args:
            data: 原始数据
            quasi_identifiers: 准标识符字段
            sensitive_attributes: 敏感属性字段
            generalization_levels: 泛化级别配置
            max_iterations: 最大迭代次数

        Returns:
            (匿名化后的数据, 统计信息)
        """
        if not data:
            return [], {"error": "No data provided"}

        # 初始化配置
        sensitive_attributes = sensitive_attributes or []
        generalization_levels = generalization_levels or {qi: 1 for qi in quasi_identifiers}

        # 验证准标识符
        for qi in quasi_identifiers:
            if qi not in data[0]:
                return [], {"error": f"Quasi-identifier '{qi}' not found in data"}

        anonymized_data = data.copy()
        iteration = 0

        while iteration < max_iterations:
            # 第一步：应用泛化
            current_anonymized = []
            for record in anonymized_data:
                gen_record = self.apply_generalization(
                    record,
                    quasi_identifiers,
                    generalization_levels
                )
                current_anonymized.append(gen_record)

            # 第二步：构建等价类
            eq_classes = self.build_equivalence_classes(
                current_anonymized,
                quasi_identifiers
            )

            # 第三步：验证 K-匿名
            is_k_anon, min_size, violated = self.validate_k_anonymity(eq_classes)

            if is_k_anon:
                # 满足 K-匿名，完成
                anonymized_data = current_anonymized
                break

            # 第四步：处理小类
            anonymized_data = self.handle_small_classes(
                current_anonymized,
                eq_classes,
                quasi_identifiers,
                generalization_levels
            )

            # 提升泛化级别准备下次迭代
            generalization_levels = {k: min(v + 1, 3) for k, v in generalization_levels.items()}
            iteration += 1

        # 最终验证
        final_eq_classes = self.build_equivalence_classes(anonymized_data, quasi_identifiers)
        is_k_anon, min_size, violated = self.validate_k_anonymity(final_eq_classes)

        # 计算信息损失
        info_loss = self.compute_information_loss(data, anonymized_data, quasi_identifiers)


        # 统计信息
        stats = {
            "original_records": len(data),
            "anonymized_records": len(anonymized_data),
            "equivalence_classes": len(final_eq_classes),
            "min_class_size": min_size,
            "max_class_size": max(len(v) for v in final_eq_classes.values()) if final_eq_classes else 0,
            "avg_class_size": float(np.mean([len(v) for v in final_eq_classes.values()])) if final_eq_classes else 0,
            "k_value": self.k,
            "is_k_anonymous": is_k_anon,
            "violated_classes": violated,
            "information_loss": info_loss,
            "iterations": iteration + 1,
            "final_generalization_levels": generalization_levels,
        }

        return anonymized_data, stats

    def _get_global_ranges(self, data: List[Dict], quasi_identifiers: List[str]) -> Dict[str, float]:
        """
        辅助函数：计算每个数值型准标识符的全局最大值和最小值之差（值域）。
        用于归一化数值损失。
        """
        ranges = {}
        for qi in quasi_identifiers:
            try:
                # 尝试提取所有非空数值
                values = [float(row[qi]) for row in data if row.get(qi) is not None]
                if values:
                    max_val = max(values)
                    min_val = min(values)
                    # 如果最大等于最小（所有值都一样），避免除以0，设为1
                    ranges[qi] = (max_val - min_val) if (max_val - min_val) > 0 else 1.0
            except (ValueError, TypeError):
                # 如果不是数值列（比如邮编是字符串），跳过
                pass
        return ranges

    def _parse_interval_width(self, val_str: str) -> float:
        """
        辅助函数：解析像 "20-30", "20~30" 这样的区间字符串，返回区间宽度。
        如果是单个数值，宽度为 0。
        """
        # 匹配常见的区间格式：数字-数字，数字~数字
        # 比如: 20-30 -> width 10
        match = re.match(r"\[?(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)]?", val_str)
        if match:
            low, high = map(float, match.groups())
            return abs(high - low)
        return 0.0

    def compute_information_loss(
            self,
            original_data: List[Dict],
            anonymized_data: List[Dict],
            quasi_identifiers: List[str]
    ) -> float:
        """
        改进后的信息损失率计算 (基于 NCP 思想)
        能够量化泛化（区间化）和屏蔽带来的具体损失程度。
        """
        if not original_data or not anonymized_data:
            return 0.0

        # 1. 预先计算数值列的全局范围 (用于归一化)
        global_ranges = self._get_global_ranges(original_data, quasi_identifiers)

        total_loss = 0.0
        total_cells = 0

        for orig, anon in zip(original_data, anonymized_data):
            for qi in quasi_identifiers:
                if qi not in orig or qi not in anon:
                    continue

                total_cells += 1
                orig_val = str(orig[qi])
                anon_val = str(anon[qi])

                # Case A: 完全没变 -> 损失 0
                if orig_val == anon_val:
                    continue  # loss += 0

                # Case B: 完全屏蔽 (例如 *, ?, N/A) -> 损失 1
                if anon_val in ['*', '?', 'N/A', 'nan', 'None', '']:
                    total_loss += 1.0
                    continue

                # Case C: 数值型泛化 (例如 25 -> "20-30")
                # 检查这一列是否被判定为数值列（存在于 global_ranges 中）
                if qi in global_ranges:
                    interval_width = self._parse_interval_width(anon_val)
                    if interval_width > 0:
                        # 损失 = 区间宽度 / 全局值域
                        # 例如：宽10岁 / 全局范围80岁 = 0.125
                        loss = interval_width / global_ranges[qi]
                        total_loss += min(loss, 1.0)  # 封顶为 1
                        continue

                # Case D: 字符型泛化/部分屏蔽 (例如 "123456" -> "123***")
                # 简单的启发式算法：计算 '*' 号的比例
                stars_count = anon_val.count('*')
                if stars_count > 0:
                    loss = stars_count / len(anon_val)
                    total_loss += loss
                else:
                    # 如果既不相等，又不是数值区间，也没星星，那就是完全不同的值
                    total_loss += 1.0

        # 平均损失
        return total_loss / total_cells if total_cells > 0 else 0.0


    def evaluate_privacy_risk(
        self,
        equivalence_classes: Dict[Tuple, List[Dict]],
        sensitive_attribute: str
    ) -> Dict[str, Any]:
        """
        评估隐私风险
        分析敏感属性的分布情况

        Args:
            equivalence_classes: 等价类
            sensitive_attribute: 敏感属性字段

        Returns:
            隐私风险评估报告
        """
        risk_report = {
            "total_classes": len(equivalence_classes),
            "classes_with_unique_sensitive": 0,
            "min_sensitive_diversity": float('inf'),
            "avg_sensitive_diversity": 0,
            "high_risk_classes": []
        }

        diversity_scores = []

        for key, records in equivalence_classes.items():
            # 统计敏感属性的不同值
            sensitive_values = set()
            for record in records:
                if sensitive_attribute in record:
                    val = record[sensitive_attribute]
                    if val is not None:
                        sensitive_values.add(str(val))

            diversity = len(sensitive_values)
            diversity_scores.append(diversity)

            # 检查是否只有唯一敏感值（高风险）
            if diversity == 1:
                risk_report["classes_with_unique_sensitive"] += 1
                risk_report["high_risk_classes"].append({
                    "class_key": key,
                    "size": len(records),
                    "sensitive_diversity": diversity
                })

        if diversity_scores:
            risk_report["min_sensitive_diversity"] = min(diversity_scores)
            risk_report["avg_sensitive_diversity"] = float(np.mean(diversity_scores))

        # 风险等级评估
        if risk_report["classes_with_unique_sensitive"] == 0:
            risk_report["risk_level"] = "低风险"
        elif risk_report["classes_with_unique_sensitive"] < len(equivalence_classes) * 0.3:
            risk_report["risk_level"] = "中风险"
        else:
            risk_report["risk_level"] = "高风险"

        return risk_report

