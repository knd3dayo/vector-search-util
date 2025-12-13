import asyncio
from typing import Annotated, Any
from dotenv import load_dotenv
import argparse
from fastmcp import FastMCP
from pydantic import Field
from langchain_core.documents import Document
from vector_search_util.util.search import vector_search as vector_search_tool
from vector_search_util.util.client import EmbeddingClient, EmbeddingData, CategoryData
from vector_search_util.llm.embedding_config import EmbeddingConfig

    
mcp = FastMCP("vector_search_util") #type :ignore

async def vector_search(
    query: Annotated[str, Field(description="The query string to search for in the vector database.")],
    category: Annotated[str, Field(default="", description="The category to filter the search results.")]= "",
    filter: Annotated[dict[str, list[str]], Field(default={}, description="Optional filter to apply to the search results.")]= {},
    num_results: Annotated[int, Field(description="The number of results to return.", ge=1, le=100)] = 5,
) -> Annotated[list[Document], Field(description="A list of documents matching the search query.")]: 
    """Perform a vector search in the vector database.

    Args:
        query (str): The query string to search for in the vector database.
        category (str, optional): The category to filter the search results. Defaults to "".
        filter (dict, optional): Optional filter to apply to the search results. Defaults to {}.
        num_results (int): The number of results to return.
    Returns:
        list[Document]: A list of documents matching the search query.
    """
    results = await vector_search_tool(query, category, filter, num_results)
    return results    

# update documents
async def update_documents(data_list: Annotated[list[EmbeddingData], Field(description="A list of documents to update embeddings for.")]):
    """Update embeddings for a list of documents in the vector database.

    Args:
        data_list (list[Document]): A list of documents to update embeddings for.
    """

    config = EmbeddingConfig()
    embedding_client = EmbeddingClient(config)
    await embedding_client.update_documents(data_list)

# delete documents
async def delete_documents(source_id_list: Annotated[list[str], Field(description="A list of source IDs of documents to delete.")]):
    """Delete documents from the vector database based on a list of source IDs.

    Args:
        source_id_list (list[str]): A list of source IDs of documents to delete.
    """

    config = EmbeddingConfig()
    embedding_client = EmbeddingClient(config)
    await embedding_client.delete_documents_by_source_ids(source_id_list)

# get documents
async def get_documents(
    tags: Annotated[dict[str, list[str]], Field(description="A list of tags to filter documents by.")]= {},
) -> Annotated[list[Document], Field(description="A list of documents retrieved from the vector database.")]:
    """Retrieve documents from the vector database based on a list of source IDs.

    Args:
        tags (dict[str, Any]): A list of tags to filter documents by.
    Returns:
        list[Document]: A list of documents retrieved from the vector database.
    """

    config = EmbeddingConfig()
    embedding_client = EmbeddingClient(config)
    _, documents = await embedding_client.get_documents(tags)
    return documents

# update category
async def update_categories(
    categories: Annotated[list[CategoryData], Field(description="The list of categories to update.")],
):
    """Update a category in the vector database.

    Args:
        categories (list[CategoryData]): The list of categories to update.
    """

    config = EmbeddingConfig()
    embedding_client = EmbeddingClient(config)
    await embedding_client.update_categories(categories)

# delete category
async def delete_categories(
    name_list: Annotated[list[str], Field(description="The list of category names to delete.")],
):
    """Delete categories from the vector database based on a list of category names.

    Args:
        name_list (list[str]): The list of category names to delete.
    """

    config = EmbeddingConfig()
    embedding_client = EmbeddingClient(config)
    await embedding_client.delete_categories(name_list)

# get category
async def get_categories(
    ) -> Annotated[list[CategoryData], Field(description="The list of categories retrieved from the vector database.")]:
    """Retrieve all categories from the vector database.
    Returns:
        list[CategoryData]: The list of categories retrieved from the vector database.
    """
    config = EmbeddingConfig()
    embedding_client = EmbeddingClient(config)
    categories = await embedding_client.get_categories()
    return categories

# 引数解析用の関数
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCP server with specified mode and APP_DATA_PATH.")
    # -m オプションを追加
    parser.add_argument("-m", "--mode", choices=["sse", "stdio"], default="stdio", help="Mode to run the server in: 'sse' for Server-Sent Events, 'stdio' for standard input/output.")
    # -d オプションを追加　APP_DATA_PATH を指定する
    parser.add_argument("-d", "--app_data_path", type=str, help="Path to the application data directory.")
    # 引数を解析して返す
    # -t tools オプションを追加 toolsはカンマ区切りの文字列. search_wikipedia_ja_mcp, vector_search, etc. 指定されていない場合は空文字を設定
    parser.add_argument("-t", "--tools", type=str, default="", help="Comma-separated list of tools to use, e.g., 'search_wikipedia_ja_mcp,vector_search_mcp'. If not specified, no tools are loaded.")
    # -p オプションを追加　ポート番号を指定する modeがsseの場合に使用.defaultは5001
    parser.add_argument("-p", "--port", type=int, default=5001, help="Port number to run the server on. Default is 5001.")
    # -v LOG_LEVEL オプションを追加 ログレベルを指定する. デフォルトは空白文字
    parser.add_argument("-v", "--log_level", type=str, default="", help="Log level to set for the server. Default is empty, which uses the default log level.")

    return parser.parse_args()

async def main():
    # load_dotenv() を使用して環境変数を読み込む
    load_dotenv()
    # 引数を解析
    args = parse_args()
    mode = args.mode

    # tools オプションが指定されている場合は、ツールを登録
    if args.tools:
        tools = [tool.strip() for tool in args.tools.split(",")]
        for tool_name in tools:
            # tool_nameという名前の関数が存在する場合は登録
            tool = globals().get(tool_name)
            if tool and callable(tool):
                mcp.tool()(tool)
            else:
                print(f"Warning: Tool '{tool_name}' not found or not callable. Skipping registration.")
    else:
        # デフォルトのツールを登録
        mcp.tool()(vector_search)
        mcp.tool()(update_documents)
        mcp.tool()(delete_documents)
        mcp.tool()(get_documents)
        mcp.tool()(update_categories)
        mcp.tool()(delete_categories)
        mcp.tool()(get_categories)

    if mode == "stdio":
        await mcp.run_async()
    elif mode == "sse":
        # port番号を取得
        port = args.port
        await mcp.run_async(transport="sse", port=port)


if __name__ == "__main__":
    asyncio.run(main())
