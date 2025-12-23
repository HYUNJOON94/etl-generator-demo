"""
샘플 데이터베이스 메타데이터
데모용 PostgreSQL 및 MySQL 스키마
"""

SAMPLE_POSTGRES_ECOMMERCE = {
    "db_type": "PostgreSQL",
    "db_version": "15.0",
    "schema_summary": {
        "tables": [
            {
                "table_name": "users",
                "description": "사용자 계정 정보",
                "columns": [
                    {"column_name": "id", "data_type": "SERIAL", "nullable": False, "description": "사용자 고유 ID", "primary_key": True},
                    {"column_name": "email", "data_type": "VARCHAR(255)", "nullable": False, "description": "이메일 주소"},
                    {"column_name": "username", "data_type": "VARCHAR(100)", "nullable": False, "description": "사용자명"},
                    {"column_name": "created_at", "data_type": "TIMESTAMP", "nullable": False, "description": "가입일"},
                    {"column_name": "status", "data_type": "VARCHAR(20)", "nullable": False, "description": "계정 상태 (active, inactive, suspended)"},
                    {"column_name": "is_deleted", "data_type": "BOOLEAN", "nullable": False, "description": "삭제 여부 (soft delete)"}
                ]
            },
            {
                "table_name": "products",
                "description": "상품 정보",
                "columns": [
                    {"column_name": "id", "data_type": "SERIAL", "nullable": False, "description": "상품 고유 ID", "primary_key": True},
                    {"column_name": "name", "data_type": "VARCHAR(255)", "nullable": False, "description": "상품명"},
                    {"column_name": "category_id", "data_type": "INTEGER", "nullable": False, "description": "카테고리 ID", "foreign_key": {"ref_table": "categories", "ref_column": "id"}},
                    {"column_name": "price", "data_type": "DECIMAL(10,2)", "nullable": False, "description": "가격"},
                    {"column_name": "stock", "data_type": "INTEGER", "nullable": False, "description": "재고 수량"},
                    {"column_name": "is_deleted", "data_type": "BOOLEAN", "nullable": False, "description": "삭제 여부"}
                ]
            },
            {
                "table_name": "categories",
                "description": "상품 카테고리",
                "columns": [
                    {"column_name": "id", "data_type": "SERIAL", "nullable": False, "description": "카테고리 고유 ID", "primary_key": True},
                    {"column_name": "name", "data_type": "VARCHAR(100)", "nullable": False, "description": "카테고리명"},
                    {"column_name": "parent_id", "data_type": "INTEGER", "nullable": True, "description": "상위 카테고리 ID", "foreign_key": {"ref_table": "categories", "ref_column": "id"}}
                ]
            },
            {
                "table_name": "orders",
                "description": "주문 정보",
                "columns": [
                    {"column_name": "id", "data_type": "SERIAL", "nullable": False, "description": "주문 고유 ID", "primary_key": True},
                    {"column_name": "user_id", "data_type": "INTEGER", "nullable": False, "description": "주문자 ID", "foreign_key": {"ref_table": "users", "ref_column": "id"}},
                    {"column_name": "order_date", "data_type": "TIMESTAMP", "nullable": False, "description": "주문일시"},
                    {"column_name": "total_amount", "data_type": "DECIMAL(12,2)", "nullable": False, "description": "총 주문금액"},
                    {"column_name": "status", "data_type": "VARCHAR(30)", "nullable": False, "description": "주문 상태 (pending, confirmed, shipped, delivered, cancelled)"},
                    {"column_name": "shipping_address", "data_type": "TEXT", "nullable": True, "description": "배송지 주소"}
                ]
            },
            {
                "table_name": "order_items",
                "description": "주문 상세 항목",
                "columns": [
                    {"column_name": "id", "data_type": "SERIAL", "nullable": False, "description": "항목 고유 ID", "primary_key": True},
                    {"column_name": "order_id", "data_type": "INTEGER", "nullable": False, "description": "주문 ID", "foreign_key": {"ref_table": "orders", "ref_column": "id"}},
                    {"column_name": "product_id", "data_type": "INTEGER", "nullable": False, "description": "상품 ID", "foreign_key": {"ref_table": "products", "ref_column": "id"}},
                    {"column_name": "quantity", "data_type": "INTEGER", "nullable": False, "description": "주문 수량"},
                    {"column_name": "unit_price", "data_type": "DECIMAL(10,2)", "nullable": False, "description": "단가"}
                ]
            }
        ],
        "relationships": [
            "products.category_id → categories.id",
            "orders.user_id → users.id",
            "order_items.order_id → orders.id",
            "order_items.product_id → products.id",
            "categories.parent_id → categories.id"
        ]
    },
    "constraints": {
        "soft_delete_rule": "is_deleted = false",
        "valid_status_values": ["active", "inactive", "suspended", "pending", "confirmed", "shipped", "delivered", "cancelled"],
        "mandatory_filters": ["is_deleted = false"]
    }
}

SAMPLE_MYSQL_HR = {
    "db_type": "MySQL",
    "db_version": "8.0",
    "schema_summary": {
        "tables": [
            {
                "table_name": "employees",
                "description": "직원 정보",
                "columns": [
                    {"column_name": "id", "data_type": "INT AUTO_INCREMENT", "nullable": False, "description": "직원 고유 ID", "primary_key": True},
                    {"column_name": "name", "data_type": "VARCHAR(100)", "nullable": False, "description": "직원명"},
                    {"column_name": "email", "data_type": "VARCHAR(255)", "nullable": False, "description": "이메일"},
                    {"column_name": "department_id", "data_type": "INT", "nullable": False, "description": "부서 ID", "foreign_key": {"ref_table": "departments", "ref_column": "id"}},
                    {"column_name": "position", "data_type": "VARCHAR(100)", "nullable": False, "description": "직책"},
                    {"column_name": "salary", "data_type": "DECIMAL(12,2)", "nullable": False, "description": "급여"},
                    {"column_name": "hire_date", "data_type": "DATE", "nullable": False, "description": "입사일"},
                    {"column_name": "manager_id", "data_type": "INT", "nullable": True, "description": "상사 ID", "foreign_key": {"ref_table": "employees", "ref_column": "id"}},
                    {"column_name": "status", "data_type": "ENUM('active', 'resigned', 'on_leave')", "nullable": False, "description": "재직 상태"}
                ]
            },
            {
                "table_name": "departments",
                "description": "부서 정보",
                "columns": [
                    {"column_name": "id", "data_type": "INT AUTO_INCREMENT", "nullable": False, "description": "부서 고유 ID", "primary_key": True},
                    {"column_name": "name", "data_type": "VARCHAR(100)", "nullable": False, "description": "부서명"},
                    {"column_name": "budget", "data_type": "DECIMAL(15,2)", "nullable": True, "description": "예산"},
                    {"column_name": "head_id", "data_type": "INT", "nullable": True, "description": "부서장 ID", "foreign_key": {"ref_table": "employees", "ref_column": "id"}}
                ]
            },
            {
                "table_name": "attendance",
                "description": "출퇴근 기록",
                "columns": [
                    {"column_name": "id", "data_type": "INT AUTO_INCREMENT", "nullable": False, "description": "기록 ID", "primary_key": True},
                    {"column_name": "employee_id", "data_type": "INT", "nullable": False, "description": "직원 ID", "foreign_key": {"ref_table": "employees", "ref_column": "id"}},
                    {"column_name": "date", "data_type": "DATE", "nullable": False, "description": "날짜"},
                    {"column_name": "check_in", "data_type": "TIME", "nullable": True, "description": "출근 시간"},
                    {"column_name": "check_out", "data_type": "TIME", "nullable": True, "description": "퇴근 시간"},
                    {"column_name": "status", "data_type": "ENUM('present', 'absent', 'late', 'half_day')", "nullable": False, "description": "출근 상태"}
                ]
            },
            {
                "table_name": "projects",
                "description": "프로젝트 정보",
                "columns": [
                    {"column_name": "id", "data_type": "INT AUTO_INCREMENT", "nullable": False, "description": "프로젝트 ID", "primary_key": True},
                    {"column_name": "name", "data_type": "VARCHAR(200)", "nullable": False, "description": "프로젝트명"},
                    {"column_name": "department_id", "data_type": "INT", "nullable": False, "description": "담당 부서 ID", "foreign_key": {"ref_table": "departments", "ref_column": "id"}},
                    {"column_name": "start_date", "data_type": "DATE", "nullable": False, "description": "시작일"},
                    {"column_name": "end_date", "data_type": "DATE", "nullable": True, "description": "종료일"},
                    {"column_name": "status", "data_type": "ENUM('planning', 'in_progress', 'completed', 'on_hold')", "nullable": False, "description": "프로젝트 상태"}
                ]
            },
            {
                "table_name": "project_members",
                "description": "프로젝트 참여 인원",
                "columns": [
                    {"column_name": "id", "data_type": "INT AUTO_INCREMENT", "nullable": False, "description": "ID", "primary_key": True},
                    {"column_name": "project_id", "data_type": "INT", "nullable": False, "description": "프로젝트 ID", "foreign_key": {"ref_table": "projects", "ref_column": "id"}},
                    {"column_name": "employee_id", "data_type": "INT", "nullable": False, "description": "직원 ID", "foreign_key": {"ref_table": "employees", "ref_column": "id"}},
                    {"column_name": "role", "data_type": "VARCHAR(50)", "nullable": False, "description": "역할"}
                ]
            }
        ],
        "relationships": [
            "employees.department_id → departments.id",
            "employees.manager_id → employees.id",
            "departments.head_id → employees.id",
            "attendance.employee_id → employees.id",
            "projects.department_id → departments.id",
            "project_members.project_id → projects.id",
            "project_members.employee_id → employees.id"
        ]
    },
    "constraints": {
        "soft_delete_rule": None,
        "valid_status_values": ["active", "resigned", "on_leave", "present", "absent", "late", "half_day", "planning", "in_progress", "completed", "on_hold"],
        "mandatory_filters": ["status != 'resigned'"]
    }
}

def get_sample_metadata(db_type: str) -> dict:
    """샘플 메타데이터 반환"""
    if db_type.lower() == "postgresql":
        return SAMPLE_POSTGRES_ECOMMERCE
    elif db_type.lower() == "mysql":
        return SAMPLE_MYSQL_HR
    else:
        return SAMPLE_POSTGRES_ECOMMERCE
