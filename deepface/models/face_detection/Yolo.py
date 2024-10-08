# built-in dependencies
from typing import Any, List

# 3rd party dependencies
import numpy as np
from dotenv import dotenv_values

# project dependencies
from deepface.models.Detector import Detector, FacialAreaRegion
from deepface.commons import weight_utils
from deepface.commons.logger import Logger

logger = Logger()

# Model's weights paths
PATH = ".deepface/weights/yolov8n-face.pt"

# Google Drive URL from repo (https://github.com/derronqi/yolov8-face) ~6MB
WEIGHT_URL = "https://drive.google.com/uc?id=1qcr9DbgsX3ryrz2uU8w4Xm3cOrRywXqb"


class YoloClient(Detector):
    def __init__(self):
        self.model = self.build_model()
        #self.config = dotenv_values(".env")

    def build_model(self) -> Any:
        config = dotenv_values(".env")
        """
        Build a yolo detector model
        Returns:
            model (Any)
        """

        # Import the optional Ultralytics YOLO model
        try:
            from ultralytics import YOLO
        except ModuleNotFoundError as e:
            raise ImportError(
                "Yolo is an optional detector, ensure the library is installed. "
                "Please install using 'pip install ultralytics'"
            ) from e

        if ("CUSTOM_YOLO_WEIGHTS" in config and config["YOLO_CUSTOM_WEIGHTS"]):
            weight_file =  config["YOLO_CUSTOM_WEIGHTS"]
        else:
            weight_file = weight_utils.download_weights_if_necessary(
                file_name="yolov8n-face.pt", source_url=WEIGHT_URL
            )

        # Return face_detector
        return YOLO(weight_file)

    def detect_faces(self, img: np.ndarray) -> List[FacialAreaRegion]:
        config = dotenv_values(".env")
        """
        Detect and align face with yolo

        Args:
            img (np.ndarray): pre-loaded image as numpy array

        Returns:
            results (List[FacialAreaRegion]): A list of FacialAreaRegion objects
        """
        resp = []

        if ("YOLO_DEVICE" in config and config["YOLO_DEVICE"]):
            yolo_device = config["YOLO_DEVICE"]
        else:
            yolo_device = "cuda:0"
        logger.debug(f"YOLO_DEVICE: {yolo_device}")

        if ("YOLO_CONFIDENCE" in config and config["YOLO_CONFIDENCE"]):
            yolo_confidence = float(config["YOLO_CONFIDENCE"])
        else:
            yolo_confidence = 0.25


        # Detect faces
        results = self.model.predict(img, verbose=False, show=False, conf=yolo_confidence, device=yolo_device)[0]

        # For each face, extract the bounding box, the landmarks and confidence
        for result in results:

            if result.boxes is None or result.keypoints is None:
                continue

            # Extract the bounding box and the confidence
            x, y, w, h = result.boxes.xywh.tolist()[0]
            confidence = result.boxes.conf.tolist()[0]

            # right_eye_conf = result.keypoints.conf[0][0]
            # left_eye_conf = result.keypoints.conf[0][1]
            right_eye = result.keypoints.xy[0][0].tolist()
            left_eye = result.keypoints.xy[0][1].tolist()

            # eyes are list of float, need to cast them tuple of int
            left_eye = tuple(int(i) for i in left_eye)
            right_eye = tuple(int(i) for i in right_eye)

            x, y, w, h = int(x - w / 2), int(y - h / 2), int(w), int(h)
            facial_area = FacialAreaRegion(
                x=x,
                y=y,
                w=w,
                h=h,
                left_eye=left_eye,
                right_eye=right_eye,
                confidence=confidence,
            )
            resp.append(facial_area)

        return resp
