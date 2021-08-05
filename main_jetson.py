from pathlib import Path
import cv2
import depthai as dai
import contextlib
import numpy as np
import time
import argparse
import sys
import math
import matplotlib.pyplot as plt
from ESC_Jetson import leftMotorSpeed, rightMotorSpeed, disarm


nnPathDefault = str((Path(__file__).parent / Path('models/mobilenet-ssd_openvino_2021.2_5shave.blob')).resolve().absolute())
parser = argparse.ArgumentParser()

logo = cv2.imread('/home/barkin/Autonomous-Rover/images/nvidia.png')

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
xout_rgb = pipeline.createXLinkOut()
xout_disparity = pipeline.createXLinkOut()
xout_rectifiedRight = pipeline.createXLinkOut()

xout_rgb.setStreamName("rgb")
xout_disparity.setStreamName("depth")
xout_rectifiedRight.setStreamName("rectifiedRight")

if args.sync:
    nn.passthrough.link(xout_rgb.input)
else:
    cam_rgb.preview.link(xout_rgb.input)
    left.out.link(stereo.left)
    right.out.link(stereo.right)
    stereo.disparity.link(xout_disparity.input)
    stereo.rectifiedRight.link(xout_rectifiedRight.input)

nnOut = pipeline.createXLinkOut()
nnOut.setStreamName("nn")
nn.out.link(nnOut.input)

q_list = []
settings = False

class trackbar:
    def __init__(self, trackbarName, windowName, minValue, maxValue, defaultValue, handler):
        cv2.createTrackbar(trackbarName, windowName, minValue, maxValue, handler)
        cv2.setTrackbarPos(trackbarName, windowName, defaultValue)

#WLS Filter
class wlsFilter:
    wlsName = "Settings"
    def on_trackbar_change_lambda(self, value):
        self._lambda = value * 100

    def on_trackbar_change_sigma(self, value):
        self._sigma = value / float(10)

    def __init__(self, _lambda, _sigma):
        self._lambda = _lambda
        self._sigma = _sigma
        self.wlsFilter = cv2.ximgproc.createDisparityWLSFilterGeneric(False)
        if settings == True:
            cv2.imshow(self.wlsName, logo)
            cv2.namedWindow(self.wlsName, cv2.WINDOW_AUTOSIZE)
            self.lambdaTrackbar = trackbar('Lambda', self.wlsName, 0, 255, 80, self.on_trackbar_change_lambda)
            self.sigmaTrackbar = trackbar('Sigma', self.wlsName, 0, 100, 15, self.on_trackbar_change_sigma)

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
coloredDisp = {}
collision = {}
collision[0] = True
collision[1] = True
collision[2] = True
fig, ax = plt.subplots()

ax.set_title('Histogram (RGB)')

ax.set_xlabel('Bin')
ax.set_ylabel('Frequency')
# Initialize plot line object(s). Turn on interactive plotting and show plot.
lw = 3
alpha = 0.5
lineR, = ax.plot(np.arange(10), np.zeros((10,)), c='r', lw=lw, alpha=alpha)
lineG, = ax.plot(np.arange(10), np.zeros((10,)), c='g', lw=lw, alpha=alpha)
lineB, = ax.plot(np.arange(10), np.zeros((10,)), c='b', lw=lw, alpha=alpha)

ax.set_xlim(0, 10 - 1)
ax.set_ylim(0, 1)
plt.ion()


def frameNorm(frame, bbox):
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


def displayFrame(name, frame, detections):
    for detection in detections:
        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))

        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 255, 255), 6)
        cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (255, 255, 255), 3)
        cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (255, 255, 255), 3)

        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 1)

    cv2.imshow(name, frame)

# MobilenetSSD label texts
labelMap = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

# https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack
with contextlib.ExitStack() as stack:
    for device_info in dai.Device.getAllAvailableDevices():
        device = stack.enter_context(dai.Device(pipeline, device_info))
        print("Connected to " + device_info.getMxId())
        # Output queue will be used to get the rgb frames from the output defined above
        q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        q_det = device.getOutputQueue(name="nn", maxSize=4, blocking=False)
        q_right = device.getOutputQueue(name = "rectifiedRight", maxSize=4, blocking=False)
        q_disparity = device.getOutputQueue(name = "depth", maxSize=4, blocking=False)

        q_list.append((q_rgb, q_det, q_right, q_disparity))

    while True:

        for i, (q_rgb, q_det, q_right, q_disparity) in enumerate(q_list):
            in_rgb = q_rgb.get()
            in_det = q_det.get()
            in_right = q_right.get()
            in_disparity = q_disparity.get()
            frame_rgb = in_rgb.getCvFrame()
            frame_right = in_right.getFrame()
            frame_disparity = in_disparity.getFrame()
            frame_right = cv2.flip(frame_right, flipCode=1)
            focal = frame_disparity.shape[1] / (2. * math.tan(math.radians(fov / 2)))
            depthScaleFactor = baseline * focal
            filteredDisp, frame_depth = wlsFilter.filter(frame_disparity, frame_right, depthScaleFactor)
            filteredDisp = (filteredDisp * (255 / (disp_levels - 1))).astype(np.uint8)
            coloredDisp[i] = cv2.applyColorMap(filteredDisp, cv2.COLORMAP_JET)
            numPixels = np.prod(coloredDisp[i].shape[:2])
            (b, g, r) = cv2.split(coloredDisp[i])
            histogramR = cv2.calcHist([r], [0], None, [10], [0, 255]) / numPixels
            histogramG = cv2.calcHist([g], [0], None, [10], [0, 255]) / numPixels
            histogramB = cv2.calcHist([b], [0], None, [10], [0, 255]) / numPixels
            percentageR = cv2.calcHist([r], [0], None, [1], [0, 255]) / numPixels / 10
            percentageG = cv2.calcHist([g], [0], None, [1], [0, 255]) / numPixels / 10
            percentageB = cv2.calcHist([b], [0], None, [1], [0, 255]) / numPixels / 10
            if percentageR < 0.08:
                collision[i] = True
                print("Possible Collision on OAK-D #" + str(i))
            if percentageR > 0.08:
                collision[i] = False
                print("OAK-D #" + str(i) + "is clear.")
            if collision[0] == False and collision[1] == False and collision[2] == False:
                leftMotorSpeed(60)
                rightMotorSpeed(60)
                print("Status: Going Forward")
            if collision[0] == True and collision[1] == False and collision[2] == True:
                leftMotorSpeed(60)
                rightMotorSpeed(60)
                print("Status: Going Forward")
            if collision[0] == False and collision[1] == True and collision[2] == False:
                leftMotorSpeed(60)
                rightMotorSpeed(40)
                print("Status: Turning Right")
            if collision[0] == True and collision[1] == False and collision[2] == False:
                leftMotorSpeed(60)
                rightMotorSpeed(40)
                print("Status: Turning Right")
            if collision[0] == True and collision[1] == True and collision[2] == False:
                leftMotorSpeed(60)
                rightMotorSpeed(40)
                print("Status: Turning Right")
            if collision[0] == False and collision[1] == False and collision[2] == True:
                leftMotorSpeed(40)
                rightMotorSpeed(60)
                print("Status: Turning Left")
            if collision[0] == False and collision[1] == True and collision[2] == True:
                leftMotorSpeed(40)
                rightMotorSpeed(60)
                print("Status: Turning Left")
            if collision[0] == True and collision[1] == True and collision[2] == True:
                leftMotorSpeed(40)
                rightMotorSpeed(60)
                print("Status: Turning Left")
            detections = []
            if in_det is not None:
                detections = in_det.detections
        if cv2.waitKey(1) == ord('q'):
            disarm()
            break