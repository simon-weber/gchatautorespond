import logging
import traceback
logger = logging.getLogger(__name__)


class ExceptionMiddleware(object):

    def process_exception(self, request, exception):
        logger.error(traceback.format_exc())
        return
