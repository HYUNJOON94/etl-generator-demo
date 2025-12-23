"""
ETL LLM-based SQL Generator
FastAPI 기반 메인 애플리케이션
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from sql_generator import sql_generator
from sample_metadata import SAMPLE_POSTGRES_ECOMMERCE, SAMPLE_MYSQL_HR, get_sample_metadata
from db_connector import db_connector

app = FastAPI(
    title="ETL SQL Generator",
    description="LLM 기반 자연어 → SQL 변환 서비스",
    version="1.0.0"
)

# 정적 파일 서빙
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ===== Request/Response Models =====

class SQLGenerateRequest(BaseModel):
    """SQL 생성 요청 모델"""
    request: str  # 자연어 요청
    database_info: Optional[dict] = None  # DB 메타데이터
    db_type: Optional[str] = "PostgreSQL"  # 샘플 메타데이터 사용 시
    include_etl: bool = False  # ETL 파이프라인 포함 여부
    provider: Optional[str] = "google" # google or openai
    model_name: Optional[str] = "gemini-1.5-flash" # gpt-5.2-2025-12-11, gpt-5-mini-2025-08-07, gpt-5-nano-2025-08-07


class SQLGenerateResponse(BaseModel):
    """SQL 생성 응답 모델"""
    intent_summary: str
    sql: Optional[str]
    assumptions: list
    safety_notes: list
    tables_used: list
    is_blocked: bool
    block_reason: Optional[str]
    etl_pipeline: Optional[dict] = None


class DBConnectionRequest(BaseModel):
    """데이터베이스 연결 요청"""
    db_type: str  # postgresql, mysql
    host: str
    port: int
    database: str
    user: str
    password: str


class QueryExecuteRequest(BaseModel):
    """쿼리 실행 요청"""
    sql: str
    limit: int = 10


# ===== Page Routes =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>ETL SQL Generator</h1><p>templates/index.html not found</p>")


# ===== SQL Generation API =====

@app.post("/api/generate-sql", response_model=SQLGenerateResponse)
async def generate_sql(request: SQLGenerateRequest):
    """자연어 요청을 SQL로 변환"""
    
    if not request.request.strip():
        raise HTTPException(status_code=400, detail="요청 내용을 입력해주세요.")
    
    # 메타데이터 결정
    db_info = None

    # 1. 요청에 포함된 메타데이터 우선 사용
    if request.database_info:
        db_info = request.database_info
    
    # 2. 연결된 Live DB가 있다면 메타데이터 추출하여 사용
    if not db_info and db_connector.engine:
        print("Using Live DB Metadata...")
        meta_result = db_connector.extract_metadata()
        if meta_result.get("success"):
            db_info = meta_result.get("metadata")
            
    # 3. 없으면 샘플 메타데이터 사용
    if not db_info:
        print("Using Sample Metadata...")
        db_info = get_sample_metadata(request.db_type or "PostgreSQL")
    
    # SQL 생성
    result = sql_generator.generate_sql(
        user_request=request.request,
        database_info=db_info,
        include_etl=request.include_etl,
        provider=request.provider,
        model_name=request.model_name
    )
    
    return SQLGenerateResponse(**result)


@app.get("/api/sample-metadata/{db_type}")
async def get_sample_metadata_api(db_type: str):
    """샘플 메타데이터 조회"""
    if db_type.lower() == "postgresql":
        return SAMPLE_POSTGRES_ECOMMERCE
    elif db_type.lower() == "mysql":
        return SAMPLE_MYSQL_HR
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 DB 타입입니다. (postgresql, mysql)")


# ===== Database Connection API =====

@app.post("/api/db/connect")
async def connect_database(request: DBConnectionRequest):
    """데이터베이스 연결"""
    result = db_connector.connect(
        db_type=request.db_type,
        host=request.host,
        port=request.port,
        database=request.database,
        user=request.user,
        password=request.password
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "연결 실패"))
    
    return result


@app.post("/api/db/disconnect")
async def disconnect_database():
    """데이터베이스 연결 해제"""
    db_connector.disconnect()
    return {"success": True, "message": "연결이 해제되었습니다."}


@app.get("/api/db/status")
async def get_db_status():
    """현재 데이터베이스 연결 상태"""
    if db_connector.engine and db_connector.connection_info:
        return {
            "connected": True,
            "connection_info": {
                "db_type": db_connector.connection_info.get("db_type"),
                "host": db_connector.connection_info.get("host"),
                "database": db_connector.connection_info.get("database"),
                "user": db_connector.connection_info.get("user")
            }
        }
    return {"connected": False}


@app.get("/api/db/metadata")
async def extract_metadata():
    """연결된 데이터베이스의 메타데이터 추출"""
    result = db_connector.extract_metadata()
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "메타데이터 추출 실패"))
    
    return result


@app.post("/api/generate-samples")
async def generate_samples(request: dict = None):
    """메타데이터 기반 샘플 쿼리 생성"""
    
    provider = request.get("provider", "google") if request else "google"
    model_name = request.get("model_name", "gemini-1.5-flash") if request else "gemini-1.5-flash"

    # 1. 연결된 DB가 있으면 Live Metadata 사용
    if db_connector.engine:
        meta_result = db_connector.extract_metadata()
        if meta_result.get("success"):
            metadata = meta_result.get("metadata")
            samples = sql_generator.generate_sample_queries(metadata, provider=provider, model_name=model_name)
            return {"samples": samples}
    
    # 2. 없으면 요청으로 들어온 메타데이터 사용
    if request and request.get("metadata"):
        samples = sql_generator.generate_sample_queries(request.get("metadata"), provider=provider, model_name=model_name)
        return {"samples": samples}
        
    raise HTTPException(status_code=400, detail="데이터베이스 연결이 필요합니다.")


@app.post("/api/db/execute")
async def execute_query(request: QueryExecuteRequest):
    """쿼리 실행 (SELECT만 허용)"""
    result = db_connector.test_query(request.sql, request.limit)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "쿼리 실행 실패"))
    
    return result


# ===== Health Check =====

@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "service": "ETL SQL Generator"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

