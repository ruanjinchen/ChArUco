from board import ChArUcoBoard
from typing import Tuple
from cv2 import aruco

import numpy as np
import cv2


def read_camera_parameters(filename: str) -> Tuple[np.ndarray, np.ndarray]:
    fs = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise Exception("Couldn't open file")
    _camera_matrix = fs.getNode("camera_matrix").mat()
    _dist_coefficients = fs.getNode("distortion_coefficients").mat()
    fs.release()
    return _camera_matrix, _dist_coefficients


def estimate_camera_pose_charuco(_detector, _board, frame, _camera_matrix, _dist_coefficients):
    corners, ids, rejected = _detector.detectMarkers(frame)
    if len(corners) == 0:
        raise Exception("No markers detected")
    display_frame = aruco.drawDetectedMarkers(image=frame, corners=corners)
    num_corners, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
        markerCorners=corners, markerIds=ids, image=frame, board=_board
    )
    if num_corners < 5:
        raise Exception("Not enough corners detected")
    display_frame = aruco.drawDetectedCornersCharuco(
        image=display_frame, charucoCorners=charuco_corners, charucoIds=charuco_ids
    )
    success, _rvec, _tvec = aruco.estimatePoseCharucoBoard(
        charuco_corners,
        charuco_ids,
        _board,
        _camera_matrix,
        _dist_coefficients,
        None,
        None,
        False,
    )
    if not success:
        raise Exception("Failed to estimate camera pose")
    # 让Z轴反转
    _rvec, *_ = cv2.composeRT(np.array([0, 0, -np.pi / 2]), _tvec * 0, _rvec, _tvec)
    _rvec, *_ = cv2.composeRT(np.array([0, np.pi, 0]), _tvec * 0, _rvec, _tvec)
    display_frame = cv2.drawFrameAxes(
        display_frame, _camera_matrix, _dist_coefficients, _rvec, _tvec, 0.2
    )
    cv2.imshow("Charuco", display_frame)
    return _rvec, _tvec


def main(_image_name):
    camera_matrix, dist_coefficients = read_camera_parameters("params/camera_params.yaml")
    board, aruco_dict, board_name = ChArUcoBoard(width=12, height=8, square_length=0.024)
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(aruco_dict, parameters)
    path = "image/" + _image_name
    image = cv2.imread(path)
    rvec, tvec = estimate_camera_pose_charuco(detector, board, image, camera_matrix, dist_coefficients)
    # print("旋转矢量: \n", rvec)
    # print("平移矢量: \n", tvec)
    # 对每个检测到的标记处理其旋转向量
    R, _ = cv2.Rodrigues(rvec)  # 现在 rvec[i, 0, :] 是一个1x3的旋转向量
    # 从旋转矩阵计算欧拉角 ZYX
    yaw = np.rad2deg(float(np.arctan2(R[1, 0], R[0, 0])))
    pitch = np.rad2deg(float(np.arctan2(-R[2, 0], np.sqrt(R[2, 1]**2 + R[2, 2]**2))))
    roll = np.rad2deg(float(np.arctan2(R[2, 1], R[2, 2])))
    rx = f"{roll:.3f}"
    ry = f"{pitch:.3f}"
    rz = f"{yaw:.3f}"
    X = str(tvec[0] * 1000)
    Y = str(tvec[1] * 1000)
    Z = str(tvec[2] * 1000)
    print(f"标定板的位置是(RPY): {X}, {Y}, {Z}, {rx}, {ry}, {rz}")
    cv2.waitKey(0)


if __name__ == "__main__":
    image_name = '8_Color.png'
    main(image_name)
