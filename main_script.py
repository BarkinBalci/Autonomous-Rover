from pathlib import Path
import cv2
import depthai as dai
import contextlib
import numpy as np
import time
import argparse
import sys
import math


nnPathDefault = str((Path(__file__).parent / Path('models/mobilenet-ssd_openvino_2021.2_5shave.blob')).resolve().absolute())
parser = argparse.ArgumentParser()
parser.add_argument('nnPath', nargs='?', help="Path to mobilenet detection network blob", default=nnPathDefault)
parser.add_argument('-s', '--sync', action="store_true", help="Sync RGB output with NN output", default=False)
args = parser.parse_args()

if not Path(nnPathDefault).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

# Start defining a pipeline
pipeline = dai.Pipeline()

lrcheck = False

# Define a source - mono cameras
left = pipeline.createMonoCamera()
left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
left.setBoardSocket(dai.CameraBoardSocket.LEFT)

right = pipeline.createMonoCamera()
right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
right.setBoardSocket(dai.CameraBoardSocket.RIGHT)

# Define a source - color camera
cam_rgb = pipeline.createColorCamera()
cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam_rgb.setPreviewSize(300, 300)
cam_rgb.setFps(30)
cam_rgb.setInterleaved(False)

# Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
stereo = pipeline.createStereoDepth()
stereo.initialConfig.setConfidenceThreshold(255)
stereo.setRectifyEdgeFillColor(0)  # Black, to better see the cutout from rectification (black stripe on the edges)
stereo.setLeftRightCheck(lrcheck)

# Define a neural network that will make predictions based on the source frames
nn = pipeline.createMobileNetDetectionNetwork()
nn.setConfidenceThreshold(0.5)
nn.setBlobPath(args.nnPath)
nn.setNumInferenceThreads(2)
nn.input.setBlocking(False)
cam_rgb.preview.link(nn.input)

# Create outputs
xout_video = pipeline.createXLinkOut()
xout_rgb = pipeline.createXLinkOut()
xout_disparity = pipeline.createXLinkOut()
xout_rectifiedRight = pipeline.createXLinkOut()

xout_video.setStreamName("video")
xout_rgb.setStreamName("rgb")
xout_disparity.setStreamName("depth")
xout_rectifiedRight.setStreamName("rectifiedRight")

if args.sync:
    nn.passthrough.link(xout_rgb.input)
else:
    cam_rgb.preview.link(xout_rgb.input)
    cam_rgb.video.link(xout_video.input)
    left.out.link(stereo.left)
    right.out.link(stereo.right)
    stereo.disparity.link(xout_disparity.input)
    stereo.rectifiedRight.link(xout_rectifiedRight.input)

nnOut = pipeline.createXLinkOut()
nnOut.setStreamName("nn")
nn.out.link(nnOut.input)

q_list = []

class trackbar:
    def __init__(self, trackbarName, windowName, minValue, maxValue, defaultValue, handler):
        cv2.createTrackbar(trackbarName, windowName, minValue, maxValue, handler)
        cv2.setTrackbarPos(trackbarName, windowName, defaultValue)

#WLS Filter TODO fix the sliders...
class wlsFilter:
    wlsStream = "wlsFilter"

    def on_trackbar_change_lambda(self, value):
        self._lambda = value * 100

    def on_trackbar_change_sigma(self, value):
        self._sigma = value / float(10)

    def __init__(self, _lambda, _sigma):
        self._lambda = _lambda
        self._sigma = _sigma
        self.wlsFilter = cv2.ximgproc.createDisparityWLSFilterGeneric(False)
        cv2.namedWindow(self.wlsStream)
        self.lambdaTrackbar = trackbar('Lambda', self.wlsStream, 0, 255, 80, self.on_trackbar_change_lambda)
        self.sigmaTrackbar = trackbar('Sigma', self.wlsStream, 0, 100, 15, self.on_trackbar_change_sigma)

    def filter(self, disparity, right, depthScaleFactor):
        # https://github.com/opencv/opencv_contrib/blob/master/modules/ximgproc/include/opencv2/ximgproc/disparity_filter.hpp#L92
        self.wlsFilter.setLambda(self._lambda)
        # https://github.com/opencv/opencv_contrib/blob/master/modules/ximgproc/include/opencv2/ximgproc/disparity_filter.hpp#L99
        self.wlsFilter.setSigmaColor(self._sigma)
        filteredDisp = self.wlsFilter.filter(disparity, right)

        # Compute depth from disparity (32 levels)
        with np.errstate(divide='ignore'):  # Should be safe to ignore div by zero here
            # raw depth values
            frame_depth = (depthScaleFactor / filteredDisp).astype(np.uint16)

        return filteredDisp, frame_depth


wlsFilter = wlsFilter(_lambda=8000, _sigma=1.5)

baseline = 75  # mm
disp_levels = 96
fov = 71.86



def frameNorm(frame, bbox):
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


def displayFrame(name, frame, detections):
    for detection in detections:
        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 8)
        cv2.putText(frame, labelMap[detection.label], (bbox[0] + 20, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 20, bbox[1] + 80), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0), 2)
    cv2.imshow(name, frame)

# MobilenetSSD label texts
labelMap = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

# https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack
with contextlib.ExitStack() as stack:
    for device_info in dai.Device.getAllAvailableDevices():
        device = stack.enter_context(dai.Device(pipeline, device_info))
        print("Connected to " + device_info.getMxId())
        # Output queue will be used to get the rgb frames from the output defined above
        q_video = device.getOutputQueue(name="video", maxSize=4, blocking=False)
        q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        q_det = device.getOutputQueue(name="nn", maxSize=4, blocking=False)
        q_right = device.getOutputQueue(name = "rectifiedRight", maxSize=4, blocking=False)
        q_disparity = device.getOutputQueue(name = "depth", maxSize=4, blocking=False)

        q_list.append(( q_video, q_rgb, q_det, q_right, q_disparity))

    while True:

        for i, (q_video, q_rgb, q_det, q_right, q_disparity) in enumerate(q_list):
            in_video = q_video.get()
            in_rgb = q_rgb.get()
            in_det = q_det.get()
            in_right = q_right.get()
            in_disparity = q_disparity.get()
            frame_rgb = in_rgb.getCvFrame()
            frame_video = in_video.getCvFrame()
            frame_right = in_right.getFrame()
            frame_disparity = in_disparity.getFrame()
            frame_right = cv2.flip(frame_right, flipCode=1)
            focal = frame_disparity.shape[1] / (2. * math.tan(math.radians(fov / 2)))
            depthScaleFactor = baseline * focal

            filteredDisp, frame_depth = wlsFilter.filter(frame_disparity, frame_right, depthScaleFactor)
            filteredDisp = (filteredDisp * (255 / (disp_levels - 1))).astype(np.uint8)
            coloredDisp = cv2.applyColorMap(filteredDisp, cv2.COLORMAP_JET)

            detections = []
            if in_det is not None:
                detections = in_det.detections
            cv2.namedWindow("video-" + str(i + 1), cv2.WINDOW_NORMAL)
            cv2.resizeWindow("video-" + str(i + 1), 1024, 576)
            displayFrame("video-" + str(i + 1), frame_video, detections)
            displayFrame(wlsFilter.wlsStream + str(i + 1), coloredDisp, detections)
        if cv2.waitKey(1) == ord('q'):
            break