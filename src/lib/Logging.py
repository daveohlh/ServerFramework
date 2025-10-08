import sys

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from loguru import logger

from lib.Environment import env

logger.remove()

log_level = env("LOG_LEVEL")
server_timezone = env("TZ")


def format_with_timezone(record):
    """Format log record with server timezone"""
    if server_timezone != "UTC":
        # Convert UTC time to server timezone for display
        utc_time = record["time"].replace(tzinfo=ZoneInfo("UTC"))
        local_time = utc_time.astimezone(ZoneInfo(server_timezone))
        record["time"] = local_time
    return record


LOG_LEVEL_MAP = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "VERBOSE": 5,
    "SQL": 3,
    "NOTSET": 0,
}
logger.level("VERBOSE", no=5, color="<blue>")
logger.level("SQL", no=3, color="<magenta>")

logger.add(sys.stdout, level=log_level, filter=format_with_timezone)
