import logging
import sys

def setup_logging():
    """Configures centralized logging for the entire application."""
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("MEDiFLOW")

logger = setup_logging()