import numpy as np

GESTURES = ["NONE", "FIST", "1", "2", "3", "PALM"]


def landmarks_to_features(landmarks):
    """Turn MediaPipe's 21 hand landmarks into a position- and size-independent vector."""
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
    pts -= pts[0]  # make the wrist the origin, so it doesn't matter where the hand is in the frame
    scale = np.max(np.linalg.norm(pts[:, :2], axis=1))
    if scale > 0:
        pts /= scale  # so it doesn't matter how close the hand is to the camera
    return pts.flatten()
