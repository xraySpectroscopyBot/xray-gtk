#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from configparser import ConfigParser
import serial
from serial.tools.list_ports import comports
import json
import time
import os

path = os.path.dirname(os.path.abspath(__file__))

config = ConfigParser()
config.read(path + "/spektrum.ini")

counts = []
times = {"start" : 0}
parameters = {"stepsperangle" : -1, "stepsize" : -1, "stepangle" : -1.0, "time" : -1, "startangle" : -1, "startsteps" : -1, "endangle" :-1, "measurementstotal" : -1}

ser = serial.Serial()
ser.baudrate = 9600
ser.timeout = 1
ser.write_timeout = 1

class GtkSignalHandlers:
	def onQuit(self, *a, **kv):
		with open(path + "/spektrum.ini", "w") as configfile:
			config.write(configfile)
		if ser.is_open:
			ser.close()
		print ("Done")
		Gtk.main_quit()

	def onDraw(self, *a, **kv):
		if parameters["time"] != -1:
			if parameters["time"] - (time.time() - times["start"]) > 0:
				builder.get_object("TimeLabel").set_text(str(round(parameters["time"] - (time.time() - times["start"]), 1)))
			else:
				builder.get_object("TimeLabel").set_text("0")
		else:
			builder.get_object("TimeLabel").set_text("Zeit")

	def onSerialComboChanged(self, *a, **kv):
		try:
			serialid = combo.get_active()
			if ser.is_open:
				ser.close()
			ser.port = comports()[serialid].device
			ser.open()
			ser.write(b'{"command":"position"}')
			time.sleep(0.5)
			if ser.readline() == b'':
				builder.get_object("ButtonOk0").set_sensitive(True)
				#updateSerialPorts()
			else:
				config["Serial"] = {"vid": str(comports()[serialid].vid), "pid": str(comports()[serialid].pid)}
				builder.get_object("ButtonOk0").set_sensitive(True)
		except serial.SerialException:
			builder.get_object("ButtonOk0").set_sensitive(False)
			#updateSerialPorts()

	def onAngleEntryChanged(self, *a, **kv):
		try:
			int(builder.get_object("AngleEntry").get_text())
			builder.get_object("ButtonOk3").set_sensitive(True)
		except ValueError:
			builder.get_object("ButtonOk3").set_sensitive(False)

	def onParameterEntryChanged(self, *a, **kv):
		try:
			parameters["stepangle"] = float(builder.get_object("StepsizeEntry").get_text())
			parameters["time"] = int(builder.get_object("TimeEntry").get_text())
			parameters["startangle"] = int(builder.get_object("StartStepsEntry").get_text())
			parameters["endangle"] = int(builder.get_object("EndStepsEntry").get_text())

			if parameters["startangle"] >= 0 and parameters["endangle"] >= parameters["startangle"] and parameters["endangle"] <= int(config["Stepper"]["angle"]) and parameters["stepangle"] > 0 and parameters["stepangle"] <= parameters["endangle"] and parameters["time"] > 0:
				parameters["stepsperangle"] = abs(int(config["Stepper"]["maximum"]) - int(config["Stepper"]["minimum"])) // int(config["Stepper"]["angle"])
				parameters["stepsize"] = parameters["stepsperangle"] * parameters["stepangle"]
				parameters["startsteps"] = parameters["stepsperangle"] * parameters["startangle"]
				endsteps = parameters["stepsperangle"] * parameters["endangle"]
				stepstotal = abs(endsteps - parameters["startsteps"])
				parameters["measurementstotal"] = stepstotal // parameters["stepsize"]
				timetotal = parameters["measurementstotal"] * parameters["time"]
				config["Parameters"] = {"stepangle": str(parameters["stepangle"]), "time": str(parameters["time"]), "startangle": str(parameters["startangle"]), "endangle": str(parameters["endangle"])}
				builder.get_object("NumberLabel").set_text("Messungen: " + str(parameters["measurementstotal"]))
				builder.get_object("TimeEstimatedLabel").set_text("Zeit: " + str(timetotal) + "s")
				builder.get_object("ButtonOk4").set_sensitive(True)
			else:
				builder.get_object("ButtonOk4").set_sensitive(False)
		except ValueError:
			builder.get_object("ButtonOk4").set_sensitive(False)

	def onIntensityEntryChanged(self, *a, **kv):
		try:
			int(builder.get_object("IntensityEntry").get_text())
			builder.get_object("ButtonOk5").set_sensitive(True)
		except ValueError:
			builder.get_object("ButtonOk5").set_sensitive(False)

	def onButtonTimer(self, *a, **kv):
		times["start"] = time.time()

	def onButtonUpFast(self, *a, **kv):
		ser.write(b'{"command":"move", "direction":"up", "velocity":"1000"}')
	def onButtonUpSlow(self, *a, **kv):
		ser.write(b'{"command":"move", "direction":"up", "velocity":"4000"}')
	def onButtonDownSlow(self, *a, **kv):
		ser.write(b'{"command":"move", "direction":"down", "velocity":"4000"}')
	def onButtonDownFast(self, *a, **kv):
		ser.write(b'{"command":"move", "direction":"down", "velocity":"1000"}')

	def onButtonMoveReleased(self, *a, **kv):
		ser.write(b'{"command":"stop"}')

	def onButtonOk0(self, *a, **kv):
		stack.set_visible_child(builder.get_object("Fixed1"))
	def onButtonOk1(self, *a, **kv):
		stack.set_visible_child(builder.get_object("Fixed2"))
	def onButtonOk2(self, *a, **kv):
		ser.write(b'{"command":"position"}')
		data = json.loads(ser.readline().decode("utf-8"))
		try:
			config["Stepper"]["minimum"] = str(data["position"])		
			config["Stepper"]["maximum"]
			stack.set_visible_child(builder.get_object("Fixed4"))
		except KeyError:
			config["Stepper"] = {}
			config["Stepper"]["minimum"] = str(data["position"])	
			stack.set_visible_child(builder.get_object("Fixed3"))
	def onButtonOk3(self, *a, **kv):
		ser.write(b'{"command":"position"}')
		data = json.loads(ser.readline().decode("utf-8"))
		config["Stepper"]["maximum"] = str(data["position"])	
		config["Stepper"]["angle"] = builder.get_object("AngleEntry").get_text()
		ser.write(b'{"command":"position"}')
		data = json.loads(ser.readline().decode("utf-8"))
		cmd = '{"command":"goto", "steps": "' + str(int(config["Stepper"]["minimum"]) - int(config["Stepper"]["maximum"])) + '", "velocity":"2000"}'
		ser.write(cmd.encode("utf-8"))
		stack.set_visible_child(builder.get_object("Fixed4"))
	def onButtonOk4(self, *a, **kv):
		stack.set_visible_child(builder.get_object("Fixed5"))
	def onButtonOk5(self, *a, **kv):
		if len(counts) == 0:
			counts.append(int(builder.get_object("IntensityEntry").get_text()))
			builder.get_object("IntensityEntry").set_text("")
			cmd = '{"command":"goto", "steps": "' + str(-parameters["startsteps"]) + '", "velocity":"2000"}'
			ser.write(cmd.encode("utf-8"))
			stack.set_visible_child(builder.get_object("Fixed6"))
			builder.get_object("MeasureLabel").set_text("Messung durchführen.")
		elif len(counts) < parameters["measurementstotal"]:
			cmd = '{"command":"goto", "steps": "' + str(-parameters["stepsize"]) + '", "velocity":"2000"}'
			ser.write(cmd.encode("utf-8"))
			counts.append(int(builder.get_object("IntensityEntry").get_text()))
			builder.get_object("IntensityEntry").set_text("")
		else:
			counts.append(int(builder.get_object("IntensityEntry").get_text()))
			builder.get_object("IntensityEntry").set_text("")
			ser.write(b'{"command":"position"}')
			data = json.loads(ser.readline().decode("utf-8"))
			cmd = '{"command":"goto", "steps": "' + str(-data["position"]) + '", "velocity":"2000"}'
			ser.write(cmd.encode("utf-8"))

			stack.set_visible_child(builder.get_object("Fixed7"))

			GtkSignalHandlers.onSave(window)
			
	def onButtonOk6(self, *a, **kv):
		stack.set_visible_child(builder.get_object("Fixed5"))

	def onSave(self, *a, **kv):
		dialog = Gtk.FileChooserDialog("Messwerte speichern", window, Gtk.FileChooserAction.SAVE, ("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK))
		dialog.set_do_overwrite_confirmation(True)
		dialog.set_current_name("Messwerte")

		filter_dat = Gtk.FileFilter()
		filter_dat.set_name("Alle .dat dateien")
		filter_dat.add_pattern("*.dat")
		dialog.add_filter(filter_dat)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("Alle Dateien")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)

		dialog.set_filter(filter_any)

		filepath = ""

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			if dialog.get_filename()[-4:] == ".dat":
				filepath = dialog.get_filename()
			else:
				filepath = dialog.get_filename() + ".dat"
			savefile = ConfigParser()
			savefile.read(filepath)
			savefile["Parameters"] = {}
			savefile["Parameters"]["stepsize"] = str(parameters["stepsize"])
			savefile["Parameters"]["time"] = str(parameters["time"])
			savefile["Parameters"]["startsteps"] = str(parameters["startsteps"])
			savefile["Parameters"]["stepsperangle"] = str(parameters["stepsperangle"])
			savefile["Parameters"]["d"] = str(2.01*10**-10)
			savefile["Data"] = {}
			savefile["Data"]["counts"] = str(counts)
			with open(filepath, "w") as save:
				savefile.write(save)
		elif response == Gtk.ResponseType.CANCEL:
			pass

		dialog.destroy()

def updateSerialPorts():
	combo.remove_all()
	for port in comports():
		combo.append_text(port.name)

builder = Gtk.Builder()
builder.add_from_file(path + "/spektrum.glade")
builder.connect_signals(GtkSignalHandlers)
window = builder.get_object("MainWindow");
stack = builder.get_object("MainStack")
combo = builder.get_object("SerialCombo")

updateSerialPorts()

'''try:
	try:
		i = 0
		while True:
			if str(comports()[i].vid) == str(config["Serial"]["vid"]) and str(comports()[i].pid) == str(config["Serial"]["pid"]):
				try:
					ser.port = comports()[i].device
					ser.open()
					ser.write(b'{"command":"position"}')
					if ser.readline() == b'':
						stack.set_visible_child(builder.get_object("Fixed0"))
					else:
						stack.set_visible_child(builder.get_object("Fixed1"))
				except serial.SerialException:
					stack.set_visible_child(builder.get_object("Fixed0"))
				break
			i = i + 1
	except IndexError:
		stack.set_visible_child(builder.get_object("Fixed0"))
except KeyError:
	stack.set_visible_child(builder.get_object("Fixed0"))'''

try:
	ser.port = "/dev/ttyAMA0"
	ser.open()
	stack.set_visible_child(builder.get_object("Fixed1"))

	try:
		builder.get_object("StepsizeEntry").set_text(config["Parameters"]["stepangle"])
		builder.get_object("TimeEntry").set_text(config["Parameters"]["time"])
		builder.get_object("StartStepsEntry").set_text(config["Parameters"]["startangle"])
		builder.get_object("EndStepsEntry").set_text(config["Parameters"]["endangle"])
	except KeyError:
		pass

	window.show_all()
	Gtk.main()
except serial.SerialException:
	print ("No Serial port found!")
	Gtk.main_quit()
