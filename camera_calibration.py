from board import ChArUcoBoard
from pathlib import Path
from cv2 import aruco

import glob
import cv2


board, aruco_dict, board_name = ChArUcoBoard(width=12, height=8, square_length=0.024)
corners_all = []
ids_all = []
image_size = None
images = glob.glob('./image/*.png')
for image in images:
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco.detectMarkers(
            image=gray,
            dictionary=aruco_dict)
    img = aruco.drawDetectedMarkers(
            image=img, 
            corners=corners)
    response, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
            markerCorners=corners,
            markerIds=ids,
            image=gray,
            board=board)
    # 至少出现20个方块才认为该张标定图片合格,可以进行后续标定
    if response > 20:
        corners_all.append(charuco_corners)
        ids_all.append(charuco_ids)
        img = aruco.drawDetectedCornersCharuco(
                image=img,
                charucoCorners=charuco_corners,
                charucoIds=charuco_ids)
        if not image_size:
            image_size = gray.shape[::-1]
        proportion = max(img.shape) / 1000.0
        img = cv2.resize(img, (int(img.shape[1]/proportion), int(img.shape[0]/proportion)))
        cv2.imshow('Charuco board', img)
        cv2.waitKey(0)
    else:
        print("无法检测图像中的标定板: {}".format(image))


cv2.destroyAllWindows()

if len(images) < 1:
    print("标定失败, 没有标定图片"
          "请拍摄图片并保存至/image文件夹中")
    exit()
if not image_size:
    print("标定失败, 您所提供的图片中我们无法检测出特征点"
          "请重试, 尝试重新传入标定板方格的实际大小或者更换标定板")
    exit()

calibration, camera_matrix, dist_coefficients, rvecs, tvecs = aruco.calibrateCameraCharuco(
        charucoCorners=corners_all,
        charucoIds=ids_all,
        board=board,
        imageSize=image_size,
        cameraMatrix=None,
        distCoeffs=None)

print("相机内参矩阵:\n", camera_matrix)
print("相机畸变:\n", dist_coefficients)

output_path = "./params/camera_params.yaml"
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
fs = cv2.FileStorage(output_path, cv2.FILE_STORAGE_WRITE)
if not fs.isOpened():
    raise Exception("路径错误!")
fs.write("camera_matrix", camera_matrix)
fs.write("distortion_coefficients", dist_coefficients)
fs.release()
print(f"标定成功, 标定结果保存在: {output_path}")
