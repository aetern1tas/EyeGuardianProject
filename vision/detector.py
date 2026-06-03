import cv2
import os
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from database.models import db, EyeRecord, FatigueLevel
from utils.logger import logger

class FatigueDetector:
    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    def __init__(self, user_id, session_id, session_obj=None, threshold=0.21, consecutive_frames=3):
        self.user_id = user_id
        self.session_id = session_id
        self.session_obj = session_obj
        self.threshold = threshold
        self.max_consecutive_frames = consecutive_frames
        self.consecutive_frames = 0
        self.is_running = False
        self.cap = None

        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        model_path = os.path.join(BASE_DIR, 'face_landmarker.task')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f'Модель не найдена по пути: {model_path}')

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
            min_face_detection_confidence=0.5
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        logger.info('FatigueDetector initialized (new API)')

    def calculate_ear(self, eye_points, landmarks):
        points = []
        for idx in eye_points:
            point = landmarks[idx]
            points.append((point.x, point.y))
        points = np.array(points)
        v1 = np.linalg.norm(points[1] - points[5])
        v2 = np.linalg.norm(points[2] - points[4])
        h = np.linalg.norm(points[0] - points[3])
        if h == 0:
            return 0
        ear = (v1 + v2) / (2.0 * h)
        return ear

    def detect_fatigue(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect(mp_image)

        if not result.face_landmarks:
            return None, FatigueLevel.UNKNOWN

        landmarks = result.face_landmarks[0]

        left_ear = self.calculate_ear(self.LEFT_EYE, landmarks)
        right_ear = self.calculate_ear(self.RIGHT_EYE, landmarks)
        avg_ear = (left_ear + right_ear) / 2

        if avg_ear < self.threshold:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0

        fatigue_level = FatigueLevel.LOW
        if self.consecutive_frames >= self.max_consecutive_frames:
            fatigue_level = FatigueLevel.HIGH

        self.save_record(avg_ear, fatigue_level)
        return avg_ear, fatigue_level

    def save_record(self, ear_score, fatigue_level):
        if ear_score is None:
            return
        record = EyeRecord(
            session_id=self.session_id,
            user_id=self.user_id,
            ear_score=ear_score,
            fatigue_level=fatigue_level
        )
        db.session.add(record)
        db.session.commit()

    def run(self):
        self.is_running = True
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logger.error('Camera not found')
            return

        state = 'welcome'
        break_start_time = None
        logger.info('Ready. Press [S] to start session')

        while self.is_running:
            if state == 'welcome':
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "EyeGuardian Pro", (160, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 2)
                cv2.putText(frame, "Press [S] to Start Session", (140, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (255, 255, 255), 2)
                cv2.putText(frame, "Press [Q] to Quit", (200, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                cv2.imshow('EyeGuardian - Fatigue Detection', frame)

                key = cv2.waitKey(100) & 0xFF
                if key == ord('s'):
                    state = 'active'
                    logger.info('Session started')
                elif key == ord('q'):
                    break

            elif state == 'active':
                ret, frame = self.cap.read()
                if not ret:
                    logger.error('Failed to read frame')
                    break

                avg_ear, fatigue_level = self.detect_fatigue(frame)

                if avg_ear is not None:
                    if fatigue_level == FatigueLevel.HIGH:
                        status = "HIGH FATIGUE - TAKE A BREAK!"
                        color = (0, 0, 255)
                    else:
                        status = "Low fatigue"
                        color = (0, 255, 0)
                    cv2.putText(frame, status, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(frame, f"EAR: {avg_ear:.3f}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                else:
                    cv2.putText(frame, "Face not detected", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                cv2.putText(frame, "[B] Break  |  [Q] Quit", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                cv2.imshow("EyeGuardian - Fatigue Detection", frame)

                key = cv2.waitKey(30) & 0xFF
                if key == ord('b'):
                    state = 'break'
                    break_start_time = time.time()
                    if self.session_obj:
                        self.session_obj.break_count += 1
                        db.session.commit()
                    logger.info('Break started')
                elif key == ord('q'):
                    break

            elif state == 'break':
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                elapsed = int(time.time() - break_start_time)
                mins, secs = divmod(elapsed, 60)

                cv2.putText(frame, "Break Time", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
                cv2.putText(frame, f"Duration: {mins:02d}:{secs:02d}", (200, 260), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2)
                cv2.putText(frame, "[R] Resume  |  [Q] Quit", (150, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (200, 200, 200), 2)

                cv2.imshow('EyeGuardian - Fatigue Detection', frame)

                key = cv2.waitKey(100) & 0xFF
                if key == ord('r'):
                    state = 'active'
                    logger.info('Resuming session')
                elif key == ord('q'):
                    break

        self.release()

    def release(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info('Resources released')