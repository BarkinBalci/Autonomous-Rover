from pathlib import Path
import cv2
import depthai as dai
import contextlib
import numpy as np
import time
import argparse

nnPathDefault = str((Path(__file__).parent / Path('models/mobilenet-ssd_openvino_2021.2_6shave.blob')).resolve().absolute())
parser = argparse.ArgumentParser()
parser.add_argument('nnPath', nargs='?', help="Path to mobilenet detection network blob", default=nnPathDefault)
parser.add_argument('-s', '--sync', action="store_true", help="Sync RGB output with NN output", default=False)
args = parser.parse_args()

if not Path(nnPathDefault).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

# Start defining a pipeline
pipeline = dai.Pipeline()

# Define a source - color camera
cam_rgb = pipeline.createColorCamera()
cam_rgb.setPreviewSize(300, 300)
cam_rgb.setFps(40)
cam_rgb.setInterleaved(False)

# Define a neural network that will make predictions based on the source frames
nn = pipeline.createMobileNetDetectionNetwork()
nn.setConfidenceThreshold(0.5)
nn.setBlobPath(args.nnPath)
nn.setNumInferenceThreads(2)
nn.input.setBlocking(False)
cam_rgb.preview.link(nn.input)

# Create outputs
xout_rgb = pipeline.createXLinkOut()
xout_rgb.setStreamName("rgb")
if args.sync:
    nn.passthrough.link(xout_rgb.input)
    print("1")
else:
    cam_rgb.preview.link(xout_rgb.input)
    print("0")
nnOut = pipeline.createXLinkOut()
nnOut.setStreamName("nn")
nn.out.link(nnOut.input)

q_list = []

def frameNorm(frame, bbox):
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


def displayFrame(name, frame, detections):
    for detection in detections:
        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
        cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
        cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
    cv2.imshow(name, frame)

# MobilenetSSD label texts
labelMap = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]



# https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack
with contextlib.ExitStack() as stack:
    for device_info in dai.Device.getAllAvailableDevices():
        device = stack.enter_context(dai.Device(pipeline, device_info))
        print("Connected to " + device_info.getMxId())
        device.startPipeline()
        # Output queue will be used to get the rgb frames from the output defined above
        q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        q_det = device.getOutputQueue(name="nn", maxSize=4, blocking=False)
        q_list.append((q_rgb, q_det))
#test
    while True:

        for i, (q_rgb, q_det) in enumerate(q_list):
            in_rgb = q_rgb.get()
            in_det = q_det.tryGet()
            rgb_frame = in_rgb.getCvFrame()
            detections = []
            if in_det is not None:
                detections = in_det.detections
            displayFrame("rgb-" + str(i + 1), rgb_frame, detections)

        if cv2.waitKey(1) == ord('q'):
            break