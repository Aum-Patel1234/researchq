from logging import Logger
from pathlib import Path
import tempfile
import traceback


def save_uploaded_file(uploaded_file, logger: Logger) -> Path:
    """Save uploaded file to a temporary location."""
    try:
        suffix = Path(uploaded_file.name).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            logger.info(f"Saved uploaded file to {tmp.name}")
            return Path(tmp.name)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
