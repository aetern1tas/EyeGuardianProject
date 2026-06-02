from vision.detector import FatigueDetector
from utils.logger import logger


class MainWindow:
    def __init__(self, user_id, session_id, session_obj=None):
        self.user_id = user_id
        self.session_id = session_id
        self.session_obj = session_obj   
        logger.info('MainWindow initialized')

    def run(self):
        detector = FatigueDetector(
            user_id=self.user_id,
            session_id=self.session_id
        )
        detector.run()
