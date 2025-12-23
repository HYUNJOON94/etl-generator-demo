"""
Database Connection Service
실제 데이터베이스 연결 및 메타데이터 추출
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import json


class DatabaseConnector:
    """데이터베이스 연결 및 메타데이터 추출 클래스"""
    
    SUPPORTED_DB_TYPES = {
        "postgresql": "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
        "mysql": "mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    }
    
    def __init__(self):
        self.engine = None
        self.connection_info = None
        self.metadata_cache = None
    
    def connect(self, db_type: str, host: str, port: int, database: str, 
                user: str, password: str) -> Dict[str, Any]:
        """데이터베이스 연결"""
        try:
            db_type_lower = db_type.lower()
            if db_type_lower not in self.SUPPORTED_DB_TYPES:
                return {
                    "success": False,
                    "error": f"지원하지 않는 DB 타입: {db_type}. 지원: {list(self.SUPPORTED_DB_TYPES.keys())}"
                }
            
            url_template = self.SUPPORTED_DB_TYPES[db_type_lower]
            connection_url = url_template.format(
                user=user,
                password=password,
                host=host,
                port=port,
                database=database
            )
            
            self.engine = create_engine(connection_url, echo=False)
            
            # 연결 테스트
            with self.engine.connect() as conn:
                if db_type_lower == "postgresql":
                    result = conn.execute(text("SELECT version()"))
                else:
                    result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
            
            self.metadata_cache = None  # 연결 시 캐시 초기화
            
            self.connection_info = {
                "db_type": db_type,
                "host": host,
                "port": port,
                "database": database,
                "user": user
            }
            
            return {
                "success": True,
                "message": f"{db_type} 데이터베이스에 연결되었습니다.",
                "version": version
            }
            
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"데이터베이스 연결 실패: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"연결 오류: {str(e)}"
            }
    
    def disconnect(self):
        """연결 해제"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.connection_info = None
            self.metadata_cache = None
    
    def extract_metadata(self) -> Dict[str, Any]:
        """데이터베이스 메타데이터 추출"""
        if not self.engine:
            return {"error": "데이터베이스에 연결되어 있지 않습니다."}
        
        # 캐시된 메타데이터가 있으면 반환
        if self.metadata_cache:
            return self.metadata_cache

        try:
            inspector = inspect(self.engine)
            tables_info = []
            relationships = []
            
            # 모든 테이블 정보 추출
            for table_name in inspector.get_table_names():
                columns = []
                pk_columns = set()
                
                # Primary Key 정보
                pk_info = inspector.get_pk_constraint(table_name)
                if pk_info:
                    pk_columns = set(pk_info.get('constrained_columns', []))
                
                # Foreign Key 정보
                fk_info = inspector.get_foreign_keys(table_name)
                fk_map = {}
                for fk in fk_info:
                    for i, col in enumerate(fk.get('constrained_columns', [])):
                        ref_cols = fk.get('referred_columns', [])
                        fk_map[col] = {
                            "ref_table": fk.get('referred_table'),
                            "ref_column": ref_cols[i] if i < len(ref_cols) else None
                        }
                        relationships.append(
                            f"{table_name}.{col} → {fk.get('referred_table')}.{ref_cols[i] if i < len(ref_cols) else '?'}"
                        )
                
                # 컬럼 정보
                for col in inspector.get_columns(table_name):
                    col_info = {
                        "column_name": col['name'],
                        "data_type": str(col['type']),
                        "nullable": col.get('nullable', True),
                        "description": col.get('comment', ''),
                        "primary_key": col['name'] in pk_columns
                    }
                    
                    if col['name'] in fk_map:
                        col_info["foreign_key"] = fk_map[col['name']]
                    
                    columns.append(col_info)
                
                # 테이블 코멘트
                table_comment = inspector.get_table_comment(table_name)
                
                tables_info.append({
                    "table_name": table_name,
                    "description": table_comment.get('text', '') if table_comment else '',
                    "columns": columns
                })
            
            # 메타데이터 구성
            db_type = self.connection_info.get('db_type', 'Unknown') if self.connection_info else 'Unknown'
            
            metadata = {
                "db_type": db_type,
                "db_version": self._get_db_version(),
                "schema_summary": {
                    "tables": tables_info,
                    "relationships": relationships
                },
                "constraints": {
                    "soft_delete_rule": None,
                    "valid_status_values": [],
                    "mandatory_filters": []
                }
            }
            
            result = {
                "success": True,
                "metadata": metadata,
                "table_count": len(tables_info)
            }
            
            self.metadata_cache = result  # 결과 캐싱
            return result
            
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"메타데이터 추출 실패: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"오류 발생: {str(e)}"
            }
    
    def _get_db_version(self) -> str:
        """DB 버전 조회"""
        if not self.engine:
            return "Unknown"
        
        try:
            with self.engine.connect() as conn:
                db_type = self.connection_info.get('db_type', '').lower() if self.connection_info else ''
                if db_type == "postgresql":
                    result = conn.execute(text("SHOW server_version"))
                elif db_type == "mysql":
                    result = conn.execute(text("SELECT VERSION()"))
                else:
                    return "Unknown"
                return result.scalar() or "Unknown"
        except:
            return "Unknown"
    
    def test_query(self, sql: str, limit: int = 10) -> Dict[str, Any]:
        """쿼리 테스트 실행 (SELECT만 허용)"""
        if not self.engine:
            return {"success": False, "error": "데이터베이스에 연결되어 있지 않습니다."}
        
        # SELECT만 허용
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {
                "success": False,
                "error": "SELECT 쿼리만 실행할 수 있습니다."
            }
        
        # LIMIT 추가 (안전을 위해)
        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                columns = list(result.keys())
                
                # 결과를 JSON 직렬화 가능한 형태로 변환
                data = []
                for row in rows:
                    data.append({col: self._serialize_value(val) for col, val in zip(columns, row)})
                
                return {
                    "success": True,
                    "columns": columns,
                    "data": data,
                    "row_count": len(data)
                }
                
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"쿼리 실행 실패: {str(e)}"
            }
    
    def _serialize_value(self, value) -> Any:
        """값을 JSON 직렬화 가능한 형태로 변환"""
        if value is None:
            return None
        if isinstance(value, (int, float, str, bool)):
            return value
        return str(value)


# 싱글톤 인스턴스
db_connector = DatabaseConnector()
