"""
VisionService: Online analyzer for webcam/IP frames with optional Google Vision
"""

from __future__ import annotations

import base64
import io
import json
import logging
from typing import Any, Dict, Optional

import cv2
import numpy as np
import requests

from ai_client.utils.config import Config


logger = logging.getLogger(__name__)


class VisionService:
    def __init__(self) -> None:
        self.config = Config()
        self.google_api_key: Optional[str] = self.config.get_vision_api_key()
        self._last_result: Optional[Dict[str, Any]] = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "opencv": True,
            "google_vision_configured": bool(self.google_api_key),
            "last_result_available": self._last_result is not None,
        }

    def analyze_frame(self, image_bytes: bytes, use_google: bool = False) -> Dict[str, Any]:
        """Analyze a single image frame with OpenCV and optional Google Vision."""
        try:
            # Decode image bytes to OpenCV image
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Failed to decode image bytes")

            height, width = frame.shape[:2]

            # Basic metrics
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = float(np.mean(gray))
            contrast = float(np.std(gray))
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

            # Dominant color (coarse)
            small = cv2.resize(frame, (32, 32))
            avg_bgr = np.mean(np.mean(small, axis=0), axis=0)
            avg_color = {
                "r": float(avg_bgr[2]),
                "g": float(avg_bgr[1]),
                "b": float(avg_bgr[0]),
            }

            result: Dict[str, Any] = {
                "opencv": {
                    "dimensions": {"width": width, "height": height},
                    "brightness": round(brightness, 2),
                    "contrast": round(contrast, 2),
                    "sharpness": round(sharpness, 2),
                    "avg_color": avg_color,
                }
            }

            # Optional Google Vision via REST API key
            if use_google and self.google_api_key:
                try:
                    b64 = base64.b64encode(image_bytes).decode("utf-8")
                    payload = {
                        "requests": [
                            {
                                "image": {"content": b64},
                                "features": [
                                    {"type": "LABEL_DETECTION", "maxResults": 5},
                                    {"type": "TEXT_DETECTION", "maxResults": 1},
                                ],
                            }
                        ]
                    }
                    url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_api_key}"
                    resp = requests.post(url, json=payload, timeout=8)
                    if resp.ok:
                        data = resp.json()
                        anns = data.get("responses", [{}])[0]
                        labels = [
                            {
                                "description": l.get("description"),
                                "score": l.get("score"),
                            }
                            for l in anns.get("labelAnnotations", [])
                        ]
                        text = anns.get("fullTextAnnotation", {}).get("text", "")
                        result["google_vision"] = {
                            "labels": labels,
                            "text": text[:2000],
                        }
                    else:
                        result["google_vision"] = {"error": f"HTTP {resp.status_code}"}
                except Exception as eg:
                    logger.warning(f"Google Vision error: {eg}")
                    result["google_vision"] = {"error": str(eg)}

            self._last_result = result
            return result

        except Exception as e:
            logger.error(f"VisionService analyze error: {e}")
            return {"error": str(e)}


# Singleton instance
vision_service = VisionService()


