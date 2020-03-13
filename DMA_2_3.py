#!/usr/bin/env python3
# -*- coding: UTF-8 -*
import sys
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, Gtk, GLib, GdkX11, GstVideo

# http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+5%3A+GUI+toolkit+integration

# Define the hard coded file paths
SOURCE_0 = "/home/mashroom/Downloads/sita_SD.mp4"
SOURCE_1 = "/home/mashroom/Downloads/sintel_SD.mp4"
OUTPUT = "output.mkv"


class Player(object):

    def __init__(self):
        # initialize GTK
        Gtk.init(sys.argv)

        # initialize GStreamer
        Gst.init(sys.argv)

        self.state = Gst.State.NULL
        self.duration = Gst.CLOCK_TIME_NONE

        self.pipeline = Gst.parse_launch(
            "uridecodebin name=uridecodebin0 uri=file://{} ! queue ! videoscale ! "
            "video/x-raw, width=640, height=480 ! queue ! "
            "videomixer name=vmix sink_0::alpha=1.0 sink_1::alpha=0.5 ! warptv name=warp !"
            " agingtv name=agtv ! gdkpixbufoverlay name=logo location=logo.png offset-x=20" 
            " offset-y=20 overlay-height=80 overlay-width=80 ! tee name=t t.src_0 ! queue ! "
            "gtksink name=sink uridecodebin name=uridecodebin1 uri=file://{} ! "
            "queue ! videoscale ! video/x-raw, width=640, height=480 ! queue ! "
            "vmix. t.src_1 ! queue ! videoconvert ! x264enc tune=zerolatency ! "
            "matroskamux ! queue ! filesink location={}"
                .format(SOURCE_0, SOURCE_1, OUTPUT))

        self.sink_1 = self.pipeline.get_by_name("vmix").get_static_pad('sink_1')
        self.sink_1.set_property("alpha", 0.0)

        agingfilter = self.pipeline.get_by_name("agtv")
        agingfilter.set_passthrough(True)
        warpfilter = self.pipeline.get_by_name("warp")
        warpfilter.set_passthrough(True)
        logofilter = self.pipeline.get_by_name("logo")
        logofilter.set_property("alpha", 0.0)
        # create the GUI
        self.build_ui()

        # instruct the bus to emit signals for each received message
        # and connect to the interesting signals
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self.on_error)
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::state-changed", self.on_state_changed)

    # set the playbin to PLAYING (start playback), register refresh callback
    # and start the GTK main loop
    def start(self):
        # start playing
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("ERROR: Unable to set the pipeline to the playing state")
            sys.exit(1)
        # start the GTK main loop. we will not regain control until
        # Gtk.main_quit() is called
        Gtk.main()

        # free resources
        self.cleanup()

    # set the playbin state to NULL and remove the reference to it
    def cleanup(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

    def build_ui(self):
        main_window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        main_window.connect("delete-event", self.on_delete_event)

        self.slider = Gtk.HScale.new_with_range(0, 1, .01)
        self.slider.set_draw_value(True)
        self.slider_update_signal_id = self.slider.connect(
            "value-changed", self.on_slider_changed)

        self.logo_button = Gtk.Button.new_with_label("Overlay logo     ")
        self.logo_button.connect("clicked", self.on_logo_effect)
        self.aging_button = Gtk.Button.new_with_label("Add aging filter     ")
        self.aging_button.connect("clicked", self.on_aging_effect)
        self.warp_button = Gtk.Button.new_with_label("Add warp filter     ")
        self.warp_button.connect("clicked", self.on_warp_effect)    


        controls = Gtk.HBox.new(False, 0)
        controls.pack_start(self.logo_button, True, True, 2)
        controls.pack_start(self.aging_button, True, True, 2)
        controls.pack_start(self.warp_button, True, True, 2)
        slidebox = Gtk.VBox.new(False, 0)
        slidebox.pack_start(self.slider, True, True, 0)
        slidebox.pack_start(controls, True, True, 0)
        main_hbox = Gtk.VBox.new(False, 0)
        main_hbox.pack_start(self.pipeline.get_by_name("sink").props.widget, True, True, 0)
        main_hbox.pack_start(slidebox, False, False, 2)

        main_window.add(main_hbox)
        main_window.set_default_size(640, 480)
        main_window.show_all()


    def on_warp_effect(self, button):
        warpfilter = self.pipeline.get_by_name("warp")
        if button.get_label() == "Add warp filter ✓":
            warpfilter.set_passthrough(True)
            button.set_label("Add warp filter     ")
        else:
            warpfilter.set_passthrough(False)
            button.set_label("Add warp filter ✓")


    def on_aging_effect(self, button):
        agingfilter = self.pipeline.get_by_name("agtv")
        if button.get_label() == "Add aging filter ✓":
            agingfilter.set_passthrough(True)
            button.set_label("Add aging filter     ")
        else:
            agingfilter.set_passthrough(False)
            button.set_label("Add aging filter ✓")

    def on_logo_effect(self, button):
        logofilter = self.pipeline.get_by_name("logo")
        if button.get_label() == "Overlay logo ✓":
            logofilter.set_property("alpha", 0.0)
            button.set_label("Overlay logo     ")
        else:
            logofilter.set_property("alpha", 1.0)
            button.set_label("Overlay logo ✓")
        


    # this function is called when the main window is closed
    def on_delete_event(self, widget, event):
        self.pipeline.set_state(Gst.State.READY)
        Gtk.main_quit()

    # this function is called every time the video window needs to be
    # redrawn. GStreamer takes care of this in the PAUSED and PLAYING states.
    # in the other states we simply draw a black rectangle to avoid
    # any garbage showing up
    def on_draw(self, widget, cr):
        if self.state < Gst.State.PAUSED:
            allocation = widget.get_allocation()

            cr.set_source_rgb(0, 0, 0)
            cr.rectangle(0, 0, allocation.width, allocation.height)
            cr.fill()

        return False

    # this function is called when the slider changes its position.
    # we perform a seek to the new position here
    def on_slider_changed(self, range):
        value = self.slider.get_value()
        self.sink_1.set_property("alpha", value)

    # this function is called when an error message is posted on the bus
    def on_error(self, bus, msg):
        err, dbg = msg.parse_error()
        print("ERROR:", msg.src.get_name(), ":", err.message)
        if dbg:
            print("Debug info:", dbg)

    # this function is called when an End-Of-Stream message is posted on the bus
    # we just set the pipeline to READY (which stops playback)
    def on_eos(self, bus, msg):
        print("End-Of-Stream reached")
        self.pipeline.set_state(Gst.State.READY)

    # this function is called when the pipeline changes states.
    # we use it to keep track of the current state
    def on_state_changed(self, bus, msg):
        old, new, pending = msg.parse_state_changed()
        if not msg.src == self.pipeline:
            # not from the playbin, ignore
            return

        self.state = new
        print("State changed from {0} to {1}".format(
            Gst.Element.state_get_name(old), Gst.Element.state_get_name(new)))


if __name__ == '__main__':
    p = Player()
    p.start()

