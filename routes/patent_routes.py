# routes.py
# rest api设计
from flask import Blueprint, request, jsonify
from extensions import db
from models import Patent
from schemas import patent_schema, patents_schema
from sqlalchemy import asc, desc
from datetime import datetime

# bp = Blueprint("api", __name__)
bp = Blueprint('patents', __name__, url_prefix='/patents')

def parse_int(val, default):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default




# ==================== 增（Create）====================

# 创建新专利
@bp.route("", methods=["POST"])
def create_patent():
    """
    创建新专利
    请求体示例：
    {
        "publication_number": "CN123456A",
        "title": "一种新型发明",
        "abstract": "本发明涉及...",
        "priority_country": "中国",
        "current_applicant": "某公司",
        ...
    }
    """
    try:
        data = request.get_json()

        # 验证必填字段
        if not data:
            return jsonify({"code": 4001, "message": "request body is empty"}), 400

        if not data.get("publication_number"):
            return jsonify({"code": 4002, "message": "publication_number is required"}), 400

        if not data.get("title"):
            return jsonify({"code": 4003, "message": "title is required"}), 400

        if not data.get("abstract"):
            return jsonify({"code": 4004, "message": "abstract is required"}), 400

        # 检查公告号是否已存在
        existing_patent = Patent.query.filter_by(
            publication_number=data.get("publication_number")
        ).first()
        if existing_patent:
            return jsonify({
                "code": 4005,
                "message": "patent with this publication_number already exists"
            }), 409

        # 创建新专利对象
        new_patent = Patent(
            publication_number=data.get("publication_number"),
            title=data.get("title"),
            abstract=data.get("abstract"),
            priority_country=data.get("priority_country"),
            current_applicant=data.get("current_applicant"),
            original_applicant=data.get("original_applicant"),
            inventor=data.get("inventor"),
            first_inventor=data.get("first_inventor"),
            simple_family=data.get("simple_family"),
            simple_family_number=data.get("simple_family_number"),
            grant_date=datetime.strptime(data.get("grant_date"), "%Y-%m-%d").date()
            if data.get("grant_date") else None,
            cited_patent=data.get("cited_patent"),
            cited_patent_count=data.get("cited_patent_count"),
            citing_patent=data.get("citing_patent"),
            citing_patent_count=data.get("citing_patent_count"),
            ipc_classification=data.get("ipc_classification"),
            first_inventor_address=data.get("first_inventor_address"),
            region=data.get("region"),
            topic_label=data.get("topic_label")
        )

        # 保存到数据库
        db.session.add(new_patent)
        db.session.commit()

        return jsonify({
            "code": 0,
            "message": "patent created successfully",
            "data": patent_schema.dump(new_patent)
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"code": 4006, "message": f"invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 5001, "message": f"server error: {str(e)}"}), 500


# ==================== 删（Delete）====================

# 删除指定id的专利
@bp.route("/<int:patent_id>", methods=["DELETE"])
def delete_patent(patent_id):
    """
    删除指定id的专利
    """
    try:
        patent = Patent.query.get(patent_id)

        if not patent:
            return jsonify({"code": 2001, "message": "patent not found"}), 404

        # 删除专利
        db.session.delete(patent)
        db.session.commit()

        return jsonify({
            "code": 0,
            "message": "patent deleted successfully",
            "data": {"id": patent_id}
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 5002, "message": f"server error: {str(e)}"}), 500


# 批量删除专利（可选）
@bp.route("/batch", methods=["DELETE"])
def batch_delete_patents():
    """
    批量删除专利
    请求体示例：
    {
        "ids": [1, 2, 3, 4, 5]
    }
    """
    try:
        data = request.get_json()

        if not data or not data.get("ids"):
            return jsonify({"code": 4001, "message": "ids list is required"}), 400

        ids = data.get("ids")
        if not isinstance(ids, list):
            return jsonify({"code": 4002, "message": "ids must be a list"}), 400

        # 查找并删除
        deleted_count = Patent.query.filter(Patent.id.in_(ids)).delete(
            synchronize_session=False
        )
        db.session.commit()

        return jsonify({
            "code": 0,
            "message": f"{deleted_count} patents deleted successfully",
            "data": {"deleted_count": deleted_count}
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 5002, "message": f"server error: {str(e)}"}), 500


# ==================== 改（Update）====================

# 完全更新（PUT）- 替换整个资源
@bp.route("/<int:patent_id>", methods=["PUT"])
def update_patent(patent_id):
    """
    完全更新专利信息（需要提供所有必填字段）
    请求体示例：
    {
        "publication_number": "CN123456A",
        "title": "更新后的标题",
        "abstract": "更新后的摘要",
        ...
    }
    """
    try:
        patent = Patent.query.get(patent_id)

        if not patent:
            return jsonify({"code": 2001, "message": "patent not found"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"code": 4001, "message": "request body is empty"}), 400

        # 验证必填字段
        if not data.get("publication_number"):
            return jsonify({"code": 4002, "message": "publication_number is required"}), 400

        if not data.get("title"):
            return jsonify({"code": 4003, "message": "title is required"}), 400

        if not data.get("abstract"):
            return jsonify({"code": 4004, "message": "abstract is required"}), 400

        # 检查公告号是否与其他专利冲突
        existing_patent = Patent.query.filter(
            Patent.publication_number == data.get("publication_number"),
            Patent.id != patent_id
        ).first()
        if existing_patent:
            return jsonify({
                "code": 4005,
                "message": "publication_number already exists for another patent"
            }), 409

        # 更新所有字段
        patent.publication_number = data.get("publication_number")
        patent.title = data.get("title")
        patent.abstract = data.get("abstract")
        patent.priority_country = data.get("priority_country")
        patent.current_applicant = data.get("current_applicant")
        patent.original_applicant = data.get("original_applicant")
        patent.inventor = data.get("inventor")
        patent.first_inventor = data.get("first_inventor")
        patent.simple_family = data.get("simple_family")
        patent.simple_family_number = data.get("simple_family_number")
        patent.grant_date = datetime.strptime(data.get("grant_date"), "%Y-%m-%d").date() \
            if data.get("grant_date") else None
        patent.cited_patent = data.get("cited_patent")
        patent.cited_patent_count = data.get("cited_patent_count")
        patent.citing_patent = data.get("citing_patent")
        patent.citing_patent_count = data.get("citing_patent_count")
        patent.ipc_classification = data.get("ipc_classification")
        patent.first_inventor_address = data.get("first_inventor_address")
        patent.region = data.get("region")
        patent.topic_label = data.get("topic_label")

        db.session.commit()

        return jsonify({
            "code": 0,
            "message": "patent updated successfully",
            "data": patent_schema.dump(patent)
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"code": 4006, "message": f"invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 5003, "message": f"server error: {str(e)}"}), 500


# 部分更新（PATCH）- 只更新提供的字段
@bp.route("/<int:patent_id>", methods=["PATCH"])
def partial_update_patent(patent_id):
    """
    部分更新专利信息（只需要提供要更新的字段）
    请求体示例：
    {
        "title": "只更新标题",
        "citing_patent_count": 10
    }
    """
    try:
        patent = Patent.query.get(patent_id)

        if not patent:
            return jsonify({"code": 2001, "message": "patent not found"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"code": 4001, "message": "request body is empty"}), 400

        # 如果更新公告号，检查是否冲突
        if "publication_number" in data:
            existing_patent = Patent.query.filter(
                Patent.publication_number == data.get("publication_number"),
                Patent.id != patent_id
            ).first()
            if existing_patent:
                return jsonify({
                    "code": 4005,
                    "message": "publication_number already exists for another patent"
                }), 409

        # 只更新提供的字段
        allowed_fields = [
            'publication_number', 'title', 'abstract', 'priority_country',
            'current_applicant', 'original_applicant', 'inventor',
            'first_inventor', 'simple_family', 'simple_family_number',
            'grant_date', 'cited_patent', 'cited_patent_count',
            'citing_patent', 'citing_patent_count', 'ipc_classification',
            'first_inventor_address', 'region', 'topic_label'
        ]

        for field in allowed_fields:
            if field in data:
                if field == 'grant_date' and data[field]:
                    # 处理日期字段
                    try:
                        setattr(patent, field, datetime.strptime(data[field], "%Y-%m-%d").date())
                    except ValueError:
                        return jsonify({
                            "code": 4006,
                            "message": f"invalid date format for {field}, expected YYYY-MM-DD"
                        }), 400
                else:
                    setattr(patent, field, data[field])

        db.session.commit()

        return jsonify({
            "code": 0,
            "message": "patent partially updated successfully",
            "data": patent_schema.dump(patent)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 5003, "message": f"server error: {str(e)}"}), 500


# ==================== 查（Read）- 保留原有的 ====================

# 查询某一id的专利
@bp.route("/<int:patent_id>", methods=["GET"])
def get_patent(patent_id):
    patent = Patent.query.get(patent_id)
    if not patent:
        return jsonify({"code": 2001, "message": "patent not found"}), 404
    return jsonify({"code": 0, "message": "success", "data": patent_schema.dump(patent)}), 200


@bp.route("", methods=["GET"])
def list_patents():
    """
    GET /api/v1/patents
    支持参数：
      - page: 第几页（从1开始），默认 1
      - per_page: 每页条数，默认 20，最大 200
      - publication_number: 按公告号模糊筛选
      - region: 按地区精确筛选
      - sort_by: 排序字段 (id, publication_number, grant_date, created_at)，默认 id
      - sort_dir: asc 或 desc，默认 desc
    返回 JSON:
      {
        "data": [...],
        "meta": {"page":1, "per_page":20, "total": 123}
      }
    """
    q = Patent.query

    # 筛选
    publication_number = request.args.get("publication_number")
    if publication_number:
        q = q.filter(Patent.publication_number.ilike(f"%{publication_number}%"))

    region = request.args.get("region")
    if region:
        q = q.filter(Patent.region == region)

    # 排序
    allowed_sort = {
        "id": Patent.id,
        "publication_number": Patent.publication_number,
        "grant_date": Patent.grant_date,
        "created_at": Patent.created_at
    }
    sort_by = request.args.get("sort_by", "id")
    sort_dir = request.args.get("sort_dir", "desc").lower()
    sort_col = allowed_sort.get(sort_by, Patent.id)
    if sort_dir == "asc":
        q = q.order_by(asc(sort_col))
    else:
        q = q.order_by(desc(sort_col))

    # 分页
    page = parse_int(request.args.get("page"), 1)
    per_page = parse_int(request.args.get("per_page"), 20)
    per_page = max(1, min(per_page, 200))  # 限制 per_page

    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    data = patents_schema.dump(items)
    meta = {"page": page, "per_page": per_page, "total": total}

    return jsonify({"code": 0, "message": "success", "data": data, "meta": meta}), 200


