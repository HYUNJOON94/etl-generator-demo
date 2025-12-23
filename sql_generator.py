"""
SQL Generator Service
LLM 기반 자연어 → SQL 변환 서비스
"""

import os
import re
import json
from typing import Optional
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
당신은 SQL 전문가입니다. 제공된 데이터베이스 메타데이터를 사용하여 사용자의 자연어 질문을 최적화된 SQL로 변환하세요.
반드시 아래 JSON 구조를 따라야 하며, 다른 텍스트 없이 JSON만 응답하세요:

{
  "intent_summary": "사용자 요청 요약",
  "sql": "생성된 SQL 쿼리 (SELECT만 허용)",
  "assumptions": ["쿼리 작성 시 가정한 사항들"],
  "safety_notes": ["보안 및 성능 관련 주의사항"],
  "tables_used": ["참조된 테이블 리스트"],
  "is_blocked": false,
  "block_reason": null
}

주의: SELECT 외의 파괴적인 쿼리(INSERT, UPDATE, DELETE, DROP 등)는 절대 생성하지 마세요.
"""

ETL_PROMPT_ADDITION = """
추가로 ETL 파이프라인 정보도 포함하세요. JSON 응답에 "etl_pipeline" 필드를 추가하세요:
{
  "etl_pipeline": {
    "extract": { "source_tables": ["소스_테이블들"], "conditions": "추출_조건" },
    "transform": ["데이터_변환_단계들"],
    "load": { "target_table": "대상_테이블", "write_mode": "append_OR_overwrite" }
  }
}
"""

class SQLGenerator:
    def __init__(self):
        self.gemini_model = None
        self.openai_client = None
        
        if GEMINI_API_KEY:
            self.gemini_model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
            
        if OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    def _validate_sql_safety(self, sql: str) -> tuple[bool, Optional[str]]:
        # ... (Safety check logic remains same) ...
        if not sql:
            return True, None
        
        dangerous_keywords = [
            r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', 
            r'\bDROP\b', r'\bTRUNCATE\b', r'\bALTER\b',
            r'\bCREATE\b', r'\bGRANT\b', r'\bREVOKE\b',
            r'\bEXEC\b', r'\bEXECUTE\b'
        ]
        
        sql_upper = sql.upper()
        for pattern in dangerous_keywords:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                keyword = re.search(pattern, sql_upper, re.IGNORECASE).group()
                return False, f"위험한 SQL 키워드 감지됨: {keyword}"
        
        return True, None
    
    def generate_sql(self, user_request: str, database_info: dict, include_etl: bool = False, provider: str = "google", model_name: str = "gemini-3.0-flash") -> dict:
        """자연어 요청을 SQL로 변환"""
        print(f"--- Calling LLM (SQL) | Provider: {provider} | Model: {model_name} ---")
        
        # Dispatch based on provider
        if provider == "openai":
            if not self.openai_client:
                 return self._generate_demo_response(user_request, database_info, include_etl, "OpenAI API Key provided not found")
            return self._generate_sql_openai(user_request, database_info, include_etl, model_name)
        else:
            # Default to Google
            if not self.gemini_model:
                return self._generate_demo_response(user_request, database_info, include_etl, "Gemini API Key provided not found")
            return self._generate_sql_gemini(user_request, database_info, include_etl, model_name)

    def _generate_sql_gemini(self, user_request: str, database_info: dict, include_etl: bool, model_name: str) -> dict:
        # 프롬프트 구성
        prompt = SYSTEM_PROMPT
        if include_etl:
            prompt += ETL_PROMPT_ADDITION
        
        prompt += f"""

## 입력 데이터

### Database Info:
```json
{json.dumps(database_info, ensure_ascii=False, indent=2)}
```

### 사용자 요청:
{user_request}

위 정보를 바탕으로 SQL을 생성하세요. 반드시 JSON 형식으로만 응답하세요.
"""
        try:
            # Update model name if needed (though we init with a default, user might request specific)
            # For Gemini, we might create a new instance or just use the default. 
            # Given the requirement, we stick to the one we initialized or re-init if really needed.
            # But the user only asked for options.
            
            response = self.gemini_model.generate_content(prompt)
            return self._parse_llm_response(response.text)
            
        except Exception as e:
            return self._error_response(str(e))

    def _generate_sql_openai(self, user_request: str, database_info: dict, include_etl: bool, model_name: str) -> dict:
        system_content = SYSTEM_PROMPT
        if include_etl:
            system_content += ETL_PROMPT_ADDITION

        user_content = f"""
## 입력 데이터

### Database Info:
```json
{json.dumps(database_info, ensure_ascii=False, indent=2)}
```

### 사용자 요청:
{user_request}

위 정보를 바탕으로 SQL을 생성하세요. 반드시 JSON 형식으로만 응답하세요.
"""
        # Map demo model names to real API model names
        real_model = model_name
        # If it's a generic name, map to default nano. Otherwise use as is.
        if model_name in ["openai", "gpt-5"]:
            real_model = "gpt-5-nano-2025-08-07"
        
        try:
            completion = self.openai_client.chat.completions.create(
                model=real_model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            return self._parse_llm_response(response_text)
        except Exception as e:
            return self._error_response(str(e))

    def _parse_llm_response(self, text: str) -> dict:
        try:
            # Clean up potential markdown code blocks if the model wrapped it
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            result = json.loads(text)
            
            # Safety check
            if result.get("sql"):
                is_safe, reason = self._validate_sql_safety(result["sql"])
                if not is_safe:
                    result["sql"] = None
                    result["is_blocked"] = True
                    result["block_reason"] = reason
            return result
        except json.JSONDecodeError:
             return {
                "intent_summary": "응답 파싱 실패",
                "sql": None,
                "assumptions": [],
                "safety_notes": ["LLM 응답이 올바른 JSON 형식이 아닙니다."],
                "tables_used": [],
                "is_blocked": True,
                "block_reason": "응답 형식 오류"
            }

    def _error_response(self, error_msg: str) -> dict:
        return {
            "intent_summary": "오류 발생",
            "sql": None,
            "assumptions": [],
            "safety_notes": [error_msg],
            "tables_used": [],
            "is_blocked": True,
            "block_reason": f"SQL 생성 중 오류: {error_msg}"
        }

    # ... (generate_sample_queries and _generate_demo_response remain similar, logic update needed for provider)
    
    def generate_sample_queries(self, database_info: dict, provider: str = "google", model_name: str = "gemini-1.5-flash") -> list[str]:
        """메타데이터 기반 샘플 쿼리 10개 생성"""
        print(f"--- Calling LLM (Samples) | Provider: {provider} | Model: {model_name} ---")
        
        prompt = f"""
당신은 SQL 전문가입니다. 아래 제공된 데이터베이스 메타데이터를 분석하여, 사용자가 물어볼 법한 **유용한 자연어 질문(쿼리 요청) 10개**를 생성해주세요.

## Database Info:
```json
{json.dumps(database_info, ensure_ascii=False, indent=2)}
```

## 규칙
1. 이 데이터베이스의 테이블과 컬럼 구조를 최대한 활용하는 다양하고 실용적인 질문이어야 합니다.
2. 단순 조회부터 집계, 그룹화, 조인 등이 포함된 질문을 다양하게 섞어주세요.
3. 출력은 오직 **자연어 질문 리스트만** JSON 배열 형식으로 주세요.
4. 예시: ["가장 최근 주문 5개 보여줘", "카테고리별 상품 개수는?"]
5. 번호 매기지 말고 순수 텍스트 배열로만 주세요.
"""
        try:
            if provider == "openai" and self.openai_client:
                # Map model name
                real_model = model_name
                if model_name in ["openai", "gpt-5"]:
                    real_model = "gpt-5-nano-2025-08-07"
                
                completion = self.openai_client.chat.completions.create(
                    model=real_model,
                    messages=[
                        {"role": "system", "content": "You are a SQL expert helper."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"} if "JSON" in prompt.upper() else None
                )
                text = completion.choices[0].message.content
            elif self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                text = response.text
            else:
                return ["API 키가 설정되지 않았습니다."]
            
            # JSON 배열 추출
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 파싱 실패 시 텍스트 라인별로 시도
                lines = [line.strip().lstrip('- ').strip() for line in text.split('\n') if line.strip()]
                return lines[:10]
                
        except Exception as e:
            print(f"Error generating samples: {e}")
            return ["샘플 쿼리 생성 실패"]

    def _generate_demo_response(self, user_request: str, database_info: dict, include_etl: bool, error_msg: Optional[str] = None) -> dict:
        """API 키가 없을 때 데모 응답 생성"""
        
        # 위험한 요청 감지
        dangerous_words = ['삭제', 'delete', 'drop', '제거', 'truncate', '수정', 'update', 'insert', '추가', '변경']
        request_lower = user_request.lower()
        
        for word in dangerous_words:
            if word in request_lower:
                return {
                    "intent_summary": user_request,
                    "sql": None,
                    "assumptions": [],
                    "safety_notes": [],
                    "tables_used": [],
                    "is_blocked": True,
                    "block_reason": f"파괴적인 작업 요청이 감지되었습니다. SELECT 쿼리만 허용됩니다."
                }
        
        db_type = database_info.get("db_type", "PostgreSQL")
        tables = database_info.get("schema_summary", {}).get("tables", [])
        
        # 간단한 데모 SQL 생성
        if tables:
            main_table = tables[0]["table_name"]
            columns = [col["column_name"] for col in tables[0].get("columns", [])[:5]]
            
            if db_type == "MySQL":
                sql = f"SELECT {', '.join(columns)}\nFROM {main_table}\nWHERE status = 'active'\nLIMIT 10;"
            else:
                sql = f"SELECT {', '.join(columns)}\nFROM {main_table}\nWHERE is_deleted = false\nLIMIT 10;"
        else:
            sql = "SELECT * FROM sample_table LIMIT 10;"
        
        result = {
            "intent_summary": f"'{user_request}'에 대한 데모 SQL 생성",
            "sql": sql,
            "assumptions": [
                "GEMINI_API_KEY가 설정되지 않아 데모 모드로 동작합니다.",
                "실제 API 키를 설정하면 정확한 SQL이 생성됩니다."
            ],
            "safety_notes": ["LIMIT 10을 자동으로 추가하여 결과를 제한했습니다."],
            "tables_used": [tables[0]["table_name"]] if tables else ["sample_table"],
            "is_blocked": False,
            "block_reason": None
        }
        
        if include_etl:
            result["etl_pipeline"] = {
                "extract": {
                    "source_tables": result["tables_used"],
                    "conditions": "is_deleted = false" if db_type == "PostgreSQL" else "status = 'active'"
                },
                "transform": [
                    "NULL 값 기본값 처리",
                    "날짜 형식 표준화",
                    "데이터 타입 검증"
                ],
                "load": {
                    "target_table": f"processed_{result['tables_used'][0]}" if result["tables_used"] else "processed_data",
                    "write_mode": "append"
                }
            }
        
        return result


# 싱글톤 인스턴스
sql_generator = SQLGenerator()
