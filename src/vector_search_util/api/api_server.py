from typing import Annotated
from fastapi import FastAPI, APIRouter
from langchain_core.documents import Document
from vector_search_util.core.client import (
    EmbeddingClient, EmbeddingBatchClient, RelationBatchClient, CategoryBatchClient, TagBatchClient
)   
from vector_search_util.model import (
    EmbeddingConfig, ConditionContainer, SourceDocumentData, CategoryData, RelationData, TagData
)

import vector_search_util.core.app as app_module


app = FastAPI()
router = APIRouter()

# vector searchでLangChainのDocumentsを返すAPI
router.add_api_route(
    path="/vector_search_langchain_documents", 
    endpoint=app_module.vector_search_langchain_documents, 
    methods=["GET"])

router.add_api_route(
    path="/get_langchain_documents", 
    endpoint=app_module.get_langchain_documents, 
    methods=["GET"])


router.add_api_route(
    path="/metadata_search",
    endpoint=app_module.metadata_search,
    methods=["GET"])


router.add_api_route(
    path="/vector_search",
    endpoint=app_module.vector_search,
    methods=["GET"])

# get documents
router.add_api_route(
    path="/get_documents",
    endpoint=app_module.get_documents,
    methods=["GET"])

# upsert documents
router.add_api_route(
    path="/upsert_documents",
    endpoint=app_module.upsert_documents,
    methods=["POST"])

# delete documents
router.add_api_route(
    path="/delete_documents",
    endpoint=app_module.delete_documents,
    methods=["DELETE"])

# get categories
router.add_api_route(
    path="/get_categories",
    endpoint=app_module.get_categories,
    methods=["GET"])

# upsert categories
router.add_api_route(
    path="/upsert_categories",
    endpoint=app_module.upsert_categories,
    methods=["POST"])

# delete category
router.add_api_route(
    path="/delete_categories",
    endpoint=app_module.delete_categories,
    methods=["DELETE"])

# get relations
router.add_api_route(
    path="/get_relations",
    endpoint=app_module.get_relations,
    methods=["GET"])

# upsert relations
router.add_api_route(
    path="/upsert_relations",
    endpoint=app_module.upsert_relations,
    methods=["POST"])

# delete relations
router.add_api_route(
    path="/delete_relations",
    endpoint=app_module.delete_relations,
    methods=["DELETE"])

# get tags
router.add_api_route(
    path="/get_tags",
    endpoint=app_module.get_tags,
    methods=["GET"])

# upsert tags
router.add_api_route(
    path="/upsert_tags",
    endpoint=app_module.upsert_tags,
    methods=["POST"])

# delete tags
router.add_api_route(
    path="/delete_tags",
    endpoint=app_module.delete_tags,
    methods=["DELETE"])

router.add_api_route(
    path="/load_documents_from_excel",
    endpoint=app_module.load_documents_from_excel,
    methods=["POST"])

router.add_api_route(
    path="/unload_documents_to_excel",
    endpoint=app_module.unload_documents_to_excel,
    methods=["GET"])

router.add_api_route(
    path="/delete_documents_from_excel",
    endpoint=app_module.delete_documents_from_excel,
    methods=["DELETE"])

router.add_api_route(
    path="/load_categories_from_excel",
    endpoint=app_module.load_categories_from_excel,
    methods=["POST"])

router.add_api_route(
    path="/unload_categories_to_excel",
    endpoint=app_module.unload_categories_to_excel,
    methods=["GET"])

router.add_api_route(
    path="/delete_category_data_from_excel",
    endpoint=app_module.delete_category_data_from_excel,
    methods=["DELETE"])

router.add_api_route(
    path="/load_relations_from_excel",
    endpoint=app_module.load_relations_from_excel,
    methods=["POST"])

router.add_api_route(
    path="/unload_relations_to_excel",
    endpoint=app_module.unload_relations_to_excel,
    methods=["GET"])

router.add_api_route(
    path="/delete_relations_from_excel",
    endpoint=app_module.delete_relations_from_excel,
    methods=["DELETE"])

router.add_api_route(
    path="/load_tags_from_excel",
    endpoint=app_module.load_tags_from_excel,
    methods=["POST"])

router.add_api_route(
    path="/unload_tags_to_excel",
    endpoint=app_module.unload_tags_to_excel,
    methods=["GET"])


router.add_api_route(
    path="/delete_tags_from_excel",
    endpoint=app_module.delete_tags_from_excel,
    methods=["DELETE"])

router.add_api_route(
    path="/get_conditions",
    endpoint=app_module.get_conditions,
    methods=["GET"])

router.add_api_route(
    path="/upsert_conditions",
    endpoint=app_module.upsert_conditions,
    methods=["POST"])

router.add_api_route(
    path="/delete_conditions",
    endpoint=app_module.delete_conditions,
    methods=["DELETE"])

app.include_router(router, prefix="/api/vector_search_util")

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8000)
