#!/usr/bin/python
import simple_daemon
import dbus
import re
import struct
import time
import sys
import io
import shlex,subprocess


class Modems_Handler():
	def __init__(self,debug=False):
		self.debug=debug
		sys_bus=dbus.SystemBus()
		ofono_proxy=sys_bus.get_object("org.ofono","/")
		iface = dbus.Interface(ofono_proxy, 'org.ofono.Manager')
		modem_names=[]
		for modem in iface.GetModems():
			modem_names.append(str(modem[0]))
		self.sys_bus=sys_bus
		self.modems=modem_names
		if self.debug:
			print 'found modem(s): '+str(self.modems)
	
	def do_click(self):
		calls=[]
		for modem in self.modems:
		  modem_proxy=self.sys_bus.get_object("org.ofono",modem)
		  voicecallmanager=dbus.Interface(modem_proxy,"org.ofono.VoiceCallManager")
		  for call in voicecallmanager.GetCalls():
		    if str(call[1]['State'])=='active':
		    	if self.debug :
		    		print('hup: '+str(call[0]))
		    	self.hup(call[0])
		    	return(True)
		    else:
		      calls.append(call)
		if len(calls)>0 :
			if self.debug:
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
		
class MediaPlayerControl():
	def __init__(self,debug=False):
		self.debug=debug
		ses_bus=dbus.SessionBus()
		if self.debug:
			print 'init MediaPlayerControl'
		players=[]
		self.player=None
		for item in ses_bus.list_names():
		    if re.match('org.mpris.MediaPlayer2',item):
		      players.append(item)
		if self.debug:
			print(players)
		if len(players)>0:
			player=dbus.Interface(ses_bus.get_object(players[0],"/org/mpris/MediaPlayer2"),'org.mpris.MediaPlayer2.Player')
			if self.debug:
				print player
			self.player=player
			
	def toggle_pause(self):
		try:
			self.player.PlayPause()
		except:
			if self.debug:
				print 'err'
			pass
	
	def next(self):
		try:
			self.player.Next()
		except:
			if self.debug:
				print 'err'
			pass
	
	def prev(self):
		try:
			self.player.Previous()
		except:
			if self.debug:
				print 'err'
			pass

	def prev2(self):
		self.prev()
		self.prev()

		
class mytest():
	def __init__(self,debug=False):
		self.debug=debug
		self.modems=Modems_Handler(debug=self.debug)
		self.mediaplayer=None
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
			        if value==1 and fl_diff<=press_time and press_num<max_presses:
			        		press_num+=1
			        elif value==1:
			        		press_num=0
			        if value==1 and not self.modems.do_click():
			        		if self.debug:
			        			print("pressed, press_num: "+str(press_num)+" , fl_diff: "+str(fl_diff))
			        		if press_num==0:
			        			self.mediaplayer=MediaPlayerControl(debug=self.debug)
			        			if self.debug:
			        				print self.mediaplayer
			        			self.mediaplayer.toggle_pause()
			        		elif press_num==1:
			        			self.mediaplayer.next()
			        		elif press_num==2:
			        			self.mediaplayer.prev2()

			        if value==0:
			        		if self.debug:
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
			
mt=mytest(debug=True)
mt.run()
