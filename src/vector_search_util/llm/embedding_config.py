from typing import Optional
import os
from dotenv import load_dotenv

class EmbeddingConfig:

    def __init__(self):
        load_dotenv()

        # 並列度の設定
        self.concurrency: int = int(os.getenv("EMBEDDING_CONCURRENCY","16"))
        
        self.app_data_path: str = os.getenv("APP_DATA_PATH","work/app_data")

        self.source_id_key: str = os.getenv("SOURCE_ID_KEY","source_id")
        self.category_key: str = os.getenv("CATEGORY_KEY","category")
        
        self.vector_db_type: str = os.getenv("VECTOR_DB_TYPE","chroma")
        self.vector_db_url: str = os.getenv("VECTOR_DB_URL", "work/chroma_db")
        self.vector_db_collection_name: str = os.getenv("VECTOR_DB_COLLECTION_NAME","")
        self.llm_provider: str = os.getenv("LLM_PROVIDER","openai")
        self.api_key: str = ""
        self.completion_model: str = ""
        self.embedding_model: str = ""
        self.api_version: Optional[str] = None
        self.endpoint: Optional[str] = None

        self.base_url: Optional[str] = None
        if self.llm_provider == "openai" or self.llm_provider == "azure_openai":
            self.api_key = os.getenv("OPENAI_API_KEY","")
            self.base_url = os.getenv("OPENAI_BASE_URL","") or None
            self.completion_model: str = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4o")
            self.embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        if self.llm_provider == "azure_openai":
            self.api_version: Optional[str] = os.getenv("AZURE_OPENAI_API_VERSION","")
            self.endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT","")


