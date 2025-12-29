from __future__ import annotations

import os, json
from dotenv import load_dotenv
from datetime import datetime
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from typing import Optional, ClassVar, Any, Callable, Sequence, Union, Literal, Annotated, TypeAlias
from datetime import datetime, timezone
from langchain_core.documents import Document

import vector_search_util._internal.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)
from typing import Optional

class EmbeddingConfig:

    def __init__(self):
        load_dotenv()

        # metadata用のキー設定
        self.source_id_key: str = os.getenv("SOURCE_ID_KEY","source_id")
        self.source_content_key: str = os.getenv("SOURCE_CONTENT_KEY","source_content")
        self.category_key: str = os.getenv("CATEGORY_KEY","category")
        self.updated_at_key: str = os.getenv("UPDATED_AT_KEY","updated_at")
        self.first_document_key: str = os.getenv("FIRST_DOCUMENT_KEY","first_document")

        # ベクトル化する際にSOURCE_CONTENTを分割する。その際のチャンクサイズ
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE","4000"))

        # 並列度の設定
        self.concurrency: int = int(os.getenv("EMBEDDING_CONCURRENCY","16"))
        
        self.app_data_path: str = os.getenv("APP_DATA_PATH","work/app_data")

        
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


# category_data
class CategoryData(BaseModel):
    name: str
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)

# relation_data
class RelationData(BaseModel):
    # Relationの各フィールド。空文字は禁止
    from_node: str
    to_node: str
    edge_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_valid(self) -> bool:
        # すべてのフィールドが非空文字列であることを確認
        return all([self.from_node, self.to_node, self.edge_type])

# tag_data
class TagData(BaseModel):
    name: str
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceDocumentData(BaseModel):

    embedding_config: ClassVar[EmbeddingConfig | None]  = None

    source_id: str
    source_content: str
    category: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata : dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def _get_embedding_config_(cls) -> EmbeddingConfig:
        if cls.embedding_config is None:
            cls.embedding_config = EmbeddingConfig()
        return cls.embedding_config

    @classmethod
    def to_langchain_documents(cls, data_list: list["SourceDocumentData"], append_vectors: bool = False) -> list[Document]:
        """Convert to Langchain Document."""
        documents: list[Document] = []
        for data in data_list:
            docs = cls.__to_langchain_documents_from_single__(data, append_vectors)
            documents.extend(docs)
        return documents

    @classmethod
    def __to_langchain_documents_from_single__(cls, data: "SourceDocumentData", append_vectors: bool = False) -> list[Document]:
        """Convert to Langchain Document."""
        embedding_config = cls._get_embedding_config_()
        documents: list[Document] = []

        # chunkingに基づいて、source_contentを分割する
        chunk_size = embedding_config.chunk_size
        updated_at_str = data.updated_at.isoformat()

        page_countents = [data.source_content[i:i+chunk_size] for i in range(0, len(data.source_content), chunk_size)]

        for i in range(len(page_countents)):
            page_content = page_countents[i]
            metadata={
                    embedding_config.source_id_key: data.source_id,
                    embedding_config.category_key: data.category,
                    embedding_config.updated_at_key: updated_at_str,
                    **data.metadata
                }
            # metadataにfirst_document_flagを追加
            if i == 0 and not append_vectors:
                metadata[embedding_config.first_document_key] = True
            doc = Document(
                page_content=page_content,
                metadata=metadata
            )
            documents.append(doc)
        return documents

    @classmethod
    def from_langchain_documents(cls, documents: list[Document], get_source_content_function: Callable) -> list["SourceDocumentData"]:
        embedding_config = cls._get_embedding_config_()

        first_documents = [doc for doc in documents if doc.metadata.get(embedding_config.first_document_key, False) == True]
        data_dict: dict[str, SourceDocumentData] = {}
        for doc in first_documents:
            source_id = doc.metadata.get(embedding_config.source_id_key, "")
            if source_id not in data_dict:
                data = SourceDocumentData.__from_langchain_document__(doc, get_source_content_function)
                data_dict[source_id] = data
        return list(data_dict.values())
    
    @classmethod
    def __from_langchain_document__(cls, document: Document, get_source_content_function: Callable[[str], str]) -> "SourceDocumentData":
        """Convert from Langchain Document."""
        embedding_config = cls._get_embedding_config_()
        source_id = document.metadata.get(embedding_config.source_id_key, "")
        category = document.metadata.get(embedding_config.category_key, "")

        updated_at_str = document.metadata.get(embedding_config.updated_at_key, None)
        if updated_at_str:
            updated_at = datetime.fromisoformat(updated_at_str)
        else:
            updated_at = datetime.now(timezone.utc)


        # documentのmetadataをコピーして、source_id, category, updated_at, first_document_keyを削除する
        metadata_copy = {
            k: v for k, v in document.metadata.copy().items() if k not in [
                embedding_config.source_id_key, 
                embedding_config.category_key, 
                embedding_config.updated_at_key, 
                embedding_config.first_document_key
                ]
            }

        data = SourceDocumentData(
            source_id=source_id,
            source_content=get_source_content_function(source_id),
            category=category,
            updated_at=updated_at,
            metadata=metadata_copy
        )
        return data


class Condition(ABC, BaseModel):
    """Base class for all conditions."""
    @abstractmethod
    def build(self):
        raise NotImplementedError


# Discriminated union for OpenAPI (oneOf + discriminator)
ConditionSpec: TypeAlias = Annotated[
    Union[
        "EqCondition",
        "InCondition",
        "ContainsCondition",
        "CompareCondition",
        "AndCondition",
        "OrCondition",
        "NotCondition",
    ],
    Field(discriminator="type"),
]

class EqCondition(Condition):
    type: Literal["eq"] = "eq"
    field: str = Field(..., description="The field to compare.")
    value: Any = Field(..., description="The value to compare against.")

    def build(self):
        return {self.field: self.value}


class InCondition(Condition):
    type: Literal["in"] = "in"
    field: str = Field(..., description="The field to compare.")
    values: list[Any] = Field(..., description="The list of values to compare against.")

    def build(self):
        return {self.field: {"$in": self.values}}


class ContainsCondition(Condition):
    """MongoDB の部分一致（正規表現）"""
    type: Literal["contains"] = "contains"
    field: str = Field(..., description="The field to compare.")
    substring: str = Field(..., description="The substring to search for.")

    def build(self):
        return {self.field: {"$regex": self.substring}}


# -------------------------
# 比較条件 ($gte, $lte, $gt, $lt)
# -------------------------

class CompareCondition(Condition):
    type: Literal["compare"] = "compare"
    field: str = Field(..., description="The field to compare.")
    operator: str = Field(..., description="The comparison operator.")
    value: Any = Field(..., description="The value to compare against.")
    def build(self):
        return {self.field: {self.operator: self.value}}


# -------------------------
# 論理条件 ($and, $or, $not)
# -------------------------

class AndCondition(Condition):
    type: Literal["and"] = "and"
    conditions: list[ConditionSpec] = Field(..., description="List of conditions")

    def build(self):
        return {"$and": [c.build() for c in self.conditions]}


class OrCondition(Condition):
    type: Literal["or"] = "or"
    conditions: list[ConditionSpec] = Field(..., description="List of conditions")

    def build(self):
        return {"$or": [c.build() for c in self.conditions]}


class NotCondition(Condition):
    type: Literal["not"] = "not"
    condition: ConditionSpec = Field(..., description="The condition to negate")

    def build(self):
        # NOT は {field: {"$not": {...}}} の形にする必要がある
        built = self.condition.build()
        field, expr = list(built.items())[0]
        return {field: {"$not": expr}}

# -------------------------
# Query Builder
# -------------------------
import uuid
class ConditionContainer(BaseModel):
    name: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Name of the condition container")
    conditions: list[ConditionSpec] = Field(default_factory=list, description="List of conditions")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the condition container")

    
    # 各種条件オブジェクトを生成するメソッド
    @classmethod
    def create_eq_condition(cls, field: str, value: Any) -> EqCondition:
        return EqCondition(field=field, value=value)
    @classmethod
    def create_in_condition(cls, field: str, values: list[Any]) -> InCondition:
        return InCondition(field=field, values=values)
    @classmethod
    def create_contains_condition(cls, field: str, substring: str) -> ContainsCondition:
        return ContainsCondition(field=field, substring=substring)

    @classmethod
    def create_compare_condition(cls, field: str, operator: str, value: Any) -> CompareCondition:
        return CompareCondition(field=field, operator=operator, value=value)
    
    @classmethod
    def create_gte_condition(cls, field: str, value: Any) -> CompareCondition:
        return CompareCondition(field=field, operator="$gte", value=value)
    @classmethod
    def create_lte_condition(cls, field: str, value: Any) -> CompareCondition:
        return CompareCondition(field=field, operator="$lte", value=value)
    @classmethod
    def create_gt_condition(cls, field: str, value: Any) -> CompareCondition:
        return CompareCondition(field=field, operator="$gt", value=value)
    @classmethod
    def create_lt_condition(cls, field: str, value: Any) -> CompareCondition:
        return CompareCondition(field=field, operator="$lt", value=value)
    @classmethod
    def create_and_condition(cls, conditions: Sequence[ConditionSpec]) -> AndCondition:
        return AndCondition(conditions=list(conditions))
    @classmethod
    def create_or_condition(cls, conditions: Sequence[ConditionSpec]) -> OrCondition:
        return OrCondition(conditions=list(conditions))
    @classmethod
    def create_not_condition(cls, condition: ConditionSpec) -> NotCondition:
        return NotCondition(condition=condition)
    # --- dictからConditionContainer生成 ---
    ## { key: value, key2: { $gte: value2 }, $and: [ ... ] } のようなMongoDB風のdictからConditionContainerを生成する
    @classmethod
    def from_dict(cls, condition_dict: dict) -> "ConditionContainer":
        container = ConditionContainer()
        if not condition_dict:
            return container

        def parse_condition(d: dict) -> ConditionSpec:
            if "$and" in d:
                sub_conditions: list[ConditionSpec] = [parse_condition(c) for c in d["$and"]]
                return cls.create_and_condition(conditions=sub_conditions)
            elif "$or" in d:
                sub_conditions: list[ConditionSpec] = [parse_condition(c) for c in d["$or"]]
                return cls.create_or_condition(conditions=sub_conditions)
            elif "$not" in d:
                sub_condition: ConditionSpec = parse_condition(d["$not"])
                return cls.create_not_condition(condition=sub_condition)
            else:
                # フィールドごとの条件解析
                field, expr = list(d.items())[0]
                if isinstance(expr, dict):
                    if "$in" in expr:
                        return cls.create_in_condition(field=field, values=expr["$in"])
                    if "$regex" in expr:
                        return cls.create_contains_condition(field=field, substring=expr["$regex"])
                    for op in ["$gte", "$lte", "$gt", "$lt"]:
                        if op in expr:
                            return cls.create_compare_condition(field=field, operator=op, value=expr[op])
                # eq
                return cls.create_eq_condition(field=field, value=expr)

        condition = parse_condition(condition_dict)
        container.conditions.append(condition)
        return container

    # --- 基本条件 ---
    def add_eq_condition(self, field, value):
        self.conditions.append(EqCondition(field=field, value=value))
        return self

    def add_in_condition(self, field, values):
        self.conditions.append(InCondition(field=field, values=values))
        return self

    def add_contains_condition(self, field, substring):
        self.conditions.append(ContainsCondition(field=field, substring=substring))
        return self

    # --- 比較条件 ---
    def add_gte_condition(self, field, value):
        self.conditions.append(CompareCondition(field=field, operator="$gte", value=value))
        return self

    def add_lte_condition(self, field, value):
        self.conditions.append(CompareCondition(field=field, operator="$lte", value=value))
        return self

    def add_gt_condition(self, field, value):
        self.conditions.append(CompareCondition(field=field, operator="$gt", value=value))
        return self

    def add_lt_condition(self, field, value):
        self.conditions.append(CompareCondition(field=field, operator="$lt", value=value))
        return self

    # --- 論理条件 ---
    def add_and_condition(self, conditions: Sequence[ConditionSpec]):
        self.conditions.append(AndCondition(conditions=list(conditions)))
        return self

    def add_or_condition(self, conditions: Sequence[ConditionSpec]):
        self.conditions.append(OrCondition(conditions=list(conditions)))
        return self

    def add_not_condition(self, condition: ConditionSpec):
        self.conditions.append(NotCondition(condition=condition))
        return self

    # --- MongoDB風 dict 生成 ---
    def build(self):
        if len(self.conditions) == 0:
            return {}
        if len(self.conditions) == 1:
            return self.conditions[0].build()
        return {"$and": [c.build() for c in self.conditions]}

    # --- PostgreSQL JSONB SQL 生成 ---
    def to_postgres_sql(self):
        if len(self.conditions) == 0:
            return ""

        translator = PostgresJsonbTranslator()
        return translator.translate(self.build())

    # --- SQLite3 JSON SQL 生成 ---
    def to_sqlite_sql(self):
        if len(self.conditions) == 0:
            return ""

        translator = SqliteJsonTranslator()
        return translator.translate(self.build())


# Resolve forward refs for discriminated union / recursive models (Pydantic v1/v2)
def _rebuild_condition_models() -> None:
    models = [
        EqCondition,
        InCondition,
        ContainsCondition,
        CompareCondition,
        AndCondition,
        OrCondition,
        NotCondition,
        ConditionContainer,
    ]
    for m in models:
        if hasattr(m, "model_rebuild"):
            m.model_rebuild()
        elif hasattr(m, "update_forward_refs"):
            m.update_forward_refs()


_rebuild_condition_models()

class ConditionTranslator(ABC):

    @abstractmethod
    def _translate_dict(self, d: dict) -> str:
        raise NotImplementedError
    
    def _translate_field(self, field: str, expr: Any) -> str:
        raise NotImplementedError
    

class PostgresJsonbTranslator(ConditionTranslator):
    def __init__(self, json_field: str = "cmetadata"):
        self.json_field = json_field

    def translate(self, condition_dict, json_field: str | None = None):
        if json_field is not None:
            self.json_field = json_field
        return self._translate_dict(condition_dict)

    def _translate_dict(self, d) -> str:
        clauses: list[str] = []
        for key, value in d.items():
            if key == "$and":
                sub = [self._translate_dict(v) for v in value]
                clauses.append("(" + " AND ".join(sub) + ")")
            elif key == "$or":
                sub = [self._translate_dict(v) for v in value]
                clauses.append("(" + " OR ".join(sub) + ")")
            else:
                clauses.append(self._translate_field(key, value))
        return " AND ".join(clauses)

    def _translate_field(self, field: str, expr: Any) -> str:
        json_field = self.json_field

        if isinstance(expr, dict):
            if "$in" in expr:
                vals = ",".join([f"'{v}'" for v in expr["$in"]])
                return f"({json_field}->>'{field}') IN ({vals})"

            if "$regex" in expr:
                return f"({json_field}->>'{field}') LIKE '%{expr['$regex']}%'"

            if "$gte" in expr:
                return f"({json_field}->>'{field}')::numeric >= {expr['$gte']}"

            if "$lte" in expr:
                return f"({json_field}->>'{field}')::numeric <= {expr['$lte']}"

            if "$gt" in expr:
                return f"({json_field}->>'{field}')::numeric > {expr['$gt']}"

            if "$lt" in expr:
                return f"({json_field}->>'{field}')::numeric < {expr['$lt']}"

            if "$not" in expr:
                inner = self._translate_field(field, expr["$not"])
                return f"NOT ({inner})"

        # eq
        return f"({json_field}->>'{field}') = '{expr}'"


class SqliteJsonTranslator(ConditionTranslator):
    """SQLite3向け（JSON1拡張）WHERE句生成。

    - json_extract(json_field, '$.key') を使ってJSONから値を取り出す
    - SQLite標準では正規表現が無い前提で $regex は LIKE にマップ

    NOTE: 既存のPostgresJsonbTranslatorと同様、現状はSQL文字列を直接生成します。
    """
    def __init__(self):
        self.json_field = "cmetadata"

    def translate(self, condition_dict) -> str:
        return self._translate_dict(condition_dict)

    def _translate_dict(self, d) -> str:
        clauses: list[str] = []
        for key, value in d.items():
            if key == "$and":
                sub = [self._translate_dict(v) for v in value]
                clauses.append("(" + " AND ".join(sub) + ")")
            elif key == "$or":
                sub = [self._translate_dict(v) for v in value]
                clauses.append("(" + " OR ".join(sub) + ")")
            else:
                clauses.append(self._translate_field(key, value))
        return " AND ".join(clauses)

    def _translate_field(self, field: str, expr: Any) -> str:
        extracted = self._json_extract(field)

        if isinstance(expr, dict):
            if "$in" in expr:
                vals = ",".join([self._sql_literal(v) for v in expr["$in"]])
                return f"{extracted} IN ({vals})"

            if "$regex" in expr:
                # 部分一致（LIKE）
                like = str(expr["$regex"]).replace("%", "\\%")
                like = like.replace("_", "\\_")
                like = like.replace("'", "''")
                return f"{extracted} LIKE '%{like}%' ESCAPE '\\'"

            if "$gte" in expr:
                return f"CAST({extracted} AS REAL) >= {self._sql_literal(expr['$gte'])}"

            if "$lte" in expr:
                return f"CAST({extracted} AS REAL) <= {self._sql_literal(expr['$lte'])}"

            if "$gt" in expr:
                return f"CAST({extracted} AS REAL) > {self._sql_literal(expr['$gt'])}"

            if "$lt" in expr:
                return f"CAST({extracted} AS REAL) < {self._sql_literal(expr['$lt'])}"

            if "$not" in expr:
                inner = self._translate_field(field, expr["$not"])
                return f"NOT ({inner})"

        # eq
        if expr is None:
            return f"{extracted} IS NULL"
        return f"{extracted} = {self._sql_literal(expr)}"

    def _json_extract(self, field: str) -> str:
        # fieldにクォートが必要なケース（記号など）がある場合はここを拡張
        return f"json_extract({self.json_field}, '$.{field}')"

    def _sql_literal(self, v: Any) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, (int, float)):
            return str(v)
        # string/その他
        s = str(v).replace("'", "''")
        return f"'{s}'"

