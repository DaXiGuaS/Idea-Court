"""
配置读取：全部配置从 .env 加载，密钥不写进代码。

.env 路径固定为项目目录下，所以从任何目录启动都能读到。
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """应用配置。字段名对应 .env 里的变量名（不区分大小写）。"""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    llm_timeout: int = 60

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env 里多出来的变量不报错
    )


settings = Settings()
