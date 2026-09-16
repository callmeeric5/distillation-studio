import logging

logging.basicConfig(
    filename="rag.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("rag")
