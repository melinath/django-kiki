import logging
import logging.handlers
from django.conf import settings


FILENAME = getattr(settings, 'STEPPING_OUT_MAIL_LOG_PATH', '.mail.log')

LOGGER = logging.getLogger('stepping_out.mail')
LOGGER.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(
	FILENAME,
	maxBytes=10000,
	backupCount=5
)
handler.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

FORMAT = getattr(settings, 'STEPPING_OUT_MAIL_LOG_FORMAT', '%(asctime)s %(msgid)s %(message)s')
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)


def test():
	log = logging.LoggerAdapter(LOGGER, {'msgid': 1})
	log.debug('debug message', )
	log.info("info message")
	log.warning("warn message")
	log.error("error message")
	log.critical("critical message")