import ssl

import pika


class RabbitMQConnection:
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool):
        self.protocol = "amqps" if use_tls else "amqp"
        self.url = f"{self.protocol}://{username}:{password}@{host}:{port}"
        self.parameters = pika.URLParameters(self.url)

        if use_tls:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.set_ciphers("ECDHE+AESGCM:!ECDSA")
            self.parameters.ssl_options = pika.SSLOptions(context=ssl_context)

    def get_channel(self) -> tuple[pika.BlockingConnection, pika.channel.Channel]:
        connection = pika.BlockingConnection(self.parameters)
        channel = connection.channel()
        return connection, channel


def validate_rabbitmq_name(name: str, field_name: str) -> None:
    """Validate RabbitMQ queue/exchange names"""
    if not name or not name.strip():
        raise ValueError(f"{field_name} cannot be empty")
    if not all(c.isalnum() or c in "-_.:" for c in name):
        raise ValueError(
            f"{field_name} can only contain letters, digits, hyphen, underscore, period, or colon"
        )
    if len(name) > 255:
        raise ValueError(f"{field_name} must be less than 255 characters")
