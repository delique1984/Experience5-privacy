"""
Marshmallow Schemas for serialization/deserialization
"""
from marshmallow import Schema, fields
from extensions import ma
from models.patent import Patent



# ==================== Patent Schema ====================

class PatentSchema(ma.SQLAlchemyAutoSchema):
    """专利数据Schema"""

    class Meta:
        model = Patent
        load_instance = True
        include_fk = True
        # 包含所有字段
        fields = (
            'id', 'publication_number', 'title', 'abstract',
            'priority_country', 'current_applicant', 'original_applicant',
            'inventor', 'first_inventor', 'simple_family',
            'simple_family_number', 'grant_date', 'cited_patent',
            'cited_patent_count', 'citing_patent', 'citing_patent_count',
            'ipc_classification', 'first_inventor_address', 'region',
            'topic_label', 'created_at'
        )

    # 日期字段格式化
    grant_date = fields.Date(format='%Y-%m-%d', allow_none=True)
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')



# ==================== Request/Response Schemas ====================

class DataMaskingRequestSchema(Schema):
    """数据脱敏请求Schema"""
    table = fields.String(required=False, load_default='nrse')
    filters = fields.Dict(required=False, load_default={})
    field_rules = fields.Dict(required=True)
    limit = fields.Integer(required=False, load_default=100)


class DataMaskingResponseSchema(Schema):
    """数据脱敏响应Schema"""
    code = fields.Integer()
    message = fields.String()
    data = fields.Dict()


from marshmallow import Schema, fields, validate

class KAnonymityRequestSchema(Schema):
    """
    K-匿名请求 Schema（最终版本）
    """

    # 要操作的数据表（未来可扩展）
    table = fields.String(
        required=False,
        load_default="nrse",
        validate=validate.OneOf(["nrse", "patents"])
    )

    # k 值
    k = fields.Integer(
        required=False,
        load_default=5,
        validate=validate.Range(min=2, max=100)
    )

    # 准标识符字段（必须）
    quasi_identifiers = fields.List(
        fields.String(),
        required=True
    )

    # 敏感字段
    sensitive_attributes = fields.List(
        fields.String(),
        required=False,
        load_default=[]
    )

    # 泛化级别，例如 {"revenue_2023":2}
    generalization_levels = fields.Dict(
        required=False,
        load_default={}
    )

    # 查询过滤条件，例如 {"region": "华东"}
    filters = fields.Dict(
        required=False,
        load_default={}
    )

    # 最大记录数限制
    limit = fields.Integer(
        required=False,
        load_default=1000,
        validate=validate.Range(min=10, max=5000)
    )


class KAnonymityResponseSchema(Schema):
    code = fields.Integer()
    message = fields.String()
    data = fields.Dict()


class DifferentialPrivacyRequestSchema(Schema):
    """差分隐私请求Schema"""

    epsilon = fields.Float(
        required=False,
        load_default=1.0,
        validate=validate.Range(min=0.1, max=10.0)
    )

    mechanism = fields.String(
        required=False,
        load_default="laplace",
        validate=validate.OneOf(["laplace", "gaussian"])
    )

    numeric_fields = fields.List(
        fields.String(),
        required=True,
        error_messages={"required": "numeric_fields is required"}
    )

    bounds = fields.Dict(
        keys=fields.String(),
        values=fields.List(fields.Float(), validate=validate.Length(equal=2)),
        required=False,
        load_default={}
    )

    filters = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        required=False,
        load_default={}
    )

    limit = fields.Integer(required=False, load_default=1000)



class DifferentialPrivacyResponseSchema(Schema):
    """差分隐私响应Schema"""
    code = fields.Integer()
    message = fields.String()
    data = fields.Dict()


class DPQueryRequestSchema(Schema):
    """差分隐私查询请求Schema"""

    query_type = fields.String(
        required=True,
        validate=validate.OneOf(["count", "sum", "avg", "histogram"])
    )

    field = fields.String(required=False, allow_none=True)

    filters = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        required=False,
        load_default={}
    )

    epsilon = fields.Float(
        required=False,
        load_default=1.0,
        validate=validate.Range(min=0.1, max=10.0)
    )

    mechanism = fields.String(
        required=False,
        load_default="laplace",
        validate=validate.OneOf(["laplace", "gaussian"])
    )

    bins = fields.List(
        fields.Float(),
        required=False,
        allow_none=True,
        load_default=None,
        metadata={"description": "only required when query_type = histogram"}
    )


# ==================== Statistics Schema ====================

class PrivacyStatisticsSchema(Schema):
    """隐私统计信息Schema"""

    total_records = fields.Integer()
    numeric_fields = fields.List(fields.String())

    supported_methods = fields.List(fields.String())

    privacy_parameters = fields.Dict()


# ==================== 实例化 Schemas ====================

# 单个对象
patent_schema = PatentSchema()


# 多个对象（列表）
patents_schema = PatentSchema(many=True)


# 请求/响应
data_masking_request_schema = DataMaskingRequestSchema()
data_masking_response_schema = DataMaskingResponseSchema()
k_anonymity_request_schema = KAnonymityRequestSchema()
k_anonymity_response_schema = KAnonymityResponseSchema()
differential_privacy_request_schema = DifferentialPrivacyRequestSchema()
differential_privacy_response_schema = DifferentialPrivacyResponseSchema()
dp_query_request_schema = DPQueryRequestSchema()
privacy_statistics_schema = PrivacyStatisticsSchema()