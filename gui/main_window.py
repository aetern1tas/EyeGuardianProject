from vision.detector import FatigueDetector
from utils.logger import logger


class MainWindow:
    def __init__(self, user_id, session_id, session_obj=None):
        self.user_id = user_id
        self.session_id = session_id
        self.session_obj = session_obj   # можешь оставить, если нужен для других целей
        logger.info('MainWindow initialized')

    def run(self):
        detector = FatigueDetector(
            user_id=self.user_id,
            session_id=self.session_id
        )
        detector.run()