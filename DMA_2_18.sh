#!/bin/bash


gst-launch-1.0 uridecodebin uri=file:///home/mashroom/Downloads/sintel_SD.mp4 ! queue ! videomixer name=vmix sink_0::alpha=0.7 sink_1::alpha=0.5 ! agingtv ! tee name=t t.src_0 ! queue ! autovideosink uridecodebin uri=file:///home/mashroom/Downloads/sita_SD.mp4 ! queue ! vmix. t.src_1 ! queue ! videoconvert ! x264enc tune=zerolatency ! matroskamux ! queue ! filesink location=mixedvid.mkv

