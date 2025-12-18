"""
NRSE 隐私保护 API 路由
实现数据脱敏、K-匿名、差分隐私三种隐私保护方法
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import NRSE
import schemas
from sqlalchemy import asc, desc
from datetime import datetime
import time
import numpy as np
from sqlalchemy import text
# 导入隐私保护服务
from services import DataMaskingService
from services import KAnonymityService
from services import DifferentialPrivacyService

bp = Blueprint('nrse', __name__, url_prefix='/nrse')

def parse_int(val, default):
    """解析整数参数"""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


# ==================== 基础路由 ====================

@bp.route('/', methods=['GET'])
def index():
    """API 首页"""
    return jsonify({
        "message": "NRSE Privacy Protection API",
        "version": "1.0",
        "endpoints": {
            "masking": "/nrse/privacy/masking",
            "k_anonymity": "/nrse/privacy/k-anonymity",
            "differential_privacy": "/nrse/privacy/differential-privacy",
            "dp_query": "/nrse/privacy/dp-query"
        }
    }), 200


@bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 测试数据库连接
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500


# ==================== 1. 数据脱敏 API ====================

@bp.route('/privacy/masking', methods=['POST'])
def data_masking():
    try:
        start_time = time.time()

        # 验证请求数据
        try:
            request_data = schemas.data_masking_request_schema.load(request.get_json() or {})
        except Exception as e:
            return jsonify({
                "code": 4001,
                "message": f"Invalid request data: {str(e)}"
            }), 400

        filters = request_data.get('filters', {})
        field_rules = request_data.get('field_rules', {})
        limit = request_data.get('limit', 100)

        if not field_rules:
            return jsonify({
                "code": 4002,
                "message": "field_rules is required"
            }), 400

        # 查询数据
        query = NRSE.query

        # 应用过滤条件
        for field, value in filters.items():
            if hasattr(NRSE, field):
                query = query.filter(getattr(NRSE, field) == value)

        nrse_records = query.limit(limit).all()

        if not nrse_records:
            return jsonify({
                "code": 2001,
                "message": "No data found"
            }), 404

        # 转换为字典列表
        original_data = []
        for record in nrse_records:
            record_dict = {}
            for column in record.__table__.columns:
                record_dict[column.name] = getattr(record, column.name)
            original_data.append(record_dict)

        # 执行数据脱敏
        masking_service = DataMaskingService("hi_i'm_salt")
        masked_data = masking_service.mask_batch(original_data, field_rules)

        # 计算处理时间
        processing_time = time.time() - start_time

        # 计算脱敏率
        total_masked_chars = 0
        total_chars = 0
        for orig, masked in zip(original_data, masked_data):
            for field in field_rules.keys():
                if field in orig and orig[field]:
                    total_chars += len(str(orig[field]))
                    masked_str = str(masked[field])
                    total_masked_chars += masked_str.count('*')

        masking_rate = (total_masked_chars / total_chars * 100) if total_chars > 0 else 0

        return jsonify({
            "code": 0,
            "message": "Data masking completed successfully",
            "data": {
                "masked_records": masked_data,
                "statistics": {
                    "total_records": len(masked_data),
                    "masked_fields": list(field_rules.keys()),
                    "masking_rate": f"{masking_rate:.2f}%",
                    "processing_time": f"{processing_time:.3f}s"
                }
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 5001,
            "message": f"Data masking failed: {str(e)}"
        }), 500


@bp.route('/privacy/masking/preview', methods=['POST'])
def preview_masking():
    """
    数据脱敏预览
    无需查询数据库，直接对提供的样本数据进行脱敏预览
    """
    try:
        data = request.get_json()

        if not data or "sample_data" not in data:
            return jsonify({
                "code": 4001,
                "message": "sample_data is required"
            }), 400

        sample_data = data.get("sample_data", [])
        field_rules = data.get("field_rules", {})

        if not field_rules:
            return jsonify({
                "code": 4002,
                "message": "field_rules is required"
            }), 400

        # 执行脱敏
        masking_service = DataMaskingService()
        masked_sample = masking_service.mask_batch(sample_data, field_rules)

        # 计算脱敏率
        masking_rates = {}
        if sample_data and len(sample_data) > 0:
            for field in field_rules.keys():
                if field in sample_data[0] and sample_data[0][field]:
                    original = str(sample_data[0][field])
                    masked = str(masked_sample[0][field])
                    rate = masking_service.calculate_masking_rate(original, masked)
                    masking_rates[field] = f"{rate * 100:.1f}%"

        return jsonify({
            "code": 0,
            "message": "Preview generated",
            "data": {
                "original": sample_data[:5],
                "masked": masked_sample[:5],
                "masking_rates": masking_rates
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 5001,
            "message": f"Preview failed: {str(e)}"
        }), 500


# ==================== 2. K-匿名处理 API ====================

@bp.route('/privacy/k-anonymity', methods=['POST'])
def k_anonymity():
    """
    K-匿名处理服务

    请求体示例:
    {
        "k": 5,
        "quasi_identifiers": ["region", "age_group", "education_level"],
        "sensitive_attributes": ["income", "disease"],
        "generalization_levels": {"region": 1, "age_group": 2},
        "filters": {},
        "limit": 1000
    }
    """
    try:
        start_time = time.time()

        # 验证请求数据
        try:
            request_data = schemas.k_anonymity_request_schema.load(request.get_json() or {})
        except Exception as e:
            return jsonify({
                "code": 4001,
                "message": f"Invalid request data: {str(e)}"
            }), 400

        k = request_data.get('k', 5)
        quasi_identifiers = request_data.get('quasi_identifiers', [])
        sensitive_attributes = request_data.get('sensitive_attributes', [])
        generalization_levels = request_data.get('generalization_levels', {})
        filters = request_data.get('filters', {})
        limit = request_data.get('limit', 1000)

        # 验证 K 值
        if k < 2 or k > 100:
            return jsonify({
                "code": 4002,
                "message": "k must be between 2 and 100"
            }), 400

        if not quasi_identifiers:
            return jsonify({
                "code": 4003,
                "message": "quasi_identifiers is required"
            }), 400

        # 查询数据
        query = NRSE.query

        for field, value in filters.items():
            if hasattr(NRSE, field):
                query = query.filter(getattr(NRSE, field) == value)

        nrse_records = query.limit(limit).all()

        if not nrse_records:
            return jsonify({
                "code": 2001,
                "message": "No data found"
            }), 404

        if len(nrse_records) < k:
            return jsonify({
                "code": 4004,
                "message": f"Insufficient data: need at least {k} records, got {len(nrse_records)}"
            }), 400

        # 转换为字典列表
        original_data = []
        for record in nrse_records:
            record_dict = {}
            for column in record.__table__.columns:
                record_dict[column.name] = getattr(record, column.name)
            original_data.append(record_dict)

        # 执行 K-匿名处理（使用 NRSE 专用服务）
        k_anon_service = KAnonymityService(k=k)
        anonymized_data, stats = k_anon_service.anonymize(
            original_data,
            quasi_identifiers,
            sensitive_attributes,
            generalization_levels
        )

        # 计算处理时间
        processing_time = time.time() - start_time

        # 评估隐私级别
        # 先判断是否返回的是错误 stats
        if "error" in stats:
            return jsonify({
                "code": 5003,
                "message": f"K-anonymity failed: {stats['error']}"
            }), 500

        # 正常流程
        is_k = stats.get("is_k_anonymous", False)

        if is_k:
            if k >= 10:
                privacy_level = "high"
            elif k >= 5:
                privacy_level = "medium"
            else:
                privacy_level = "low"
        else:
            privacy_level = "insufficient"


        return jsonify({
            "code": 0,
            "message": "K-anonymity processing completed",
            "data": {
                "anonymized_records": anonymized_data,
                "statistics": stats,
                "privacy_assessment": {
                    "privacy_level": privacy_level,
                    "is_k_anonymous": stats["is_k_anonymous"],
                    "data_utility": f"{(1 - stats['information_loss']) * 100:.1f}%",
                    "k_value": k
                },
                "processing_time": f"{processing_time:.3f}s"
            }
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "code": 5002,
            "message": f"K-anonymity processing failed: {str(e)}"
        }), 500


@bp.route('/privacy/k-anonymity/validate', methods=['POST'])
def validate_k_anonymity():
    """
    验证数据集是否满足 K-匿名
    """
    try:
        data = request.get_json()

        if not data or "dataset" not in data:
            return jsonify({
                "code": 4001,
                "message": "dataset is required"
            }), 400

        dataset = data.get("dataset", [])
        k = data.get("k", 5)
        quasi_identifiers = data.get("quasi_identifiers", [])

        if not quasi_identifiers:
            return jsonify({
                "code": 4002,
                "message": "quasi_identifiers is required"
            }), 400

        # 验证 K-匿名（使用 NRSE 专用服务）
        k_anon_service = KAnonymityService(k=k)
        eq_classes = k_anon_service.build_equivalence_classes(dataset, quasi_identifiers)
        is_k_anon, min_size, violated = k_anon_service.validate_k_anonymity(eq_classes)

        return jsonify({
            "code": 0,
            "message": "Validation completed",
            "data": {
                "is_k_anonymous": is_k_anon,
                "k_value": k,
                "min_equivalence_class_size": min_size,
                "total_equivalence_classes": len(eq_classes),
                "recommendation": "Data satisfies k-anonymity" if is_k_anon
                                else f"Need further generalization (min class size: {min_size})"
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 5002,
            "message": f"Validation failed: {str(e)}"
        }), 500


# ==================== 3. 差分隐私 API ====================

@bp.route('/privacy/differential-privacy', methods=['POST'])
def differential_privacy():
    """
    差分隐私处理服务

    请求体示例:
    {
        "epsilon": 1.0,
        "mechanism": "laplace",
        "numeric_fields": ["age", "income", "score"],
        "bounds": {
            "age": [0, 100],
            "income": [0, 1000000],
            "score": [0, 100]
        },
        "filters": {},
        "limit": 1000
    }
    """
    try:
        start_time = time.time()

        # 验证请求数据
        try:
            request_data = schemas.differential_privacy_request_schema.load(request.get_json() or {})
        except Exception as e:
            return jsonify({
                "code": 4001,
                "message": f"Invalid request data: {str(e)}"
            }), 400

        epsilon = request_data.get('epsilon', 1.0)
        mechanism = request_data.get('mechanism', 'laplace')
        numeric_fields = request_data.get('numeric_fields', [])
        bounds = request_data.get('bounds', {})
        filters = request_data.get('filters', {})
        limit = request_data.get('limit', 1000)

        # 验证 epsilon
        if epsilon < 0.1 or epsilon > 10.0:
            return jsonify({
                "code": 4002,
                "message": "epsilon must be between 0.1 and 10.0"
            }), 400

        if not numeric_fields:
            return jsonify({
                "code": 4003,
                "message": "numeric_fields is required"
            }), 400

        if mechanism not in ['laplace', 'gaussian']:
            return jsonify({
                "code": 4004,
                "message": "mechanism must be 'laplace' or 'gaussian'"
            }), 400

        # 查询数据
        query = NRSE.query

        for field, value in filters.items():
            if hasattr(NRSE, field):
                query = query.filter(getattr(NRSE, field) == value)

        nrse_records = query.limit(limit).all()

        if not nrse_records:
            return jsonify({
                "code": 2001,
                "message": "No data found"
            }), 404

        # 转换为字典列表
        original_data = []
        for record in nrse_records:
            record_dict = {}
            for column in record.__table__.columns:
                value = getattr(record, column.name)
                # 处理日期时间类型
                if isinstance(value, datetime):
                    value = value.isoformat()
                record_dict[column.name] = value
            original_data.append(record_dict)

        # 准备 bounds
        field_bounds = {}
        for field in numeric_fields:
            if field in bounds:
                field_bounds[field] = tuple(bounds[field])
            else:
                # 自动计算 bounds
                values = []
                for r in original_data:
                    if field in r and r[field] is not None:
                        try:
                            values.append(float(r[field]))
                        except (ValueError, TypeError):
                            pass

                if values:
                    field_bounds[field] = (min(values), max(values))
                else:
                    field_bounds[field] = (0, 100)

        # 执行差分隐私处理（使用 NRSE 专用服务）
        dp_service = DifferentialPrivacyService(epsilon=epsilon, delta=1e-5)
        privatized_data, dp_stats = dp_service.privatize_enterprise_data(
            original_data,
            numeric_fields,
            mechanism,
            bounds
        )

        # 计算效用损失（从 dp_stats 中获取）
        utility_metrics = dp_stats.get("field_metrics", {})

        # 计算处理时间
        processing_time = time.time() - start_time

        # 评估隐私级别
        if epsilon <= 0.5:
            privacy_level = "high"
        elif epsilon <= 2.0:
            privacy_level = "medium"
        else:
            privacy_level = "low"

        # 计算平均相对误差作为数据可用性指标
        if utility_metrics:
            avg_relative_error = np.mean([m["relative_error"] for m in utility_metrics.values()])
            # data_utility = max(0, 1 - avg_relative_error)
            data_utility = 1 / (1 + avg_relative_error)
        else:
            data_utility = 0

        return jsonify({
            "code": 0,
            "message": "Differential privacy processing completed",
            "data": {
                "privatized_records": privatized_data,
                "statistics": {
                    "total_records": len(privatized_data),
                    "epsilon": epsilon,
                    "mechanism": mechanism,
                    "privatized_fields": numeric_fields
                },
                "privacy_assessment": {
                    "privacy_level": privacy_level,
                    "privacy_budget": epsilon,
                    "data_utility": f"{data_utility * 100:.1f}%"
                },
                "utility_metrics": utility_metrics,
                "processing_time": f"{processing_time:.3f}s"
            }
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "code": 5003,
            "message": f"Differential privacy processing failed: {str(e)}"
        }), 500


@bp.route('/privacy/dp-query', methods=['POST'])
def dp_query():
    """
    差分隐私查询服务
    支持计数、求和、平均值、直方图等统计查询

    请求体示例:
    {
        "query_type": "count",
        "field": "age",
        "filters": {"region": "北京"},
        "epsilon": 1.0,
        "mechanism": "laplace"
    }
    """
    try:
        # 验证请求数据
        try:
            request_data = schemas.dp_query_request_schema.load(request.get_json() or {})
        except Exception as e:
            return jsonify({
                "code": 4001,
                "message": f"Invalid request data: {str(e)}"
            }), 400

        query_type = request_data.get('query_type')
        epsilon = request_data.get('epsilon', 1.0)
        mechanism = request_data.get('mechanism', 'laplace')
        filters = request_data.get('filters', {})
        field = request_data.get('field')

        # 验证查询类型
        if query_type not in ['count', 'sum', 'avg', 'histogram']:
            return jsonify({
                "code": 4002,
                "message": "query_type must be one of: count, sum, avg, histogram"
            }), 400

        # 构建查询
        query = NRSE.query
        for f, value in filters.items():
            if hasattr(NRSE, f):
                query = query.filter(getattr(NRSE, f) == value)

        # 执行查询获取记录
        records = query.all()

        if not records:
            return jsonify({
                "code": 2001,
                "message": "No data found"
            }), 404

        # 创建差分隐私服务（使用 NRSE 专用服务）
        dp_service = DifferentialPrivacyService(epsilon=epsilon, delta=1e-5)

        # 转换为字典列表（统一处理，避免重复代码）
        records_list = []
        for r in records:
            record_dict = {}
            for column in r.__table__.columns:
                value = getattr(r, column.name)
                # 处理日期时间类型
                if isinstance(value, datetime):
                    value = value.isoformat()
                record_dict[column.name] = value
            records_list.append(record_dict)

        # 执行不同类型的查询（使用 NRSE 专用方法）
        if query_type == "count":
            noisy_count, query_info = dp_service.query_count(records_list, mechanism=mechanism)

            result = {
                "query_type": "count",
                "noisy_result": noisy_count,
                "epsilon": epsilon,
                "mechanism": mechanism,
                "query_info": query_info
            }

        elif query_type in ["sum", "avg"]:
            if not field:
                return jsonify({
                    "code": 4003,
                    "message": "field is required for sum/avg queries"
                }), 400

            if not hasattr(NRSE, field):
                return jsonify({
                    "code": 4004,
                    "message": f"field '{field}' does not exist"
                }), 400

            if query_type == "sum":
                noisy_sum, query_info = dp_service.query_sum(
                    records_list, field, mechanism=mechanism
                )
                result = {
                    "query_type": "sum",
                    "noisy_result": round(noisy_sum, 2),
                    "field": field,
                    "epsilon": epsilon,
                    "mechanism": mechanism,
                    "query_info": query_info
                }
            else:  # avg
                noisy_avg, query_info = dp_service.query_average(
                    records_list, field, mechanism=mechanism
                )
                result = {
                    "query_type": "average",
                    "noisy_result": round(noisy_avg, 2),
                    "field": field,
                    "epsilon": epsilon,
                    "mechanism": mechanism,
                    "query_info": query_info
                }

        elif query_type == "histogram":
            if not field:
                return jsonify({
                    "code": 4003,
                    "message": "field is required for histogram query"
                }), 400

            if not hasattr(NRSE, field):
                return jsonify({
                    "code": 4004,
                    "message": f"field '{field}' does not exist"
                }), 400

            histogram, query_info = dp_service.query_histogram(
                records_list, field, mechanism=mechanism
            )

            result = {
                "query_type": "histogram",
                "noisy_result": histogram,
                "field": field,
                "epsilon": epsilon,
                "mechanism": mechanism,
                "query_info": query_info
            }

        return jsonify({
            "code": 0,
            "message": "Query completed successfully",
            "data": result
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "code": 5003,
            "message": f"Query failed: {str(e)}"
        }), 500


# ==================== 统计和监控 API ====================

@bp.route('/privacy/stats', methods=['GET'])
def privacy_stats():
    """
    获取隐私保护统计信息
    """
    try:
        # 获取数据集基本信息
        total_records = NRSE.query.count()

        # 获取数值字段的统计信息
        numeric_fields = []
        for column in NRSE.__table__.columns:
            if column.type.python_type in [int, float]:
                numeric_fields.append(column.name)

        return jsonify({
            "code": 0,
            "message": "Statistics retrieved successfully",
            "data": {
                "total_records": total_records,
                "numeric_fields": numeric_fields,
                "supported_methods": [
                    "data_masking",
                    "k_anonymity",
                    "differential_privacy"
                ],
                "privacy_parameters": {
                    "masking": {
                        "supported_types": ["name", "phone", "email", "id_card", "address", "custom", "hash"]
                    },
                    "k_anonymity": {
                        "min_k": 2,
                        "max_k": 100,
                        "recommended_k": 5
                    },
                    "differential_privacy": {
                        "min_epsilon": 0.1,
                        "max_epsilon": 10.0,
                        "recommended_epsilon": 1.0,
                        "mechanisms": ["laplace", "gaussian"]
                    }
                }
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 5004,
            "message": f"Failed to retrieve statistics: {str(e)}"
        }), 500


# ==================== 错误处理 ====================

@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "code": 404,
        "message": "Resource not found"
    }), 404


@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        "code": 500,
        "message": "Internal server error"
    }), 500