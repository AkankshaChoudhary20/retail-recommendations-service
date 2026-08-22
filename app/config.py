"""Configuration read from environment variables.

Follows the RETAIL_<SERVICE>_<AREA>_<KEY> naming convention used by the
other services in the retail-store-sample-app (e.g. RETAIL_CART_PERSISTENCE_PROVIDER).
"""
import os


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


class Settings:
    redis_url: str = _env("RETAIL_RECOMMENDATIONS_REDIS_URL", "redis://localhost:6379/0")

    messaging_provider: str = _env("RETAIL_RECOMMENDATIONS_MESSAGING_PROVIDER", "none")
    rabbitmq_addresses: str = _env("RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_ADDRESSES", "localhost:5672")
    rabbitmq_username: str = _env("RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_USERNAME", "guest")
    rabbitmq_password: str = _env("RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_PASSWORD", "guest")
    # Must match RabbitMQMessagingConfig.EXCHANGE_NAME in the orders service.
    rabbitmq_exchange: str = _env("RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_EXCHANGE", "orders-exchange")
    rabbitmq_queue: str = _env("RETAIL_RECOMMENDATIONS_MESSAGING_RABBITMQ_QUEUE", "recommendations-orders-queue")

    default_limit: int = int(_env("RETAIL_RECOMMENDATIONS_DEFAULT_LIMIT", "5"))
    max_limit: int = int(_env("RETAIL_RECOMMENDATIONS_MAX_LIMIT", "25"))


settings = Settings()
