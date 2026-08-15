import logging

logger = logging.getLogger("agents")

logging.baseConfig(
    level = logging.INFO,
    format = "%(asctime)s %(levelname)s %(message)s"
)