import cv2
import depthai

# Start defining a pipeline
pipeline = depthai.Pipeline()
found, front  = depthai.Device.getDeviceByMxId("14442C10A1E5CBD200")
found, frontR = depthai.Device.getDeviceByMxId("14442C10A1D109D100")
found, frontL = depthai.Device.getDeviceByMxId("14442C10C195A1D000")

# Define a source - color camera
camRgb = pipeline.createColorCamera()
camRgb.setPreviewSize(300, 300)
camRgb.setBoardSocket(depthai.CameraBoardSocket.RGB)
camRgb.setResolution(depthai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setInterleaved(False)
camRgb.setColorOrder(depthai.ColorCameraProperties.ColorOrder.RGB)

# Create output
xoutRgb = pipeline.createXLinkOut()
xoutRgb.setStreamName("rgb")
camRgb.preview.link(xoutRgb.input)

# Pipeline defined, now the device is connected to
with depthai.Device(pipeline, front) as device:
    # Start pipeline
    device.startPipeline()

    # Output queue will be used to get the rgb frames from the output defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

    while True:
        inRgb = qRgb.get()  # blocking call, will wait until a new data has arrived

        # Retrieve 'bgr' (opencv format) frame
        cv2.imshow("bgr", inRgb.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
with depthai.Device(pipeline, frontR) as device:
    # Start pipeline
    device.startPipeline()

    # Output queue will be used to get the rgb frames from the output defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

    while True:
        inRgb = qRgb.get()  # blocking call, will wait until a new data has arrived

        # Retrieve 'bgr' (opencv format) frame
        cv2.imshow("bgr", inRgb.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break
with depthai.Device(pipeline, frontL) as device:
    # Start pipeline
    device.startPipeline()

    # Output queue will be used to get the rgb frames from the output defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

    while True:
        inRgb = qRgb.get()  # blocking call, will wait until a new data has arrived

        # Retrieve 'bgr' (opencv format) frame
        cv2.imshow("bgr", inRgb.getCvFrame())

        if cv2.waitKey(1) == ord('q'):
            break