from Ingestion_Pipline.config.settings import ChatModelSettings
from langchain.chat_models import init_chat_model


from Ingestion_Pipline.config.settings import ChatModelSettings
from langchain_openai import ChatOpenAI
import os


def build_chat_model(settings: ChatModelSettings | None = None):
    settings = settings or ChatModelSettings()

    return init_chat_model(
        settings.model,
        model_provider=settings.provider,
    )