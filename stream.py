# This script can be run directly from a python Interpretter. 
# I am running it in Thonny (IDE already installed in the OS). 
# Shouldn't require any package installations to the best of my memory,
# but it does require running the following two commands:
# pip uninstall opencv-python
# pip install opencv-python-headless
# which fixes the following issue when trying to use opencv: 

# "qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in 
# "/home/user/.local/lib/python3.9/site-packages/cv2/qt/plugins" 
# even though it was found. This application failed to start because 
# no Qt platform plugin could be initialized. Reinstalling the application 
# may fix this problem."

# Investigate later: we had some confidence issues knowing that we were
# viewing the display in 2k resolution. Look into the hdmi_mode setting
# in the config.txt file. It should allow you to programmatically set the
# resolution of the display and even set a custom setting.

from picamera2 import MappedArray, Picamera2, Preview
import time
import cv2
import numpy as np
picam2 = Picamera2()
# Create a camera configuration (the preview_configuration) that sets default 
# values for the "main" stream which are conducive to displaying the camera feed.
# 
# It will be worth it to go back later and change some of the default configuration 
# settings to optimize for speed, such as the buffer count, queue, etc. 
# See https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf#page=69&zoom=100,153,176  
# and look for the section on increasing the CMA. Also read section 8.4 for other performance optimizations.
# Sets the configuration object returned above. Configuration settings are all of the 
# one-time settings that can't be changed at run time.
width = 1920
height = 1080
config = picam2.create_preview_configuration(main={"size": (width,height)}, display="main")
 
picam2.configure(config)

# Setting Analog Gain = 8 dB, ExposureTime = 16660, Frame Duration = 16666, and 
# other settings to default values results in roughly the same exposure as my eyes 
# for a fairly bright ambient environment.
#
# Frame Duration Limit must specify a minimum and maximum value. Not quite sure what 
# happens if you specify different values for min and max frameDurationLimits. I believe 
# it tries to operate at the fastest framerate possible. I'm guessing that if your 
# maximum FrameDuration (i.e. minimum FPS) is shorter than it can handle, it will just 
# drop frames or tradeoff something else as a consequence in order to maintain that minimum framerate.
#
# Setting NoiseReductionMode to 2 (high quality noise reduction method) may decrease the frame rate. 
# If this is the case, consider changing this to mode 1 (fast noise reduction)
# During initial testing, I set the ExposureTime to the maximum value possible for 60 FPS, and set 
# the range of FrameDurationLimits to (15000, 16700). It seems to be "happiest" operating at 16681, 
# so I changed the upper bound to that value instead, so that it can't operate much slower 
# than 60 fps. 15000 is an arbitrary lower bound that allows it to run faster than 60 FPS, even 
# though it probably can't (hardware limitation and the ExposureTime I set).
picam2.set_controls({"FrameDurationLimits": (15000,16682), 
                     "ExposureValue": 0.0, 
                     "NoiseReductionMode": 2, 
                     "ScalerCrop": (0,0,width,height), 
                     "Sharpness": 1.0, 
                     "AeEnable": False, "ExposureTime": 16660, 
                     "AnalogueGain": 8.0, "Contrast": 1.0, 
                     "Saturation": 1.0, "Brightness": 0.0})

prev_frame_time = 0
new_frame_time = 0
frame_counter = 0
fps_avg_window = 60
distCoeff = np.zeros((4,1),np.float64)
k1 = 5.0e-5;
k2 = 0.0
p1 = 0.0
p2 = 0.0
distCoeff[0,0] = k1
distCoeff[1,0] = k2
distCoeff[2,0] = p1
distCoeff[3,0] = p2
cam = np.eye(3,dtype=np.float32)  
cam[0,2] = width/2.0
cam[1,2] = height/2.0
cam[0,0] = 10.
cam[1,1] = 10.
R = np.eye(3, dtype=np.float32)
map1 = np.ndarray((height, width),dtype=np.single)
map2 = np.ndarray((height, width),dtype=np.single)
cv2.initUndistortRectifyMap(cam, distCoeff, None, None,(width,height), cv2.CV_32FC1, map1, map2)
interp = cv2.INTER_LINEAR
cpy = np.ndarray((height,width,4),dtype=np.uint8)

array_distorted = np.ndarray((height, width, 4), dtype=np.uint8)
image_width_cutoff = [int(width/4), int(width-width/4)]
def apply_barrel_distortion(request):
    # with MappedArray(request, "main") as m:
    global prev_frame_time, new_frame_time, frame_counter, distCoeff, map1, map2, interp, width, height, array_distorted, image_width_cutoff, cpy
        #width = m.array.shape[1]
        #height = m.array.shape[0]
        
        #Uncomment the two lines below and the m.array[:,:,:] = array_distorted... line to enable barrel distortion again
        #cv2.undistort(m.array, cam,distCoeff, array_distorted)
        #cv2.remap(m.array, map1, map2, interp, array_distorted)        

        #show framerate
        #colour = (0, 255, 0)
        #origin = (1200, 30)
        #font = cv2.FONT_HERSHEY_SIMPLEX
        #scale = 1
        # thickness = 2
    if frame_counter % fps_avg_window  == 0:
        prev_frame_time = new_frame_time
        new_frame_time = time.time()
        fps = str(int(1/(new_frame_time-prev_frame_time)*fps_avg_window))
        framerate = "FPS: " + fps
        print(framerate)
    frame_counter +=1
        
        # cv2.putText(m.array, framerate, origin, font, scale, colour, thickness)
        # cpy = np.ndarray.copy(m.array)
        # m.array[:,:,:] = array_distorted  #uncomment this line and comment the line below to return single image instead of split screen
        # m.array[:,:,:] = np.hstack((m.array[:,image_width_cutoff[0]:image_width_cutoff[1],:], m.array[:,image_width_cutoff[0]:image_width_cutoff[1],:]))
    return
       


picam2.pre_callback = apply_barrel_distortion

# You can run these two lines instead of picam2.start(show_preview=True) 
# if you want more control of the display settings
picam2.start_preview(Preview.QTGL, x=0, y=0, width=1920, height=1080)
picam2.start()

# picam2.start(show_preview=True)

# Specifying an array of title fields AFTER you start() makes these fields 
# appear and update in real time on the top window title bar.
picam2.title_fields = ["ExposureTime", "FrameDuration", "AnalogueGain", "DigitalGain"] 

# Sleep for the time we want the preview to remain open. 
# This is necessary since the picam2.start() statement is non-blocking.
time.sleep(60000) 


# Stop picam2 after we are done so connection is closed.
picam2.stop()

# This is how you would obtain and print a frame's metadata on a frame by frame basis. 
# This also lets you see all of the metadata contained in a frame, in case you'd like 
# to print out any of these values in real time at the top of the window using the 
# title_fields class member like is shown above.
# metadata = picam2.capture_metadata() 

# Use the capture_array function to manipulate frames in a loop (i.e. apply barrel distortion).
# array = picam2.capture_array("main")  
