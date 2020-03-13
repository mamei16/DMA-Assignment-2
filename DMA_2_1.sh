#!/bin/bash


gst-launch-1.0 uridecodebin uri=file:///home/dma/Downloads/sintel_SD.mp4 ! queue ! videoscale ! video/x-raw, width=640, height=480 ! queue ! videomixer name=vmix sink_0::alpha=1.0 sink_1::alpha=0.5 ! agingtv ! tee name=t t.src_0 ! queue max-size-buffers=12800 max-size-bytes=640000000 max-size-time=64000000000 ! autovideosink uridecodebin uri=file:///home/dma/Downloads/sita_SD.mp4 ! queue ! videoscale ! video/x-raw, width=640, height=480 ! queue ! vmix. t.src_1 ! queue ! videoconvert ! x264enc threads=4 ! matroskamux ! queue ! filesink location=mixedvid.mkv
