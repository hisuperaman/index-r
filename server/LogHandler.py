from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, Formatter, StreamHandler, FileHandler

from config import LOG_DIR

SYSLOG_LEVEL_MAP = {
	DEBUG: 7,
	INFO: 6,
	WARNING: 4,
	ERROR: 3,
	CRITICAL: 2,
}


class LogFormatter(Formatter):
	def __init__(self):
		super().__init__('%(asctime)s\t- %(levelname)s\t- %(name)s:%(lineno)d\t- %(message)s')

	def format(self, record):
		msg = super().format(record)
		return f"<{SYSLOG_LEVEL_MAP.get(record.levelno, 6)}>{msg}"


class LogHandler(StreamHandler):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setFormatter(LogFormatter())


class DebugLogHandler(LogHandler, FileHandler):

	def __init__(self):
		super().__init__(LOG_DIR / 'debug.log', encoding='utf-8')
