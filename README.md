# vector_search_util

## 概要

**vector_search_util** は、LangChain ベースのベクトル検索（登録・検索・削除）を扱うためのユーティリティライブラリです。

- Excel（`.xlsx`）からドキュメント/カテゴリ/リレーション/タグを一括投入・エクスポート
- CLI / REST API（FastAPI）/ MCP サーバー（FastMCP）として利用可能
- Vector DB は **Chroma**（ローカル永続）または **pgvector**（PostgreSQL）に対応

---

## 前提条件

- Python **3.11+**（`pyproject.toml` の `requires-python` に準拠）
- [uv](https://github.com/astral-sh/uv)

---

## セットアップ

```bash
cd vector-search-util
cp .env_template .env
uv sync
```

> `.env` は実行時設定です（OpenAI/Azure OpenAI、DB、保存先など）。

---

## CLI（コマンドライン）

CLI は `vector_search_util/__main__.py` に実装されています。

```bash
uv run -m vector_search_util --help
uv run -m vector_search_util <subcommand> --help
```

### サブコマンド一覧

- `search` : ベクトル検索（カテゴリ絞り込みのみ対応）
- `load_data` / `unload_data` / `delete_data` : ドキュメント（Excel）
- `list_category` / `load_category` / `unload_category` / `delete_category` : カテゴリ
- `list_relation` / `load_relation` / `unload_relation` / `delete_relation` : リレーション
- `list_tag` / `load_tag` / `unload_tag` / `delete_tag` : タグ

### オプション

#### 🔍 search
| オプション | 説明 |
|---|---|
| `-q, --query` | 検索クエリ（必須） |
| `-c, --category` | カテゴリ（任意、未指定なら全件） |
| `-k, --top_k` | 取得件数（デフォルト: 5） |

例:
```bash
uv run -m vector_search_util search -q "AIとは何か？" -k 5
uv run -m vector_search_util search -q "AIとは何か？" -c "tech" -k 5
```

#### 📥 load_data
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 入力 Excel ファイル（必須） |
| `--content_column` | 本文列名（デフォルト: `content`） |
| `--source_id_column` | ソースID列名（デフォルト: `source_id`） |
| `--category_column` | カテゴリ列名（デフォルト: `category`） |
| `-m, --metadata_columns` | メタデータ列名（複数指定可） |
| `--append_vectors` | 既存 source_id を削除せず追記（append）する |

例:
```bash
uv run -m vector_search_util load_data -i data.xlsx -m author url
```

#### 📤 unload_data
| オプション | 説明 |
|---|---|
| `-o, --output_file` | 出力 Excel ファイル（必須） |

例:
```bash
uv run -m vector_search_util unload_data -o output.xlsx
```

#### 🗑 delete_data
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 削除対象 Excel（必須） |
| `--source_id_column` | ソースID列名（デフォルト: `source_id`） |

例:
```bash
uv run -m vector_search_util delete_data -i delete_list.xlsx
```

#### 🏷 カテゴリ

`list_category` は引数なしです。

`load_category`:
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 入力 Excel（必須） |
| `--name_column` | 名前列名（デフォルト: `name`） |
| `--description_column` | 説明列名（デフォルト: `description`） |
| `-m, --metadata_columns` | メタデータ列名（複数指定可） |

`unload_category`:
| オプション | 説明 |
|---|---|
| `-o, --output_file` | 出力 Excel（必須） |

`delete_category`:
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 削除対象 Excel（必須） |
| `--name_column` | 名前列名（デフォルト: `name`） |

例:
```bash
uv run -m vector_search_util list_category
uv run -m vector_search_util load_category -i category.xlsx
uv run -m vector_search_util unload_category -o category_out.xlsx
uv run -m vector_search_util delete_category -i category_delete.xlsx
```

#### 🔗 リレーション

`list_relation` は引数なしです。

`load_relation`:
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 入力 Excel（必須） |
| `--from_node_column` | from 列名（デフォルト: `from_node`） |
| `--to_node_column` | to 列名（デフォルト: `to_node`） |
| `--edge_type_column` | type 列名（デフォルト: `edge_type`） |
| `-m, --metadata_columns` | メタデータ列名（複数指定可） |

`unload_relation`:
| オプション | 説明 |
|---|---|
| `-o, --output_file` | 出力 Excel（必須） |

`delete_relation`:
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 削除対象 Excel（必須） |
| `--from_node_column` | from 列名（デフォルト: `from_node`） |
| `--to_node_column` | to 列名（デフォルト: `to_node`） |
| `--edge_type_column` | type 列名（デフォルト: `edge_type`） |

例:
```bash
uv run -m vector_search_util list_relation
uv run -m vector_search_util load_relation -i relation.xlsx
uv run -m vector_search_util unload_relation -o relation_out.xlsx
uv run -m vector_search_util delete_relation -i relation_delete.xlsx
```

#### 🏷 タグ

`list_tag` は引数なしです。

`load_tag`:
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 入力 Excel（必須） |
| `--name_column` | 名前列名（デフォルト: `name`） |
| `--description_column` | 説明列名（デフォルト: `description`） |
| `-m, --metadata_columns` | メタデータ列名（複数指定可） |

`unload_tag`:
| オプション | 説明 |
|---|---|
| `-o, --output_file` | 出力 Excel（必須） |

`delete_tag`:
| オプション | 説明 |
|---|---|
| `-i, --input_file_path` | 削除対象 Excel（必須） |
| `--name_column` | 名前列名（デフォルト: `name`） |

例:
```bash
uv run -m vector_search_util list_tag
uv run -m vector_search_util load_tag -i tag.xlsx
uv run -m vector_search_util unload_tag -o tag_out.xlsx
uv run -m vector_search_util delete_tag -i tag_delete.xlsx
```

---

## Python から利用（ライブラリとして）

高度なフィルタ（メタデータ条件）を使いたい場合は、Python から `ConditionContainer` を利用できます。

```python
import asyncio
from vector_search_util.core.client import EmbeddingClient
from vector_search_util.model import ConditionContainer

async def main():
    client = EmbeddingClient()

    # metadata の author が "alice" のものだけ検索
    cond = ConditionContainer().add_eq_condition("author", "alice")

    results = await client.vector_search(
        query="AIとは何か？",
        category="",
        condition=cond,
        top_k=5,
    )
    for r in results:
        print(r.source_id, r.category)

asyncio.run(main())
```

---

## REST API サーバー（FastAPI）

`api/api_server.py` は FastAPI アプリです。

### 起動方法

```bash
uv run -m vector_search_util.api.api_server
```

- デフォルト: `http://localhost:8000`
- ヘルスチェック: `GET /ping`

### 主なエンドポイント（抜粋）

| メソッド | パス | 概要 |
|---|---|---|
| `GET` | `/vector_search` | ベクトル検索（`query`, `category`, `num_results`） |
| `GET` | `/get_documents` | ドキュメント取得（`source_ids`, `category_ids`） |
| `POST` | `/upsert_documents` | ドキュメント upsert |
| `DELETE` | `/delete_documents` | ドキュメント削除 |
| `GET` | `/get_categories` | カテゴリ一覧 |
| `GET` | `/get_relations` | リレーション一覧 |
| `GET` | `/get_tags` | タグ一覧 |
| `POST` | `/load_documents_from_excel` | Excel からロード |
| `GET` | `/unload_documents_to_excel` | Excel へエクスポート |
| `DELETE` | `/delete_documents_from_excel` | Excel 指定で削除 |

例（検索）:
```bash
curl 'http://localhost:8000/vector_search?query=AI%E3%81%A8%E3%81%AF%E4%BD%95%E3%81%8B%EF%BC%9F&num_results=5'
```

---

## MCP サーバー（FastMCP）

`mcp/mcp_server.py` は MCP サーバーとして動作します。

### 起動方法

標準入出力（stdio）:
```bash
uv run -m vector_search_util.mcp.mcp_server -m stdio
```

Streamable HTTP:
```bash
uv run -m vector_search_util.mcp.mcp_server -m http -p 5001
```

### 引数

| オプション | 説明 |
|---|---|
| `-m, --mode` | `http` または `stdio`（デフォルト: `stdio`） |
| `-p, --port` | HTTP のポート（デフォルト: 5001） |
| `-t, --tools` | 登録するツールをカンマ区切りで指定（未指定時は主要ツールを一括登録） |
| `-v, --log_level` | ログレベル（空ならデフォルト） |

---

## Docker（MCP サーバーを HTTP で起動）

このリポジトリの `docker-compose.yml` は MCP サーバーを **Streamable HTTP** で起動する設定です。

```bash
cd vector-search-util
cp .env_template .env
# 必要に応じて .env の HOST_PORT を変更

docker compose up --build
```

- コンテナ内ポート: `5001`（固定）
- ホスト公開ポート: `.env` の `HOST_PORT`（未指定なら `5001`）

---

## ディレクトリ構成

```
src/vector_search_util/
├── _internal/         # LangChain/DB/ログ等の内部実装
├── api/               # FastAPI サーバー
├── core/              # EmbeddingClient / BatchClient
├── mcp/               # MCP サーバー
├── model/             # EmbeddingConfig / Pydantic model / ConditionContainer
└── __main__.py        # CLI エントリーポイント
```

---

## 環境変数（.env）

`.env_template` を参照してください（主要項目のみ抜粋）。

### メタデータキー

| 変数名 | デフォルト | 説明 |
|---|---:|---|
| `SOURCE_ID_KEY` | `source_id` | source_id として扱うメタデータキー |
| `CATEGORY_KEY` | `category` | category として扱うメタデータキー |
| `SOURCE_CONTENT_KEY` | `source_content` | 本文キー |
| `UPDATED_AT_KEY` | `updated_at` | 更新日時キー |
| `FIRST_DOCUMENT_KEY` | `first_document` | chunk 先頭判定キー |

### 動作設定

| 変数名 | デフォルト | 説明 |
|---|---:|---|
| `CHUNK_SIZE` | `4000` | ベクトル化前の分割サイズ |
| `EMBEDDING_CONCURRENCY` | `16` | 非同期処理の並列度 |
| `APP_DATA_PATH` | `work/app_data` | SQLite（管理DB）の保存先 |

### Vector DB

| 変数名 | 例 | 説明 |
|---|---|---|
| `VECTOR_DB_TYPE` | `chroma` / `pgvector` | ベクトルDB種別 |
| `VECTOR_DB_URL` | `work/chroma_db` / `postgresql+psycopg://...` | 保存先 or 接続文字列 |
| `VECTOR_DB_COLLECTION_NAME` | `sample_collection` | コレクション名 |

### LLM/Embedding

| 変数名 | 例 | 説明 |
|---|---|---|
| `LLM_PROVIDER` | `openai` / `azure_openai` | プロバイダ |
| `OPENAI_API_KEY` | `...` | APIキー |
| `OPENAI_COMPLETION_MODEL` | `gpt-5` | 生成モデル |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | 埋め込みモデル |
| `OPENAI_BASE_URL` | `http://...` | OpenAI互換エンドポイント（任意） |
| `AZURE_OPENAI_API_VERSION` | `2024-xx-xx` | Azure OpenAI の API version |
| `AZURE_OPENAI_ENDPOINT` | `https://...` | Azure OpenAI endpoint |

---

## 変更履歴

- README は現状の実装（CLI/API/MCP/Docker/環境変数）に合わせて記載しています。
