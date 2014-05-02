#!/usr/bin/python
import simple_daemon
import dbus
import struct
import time
import sys
import io
import shlex,subprocess


class Modems_Handler():
	def __init__(self):
		sys_bus=dbus.SystemBus()
		ofono_proxy=sys_bus.get_object("org.ofono","/")
		iface = dbus.Interface(ofono_proxy, 'org.ofono.Manager')
		modem_names=[]
		for modem in iface.GetModems():
			modem_names.append(str(modem[0]))
		self.sys_bus=sys_bus
		self.modems=modem_names
	
	def do_click(self):
		calls=[]
		for modem in self.modems:
		  modem_proxy=self.sys_bus.get_object("org.ofono",modem)
		  voicecallmanager=dbus.Interface(modem_proxy,"org.ofono.VoiceCallManager")
		  for call in voicecallmanager.GetCalls():
		    if str(call[1]['State'])=='active':
		      print('hup: '+str(call[0]))
		      self.hup(call[0])
		      return(True)
		    else:
		      calls.append(call)
		if len(calls)>0 :
			print('Answer : '+str(calls[0][0]))
			self.answer(calls[0][0])
			return(True)
		else:
			return(False)
	
	def answer(self,call):
		call_proxy=self.sys_bus.get_object("org.ofono",call)
		dbus.Interface(call_proxy,'org.ofono.VoiceCall').Answer()
		
	def hup(self,call):
		call_proxy=self.sys_bus.get_object("org.ofono",call)
		dbus.Interface(call_proxy,'org.ofono.VoiceCall').Hangup()

		
class mytest():
	def __init__(self):
		self.modems=Modems_Handler()
		pass
	def run(self):
			max_presses=2
			press_time=1.5
			infile_path = "/dev/input/by-path/platform-soc-audio.0-event-headset-button"
			#
			#long int, long int, unsigned short, unsigned short, unsigned int
			#
			FORMAT = 'llHHI'
			EVENT_SIZE = struct.calcsize(FORMAT)
			
			#open file in binary mode
			in_file = io.open(infile_path, "rb",EVENT_SIZE)
			
			event = in_file.read(EVENT_SIZE)
			press_num=0
			l_tv_sec=0
			l_tv_usec=0
			l_fl_sec=0.0
			while event:
			    (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)
			    fl_sec=tv_sec+float(0.000001*tv_usec)
			    if type != 0 or code != 0 or value != 0:
			        fl_diff=fl_sec-l_fl_sec
			        #print("Event type %u, code %u, value: %u at %d s, %d us ; diff %d s %d us   " % (type, code, value, tv_sec, tv_usec,tv_sec-l_tv_sec,tv_usec-l_tv_usec)+"float: "+str(fl_sec)+" diff: "+str(fl_diff))
			        if value==1 and fl_diff<=press_time and press_num<max_presses:
			        		press_num+=1
			        elif value==1:
			        		press_num=0
			        if value==1 and not self.modems.do_click():
			        		print("pressed, press_num: "+str(press_num)+" , fl_diff: "+str(fl_diff))
			        		if press_num==0:
			        			subprocess.call(shlex.split("dbus-send --session --type=method_call --dest=com.jolla.mediaplayer.remotecontrol /com/jolla/mediaplayer/remotecontrol com.jolla.mediaplayer.remotecontrol.executeCommand string:\"toggle_pause\""))
			        		elif press_num==1:
			        			subprocess.call(shlex.split("dbus-send --session --type=method_call --dest=com.jolla.mediaplayer.remotecontrol /com/jolla/mediaplayer/remotecontrol com.jolla.mediaplayer.remotecontrol.executeCommand string:\"next\""))
			        		elif press_num==2:
			        			subprocess.call(shlex.split("dbus-send --session --type=method_call --dest=com.jolla.mediaplayer.remotecontrol /com/jolla/mediaplayer/remotecontrol com.jolla.mediaplayer.remotecontrol.executeCommand string:\"prev\""))
			        			subprocess.call(shlex.split("dbus-send --session --type=method_call --dest=com.jolla.mediaplayer.remotecontrol /com/jolla/mediaplayer/remotecontrol com.jolla.mediaplayer.remotecontrol.executeCommand string:\"prev\""))
			        if value==0:
			        		print("released, fl_diff: "+str(fl_diff)+"\n")
				l_tv_sec=tv_sec
				l_tv_usec=tv_usec
				l_fl_sec=fl_sec
			   #else:
			        # Events with code, type and value == 0 are "separator" events
			    #    print("===========================================")	
			    #time.sleep(0.5)
			    #s=in_file.peek(EVENT_SIZE)
			    #print("s"+s)
			    event = in_file.read(EVENT_SIZE)
			
			in_file.close()
			
mt=mytest()
mt.run()
