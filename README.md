[api_documentation.md](https://github.com/user-attachments/files/24233605/api_documentation.md)
# 隐私数据保护平台 API 文档

## 系统概述

基于 **Flask + SQLAlchemy + Marshmallow + MySQL** 构建的隐私数据保护平台，提供三种隐私保护方法：

1. **数据脱敏** (Data Masking)
2. **K-匿名处理** (K-Anonymity based on KACA)
3. **差分隐私** (Differential Privacy)

---

## 快速开始

### 1. 安装依赖

```bash
pip install flask flask-sqlalchemy flask-marshmallow pymysql flask-cors numpy scikit-learn
```

### 2. 配置数据库

在 `config.py` 中配置 MySQL 连接：

```python
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_password"
MYSQL_DATABASE = "privacy_platform"
```

### 3. 创建数据库

```sql
CREATE DATABASE privacy_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

---

## API 接口文档

### 基础信息

- **Base URL**: `http://localhost:5000/api/v1`
- **Content-Type**: `application/json`
- **编码**: UTF-8

---

## 一、数据脱敏服务

### 1.1 批量数据脱敏

**接口**: `POST /api/v1/privacy/masking`

**功能**: 对指定字段进行数据脱敏处理

**请求体**:
```json
{
  "table": "patents",
  "filters": {
    "region": "北京"
  },
  "field_rules": {
    "first_inventor": "name",
    "first_inventor_address": "address",
    "publication_number": "custom"
  },
  "limit": 100
}
```

**参数说明**:
- `table`: 表名（默认 patents）
- `filters`: 筛选条件（可选）
- `field_rules`: 脱敏规则字典
  - 支持类型: `phone`, `email`, `id_card`, `name`, `address`, `custom`, `hash`
- `limit`: 返回记录数限制

**响应示例**:
```json
{
  "code": 0,
  "message": "data masking completed successfully",
  "data": {
    "masked_records": [
      {
        "id": 1,
        "first_inventor": "张*",
        "first_inventor_address": "北京市****",
        "publication_number": "CN1***********34"
      }
    ],
    "statistics": {
      "total_records": 100,
      "masked_fields": ["first_inventor", "first_inventor_address"],
      "processing_time": "0.123s"
    }
  }
}
```

### 1.2 脱敏效果预览

**接口**: `POST /api/v1/privacy/masking/preview`

**功能**: 预览脱敏效果，不保存到数据库

**请求体**:
```json
{
  "sample_data": [
    {
      "name": "张三",
      "phone": "13812345678",
      "email": "zhangsan@example.com"
    }
  ],
  "field_rules": {
    "name": "name",
    "phone": "phone",
    "email": "email"
  }
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "preview generated",
  "data": {
    "original": [...],
    "masked": [
      {
        "name": "张*",
        "phone": "138****5678",
        "email": "z***@example.com"
      }
    ],
    "masking_rates": {
      "name": "50.0%",
      "phone": "36.4%",
      "email": "33.3%"
    }
  }
}
```

---

## 二、K-匿名处理服务

### 2.1 K-匿名处理

**接口**: `POST /api/v1/privacy/k-anonymity`

**功能**: 使用 KACA 算法对数据进行 K-匿名处理

**请求体**:
```json
{
  "table": "patents",
  "k": 5,
  "quasi_identifiers": ["region", "ipc_classification"],
  "sensitive_attributes": ["first_inventor"],
  "generalization_levels": {
    "region": 1
  },
  "filters": {},
  "limit": 1000
}
```

**参数说明**:
- `k`: K值（默认5，范围2-100）
- `quasi_identifiers`: 准标识符字段列表
- `sensitive_attributes`: 敏感属性字段列表
- `generalization_levels`: 泛化级别配置
- `limit`: 处理记录数限制

**响应示例**:
```json
{
  "code": 0,
  "message": "k-anonymity processing completed",
  "data": {
    "anonymized_records": [...],
    "statistics": {
      "original_records": 1000,
      "anonymized_records": 1000,
      "equivalence_classes": 150,
      "min_class_size": 5,
      "max_class_size": 25,
      "avg_class_size": 6.67,
      "k_value": 5,
      "is_k_anonymous": true,
      "information_loss": 0.23
    },
    "privacy_assessment": {
      "privacy_level": "medium",
      "is_k_anonymous": true,
      "data_utility": "77.0%"
    },
    "processing_time": "0.456s"
  }
}
```

### 2.2 K-匿名验证

**接口**: `POST /api/v1/privacy/k-anonymity/validate`

**功能**: 验证数据集是否满足 K-匿名

**请求体**:
```json
{
  "dataset": [
    {"age": "20-30", "region": "北京市", "job": "工程师"},
    {"age": "20-30", "region": "北京市", "job": "工程师"}
  ],
  "k": 2,
  "quasi_identifiers": ["age", "region", "job"]
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "validation completed",
  "data": {
    "is_k_anonymous": true,
    "k_value": 2,
    "min_equivalence_class_size": 2,
    "total_equivalence_classes": 1,
    "recommendation": "Data satisfies k-anonymity"
  }
}
```

---

## 三、差分隐私服务

### 3.1 数据集差分隐私处理

**接口**: `POST /api/v1/privacy/differential-privacy`

**功能**: 对数值字段添加差分隐私噪声

**请求体**:
```json
{
  "table": "patents",
  "epsilon": 1.0,
  "mechanism": "laplace",
  "numeric_fields": ["cited_patent_count", "citing_patent_count"],
  "bounds": {
    "cited_patent_count": [0, 1000],
    "citing_patent_count": [0, 1000]
  },
  "filters": {},
  "limit": 1000
}
```

**参数说明**:
- `epsilon`: 隐私预算（0.1-10.0，越小隐私越强）
- `mechanism`: 噪声机制（`laplace` 或 `gaussian`）
- `numeric_fields`: 需要添加噪声的数值字段
- `bounds`: 字段取值范围（用于计算敏感度）

**响应示例**:
```json
{
  "code": 0,
  "message": "differential privacy processing completed",
  "data": {
    "privatized_records": [...],
    "statistics": {
      "total_records": 1000,
      "epsilon": 1.0,
      "mechanism": "laplace",
      "privatized_fields": ["cited_patent_count", "citing_patent_count"]
    },
    "privacy_assessment": {
      "privacy_level": "medium",
      "privacy_budget": 1.0,
      "data_utility": "85.3%"
    },
    "utility_metrics": {
      "cited_patent_count": {
        "mae": 12.5,
        "mse": 234.6,
        "rmse": 15.3,
        "relative_error": 0.08
      }
    },
    "processing_time": "0.234s"
  }
}
```

### 3.2 差分隐私统计查询

**接口**: `POST /api/v1/privacy/differential-privacy/query`

**功能**: 执行带差分隐私保护的统计查询

**请求体**:
```json
{
  "query_type": "count",
  "table": "patents",
  "field": "cited_patent_count",
  "filters": {"region": "北京"},
  "epsilon": 1.0,
  "mechanism": "laplace"
}
```

**query_type 支持类型**:
- `count`: 计数查询
- `sum`: 求和查询
- `avg`: 平均值查询
- `histogram`: 直方图查询

**响应示例（计数查询）**:
```json
{
  "code": 0,
  "message": "query completed",
  "data": {
    "query_type": "count",
    "noisy_result": 523,
    "epsilon": 1.0,
    "mechanism": "laplace"
  }
}
```

**响应示例（直方图查询）**:
```json
{
  "code": 0,
  "message": "query completed",
  "data": {
    "query_type": "histogram",
    "noisy_result": {
      "工程师": 345,
      "经理": 178,
      "研究员": 89
    },
    "field": "job",
    "epsilon": 1.0
  }
}
```

---

## 四、隐私保护日志

### 4.1 查询处理日志

**接口**: `GET /api/v1/privacy/logs`

**参数**:
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认20）
- `method`: 按方法筛选（可选: `data_masking`, `k_anonymity`, `differential_privacy`）

**示例**:
```
GET /api/v1/privacy/logs?page=1&per_page=20&method=k_anonymity
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "logs": [
      {
        "id": 1,
        "method": "k_anonymity",
        "table_name": "patents",
        "record_count": 1000,
        "parameters": {...},
        "privacy_level": "medium",
        "data_utility": 0.77,
        "processing_time": 0.456,
        "created_at": "2024-01-15T10:30:00"
      }
    ],
    "total": 50,
    "page": 1,
    "per_page": 20
  }
}
```

### 4.2 统计信息

**接口**: `GET /api/v1/privacy/logs/statistics`

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "method_usage": {
      "data_masking": 150,
      "k_anonymity": 80,
      "differential_privacy": 120
    },
    "average_processing_time": "0.325s",
    "total_processed_records": 350000,
    "privacy_level_distribution": {
      "high": 200,
      "medium": 100,
      "low": 50
    }
  }
}
```

---

## 测试示例

### Python 测试脚本

```python
import requests
import json

BASE_URL = "http://localhost:5000/api/v1"

# 1. 测试数据脱敏
def test_data_masking():
    url = f"{BASE_URL}/privacy/masking"
    payload = {
        "table": "patents",
        "field_rules": {
            "first_inventor": "name",
            "first_inventor_address": "address"
        },
        "limit": 10
    }
    
    response = requests.post(url, json=payload)
    print("数据脱敏结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 2. 测试K-匿名
def test_k_anonymity():
    url = f"{BASE_URL}/privacy/k-anonymity"
    payload = {
        "k": 5,
        "quasi_identifiers": ["region", "ipc_classification"],
        "sensitive_attributes": ["first_inventor"],
        "limit": 100
    }
    
    response = requests.post(url, json=payload)
    print("\nK-匿名处理结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 3. 测试差分隐私
def test_differential_privacy():
    url = f"{BASE_URL}/privacy/differential-privacy"
    payload = {
        "epsilon": 1.0,
        "mechanism": "laplace",
        "numeric_fields": ["cited_patent_count"],
        "bounds": {"cited_patent_count": [0, 1000]},
        "limit": 50
    }
    
    response = requests.post(url, json=payload)
    print("\n差分隐私处理结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 4. 测试差分隐私查询
def test_dp_query():
    url = f"{BASE_URL}/privacy/differential-privacy/query"
    payload = {
        "query_type": "count",
        "table": "patents",
        "epsilon": 1.0,
        "filters": {}
    }
    
    response = requests.post(url, json=payload)
    print("\n差分隐私查询结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_data_masking()
    test_k_anonymity()
    test_differential_privacy()
    test_dp_query()
```

### cURL 测试命令

```bash
# 1. 数据脱敏
curl -X POST http://localhost:5000/api/v1/privacy/masking \
  -H "Content-Type: application/json" \
  -d '{
    "field_rules": {
      "first_inventor": "name",
      "first_inventor_address": "address"
    },
    "limit": 10
  }'

# 2. K-匿名处理
curl -X POST http://localhost:5000/api/v1/privacy/k-anonymity \
  -H "Content-Type: application/json" \
  -d '{
    "k": 5,
    "quasi_identifiers": ["region", "ipc_classification"],
    "limit": 100
  }'

# 3. 差分隐私处理
curl -X POST http://localhost:5000/api/v1/privacy/differential-privacy \
  -H "Content-Type: application/json" \
  -d '{
    "epsilon": 1.0,
    "mechanism": "laplace",
    "numeric_fields": ["cited_patent_count"],
    "bounds": {"cited_patent_count": [0, 1000]},
    "limit": 50
  }'

# 4. 查询日志
curl -X GET "http://localhost:5000/api/v1/privacy/logs?page=1&per_page=10"
```

---

## 隐私保护方法对比

| 特性 | 数据脱敏 | K-匿名 | 差分隐私 |
|-----|---------|--------|---------|
| **隐私保护强度** | 中等 | 高 | 非常高 |
| **数据可用性** | 高（80-90%） | 中等（60-80%） | 中等（70-85%） |
| **适用场景** | 个人信息保护 | 再识别攻击防护 | 统计查询保护 |
| **处理速度** | 快 | 中等 | 快 |
| **可逆性** | 不可逆（哈希）/可逆（脱敏） | 不可逆 | 不可逆 |
| **数学证明** | 无 | 无 | 有（ε-差分隐私） |

---

## 常见问题

### 1. 如何选择合适的K值？
- K=2-3: 弱隐私保护
- K=5-10: 标准隐私保护（推荐）
- K>10: 强隐私保护（信息损失较大）

### 2. 如何选择epsilon值？
- ε≤0.5: 强隐私保护
- ε=1.0: 标准隐私保护（推荐）
- ε≥2.0: 弱隐私保护

### 3. 信息损失如何计算？
信息损失 = (泛化/修改的值数量) / (总值数量)

---

## 扩展功能建议

1. **数据合成**: 使用生成模型创建合成数据集
2. **L-多样性**: 在K-匿名基础上增加敏感属性多样性
3. **T-接近性**: 确保敏感属性分布接近原始分布
4. **联邦学习**: 支持多方协作的隐私保护机器学习
5. **同态加密**: 支持加密数据上的计算

---

## 参考资料

- [差分隐私理论](https://en.wikipedia.org/wiki/Differential_privacy)
- [K-匿名算法](https://en.wikipedia.org/wiki/K-anonymity)
- [数据脱敏标准](https://www.gb688.cn/bzgk/gb/newGbInfo?hcno=...)
