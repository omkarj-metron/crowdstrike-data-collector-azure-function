import os
import logging
from dotenv import load_dotenv


def setup_logger(name: str, logfile: str = None) -> logging.Logger:
    """Create and configure a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Clear handlers if re-running
    if logger.handlers:
        logger.handlers = []

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(message)s")
    
    # Console handler (INFO level)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # File handler if path provided (DEBUG level)
    if logfile:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


def get_env_config():
    """Load and validate environment configuration.
    
    In Azure Functions, environment variables are set via Application Settings.
    load_dotenv() will only load from .env file if it exists (useful for local dev).
    """
    # Only load .env if it exists (for local development)
    # In Azure Functions, environment variables are set via Application Settings
    if os.path.exists(".env"):
        load_dotenv()

    # Required CrowdStrike config
    script_file_names = os.getenv("SCRIPT_FILE_NAMES")
    if not script_file_names:
        raise ValueError("SCRIPT_FILE_NAMES environment variable not set. Provide comma-separated script filenames.")
    script_names = [s.strip() for s in script_file_names.split(",") if s.strip()]

    # Optional config with defaults
    upload_to_bh = os.getenv("UPLOAD_TO_BLOODHOUND", "false").lower() in ("1", "true", "yes")
    
    try:
        max_retries = int(os.getenv("MAX_RETRIES", "10"))
    except ValueError:
        max_retries = 10
    
    try:
        retry_delay = int(os.getenv("RETRY_DELAY", "5"))
    except ValueError:
        retry_delay = 5

    return {
        "script_names": script_names,
        "upload_to_bh": upload_to_bh,
        "max_retries": max_retries,
        "retry_delay": retry_delay
    }


def ensure_directories():
    """Create required directories if they don't exist.
    
    In Azure Functions (cloud), use /tmp for temporary storage or Azure Files for persistent storage.
    For local development (including func start), use current directory.
    """
    # Check if running in Azure Functions cloud (not local func start)
    # Azure Functions cloud sets WEBSITE_INSTANCE_ID, local func start does not
    is_azure_cloud = os.environ.get("WEBSITE_INSTANCE_ID") is not None
    
    if is_azure_cloud:
        # Running in Azure Functions cloud - use /tmp for temporary storage
        # For persistent storage, consider using Azure Files or Blob Storage
        base_dir = "/tmp"
    else:
        # Running locally (func start or standalone) - use current directory
        base_dir = os.getcwd()
    
    logs_dir = os.path.join(base_dir, "logs")
    rtr_result_dir = os.path.join(base_dir, "rtr-result")
    
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(rtr_result_dir, exist_ok=True)
    
    return logs_dir, rtr_result_dir