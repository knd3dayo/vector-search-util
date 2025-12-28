from langchain_core.embeddings import Embeddings

from vector_search_util.model import EmbeddingConfig
from vector_search_util._internal.langchain.langchain_client import LangchainClient, LangchainOpenAIClient, LangchainAzureOpenAIClient

import vector_search_util._internal.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class LangchainFactory:

    @classmethod
    def create_client(cls, llm_config: EmbeddingConfig = EmbeddingConfig()) -> LangchainClient:

        if llm_config.llm_provider == "openai":
            client = LangchainOpenAIClient(llm_config)
            return client
        elif llm_config.llm_provider == "azure_openai":
            client = LangchainAzureOpenAIClient(llm_config)
            return client
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.llm_provider}")

        
