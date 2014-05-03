#!/usr/bin/python
from simple_daemon import Daemon
## simple_daemon from https://pypi.python.org/pypi/simple_daemon
import dbus
import re
import struct
import time
import sys
import io



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
		  calls=self.get_calls()
		  for call in calls:
		    if str(call['State'])=='active' or str(call['State'])=="alerting" or str(call['State'])=="dialing":
		    	if self.debug :
		    		print('hup: '+str(call['call']))
		    	self.hup(call['call'])
		    	return(True)
		  if len(calls)>0 :
			if self.debug:
				print('Answer : '+str(calls[0]['call']))
			self.answer(calls[0]['call'])
			return(True)
		  else:
			return(False)
			
	def get_calls(self):
		calls=[]
		for modem in self.modems:
		  modem_proxy=self.sys_bus.get_object("org.ofono",modem)
		  voicecallmanager=dbus.Interface(modem_proxy,"org.ofono.VoiceCallManager")
		  for call in voicecallmanager.GetCalls():
		  		calls.append({'call':call[0],'State':call[1]['State']})
		if self.debug:
			print calls
		return calls		  		
	
	def answer(self,call):
		try:
			call_proxy=self.sys_bus.get_object("org.ofono",call)
			dbus.Interface(call_proxy,'org.ofono.VoiceCall').Answer()
		except:
			# Error answering ? Let's try HUP 
			if self.debug:
					print 'err ans'  
			try:
				self.hup(call)
			except Exception as e:
				if self.debug:
					print 'err hup outgoing: '+str(e)				
				pass
		
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

		
class JollaHeadsetButtonHandler():
	def __init__(self,debug=False):
		self.max_command_string_len=3
		self.debug=debug
		self.modems=Modems_Handler(debug=self.debug)
		self.mediaplayer=None
		pass
	def get_max_command_string_len(self):
		return self.max_command_string_len
	def do_command(self,command_str=''):
		if self.debug:
			print 'processing: '+command_str
		if len(command_str)<1:
			return False
		press_num=len(command_str)-1
		if not self.modems.do_click():
	     		if press_num==0:
	     			self.mediaplayer=MediaPlayerControl(debug=self.debug)
	     			if self.debug:
	     				print "do toggle_pause"
	     				print self.mediaplayer
	     			self.mediaplayer.toggle_pause()
	     		elif press_num==1:
	     			if self.debug:
	     				print "do next"
	     			self.mediaplayer.next()
	     		elif press_num==2:
	     			if self.debug:
	     				print "do prev2"
	     			self.mediaplayer.prev2()
		pass
		
		

class JollaHeadsetButtonD(Daemon):
	def __init__(self,button_handler_class=JollaHeadsetButtonHandler,debug=False,pidfile="/var/run/jolla_headset_button_d.pid",*args,**kwargs):
		super(JollaHeadsetButtonD,self).__init__(pidfile=pidfile,*args,**kwargs)
		self.debug=debug
		self.buttonhandler=button_handler_class(debug=self.debug)
	def run(self):
			max_presses=self.buttonhandler.get_max_command_string_len()-1
			press_num_inc_time=1.5
			long_press_duration=2.0
			max_press_duration=6.0
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
			reset_press_num=False
			l_tv_sec=0
			l_tv_usec=0
			l_fl_sec=0.0
			prev_value=0
			while event:
			    (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)
			    fl_sec=tv_sec+float(0.000001*tv_usec)
			    if type != 0 or code != 0 or value != 0:
			        fl_diff=fl_sec-l_fl_sec
			        if value==1 and fl_diff<=press_num_inc_time and press_num<max_presses and prev_value==0:
			        		if self.debug:
			        			print '\npress_num inc'
			        		press_num+=1
			        elif ( value==1 ) or reset_press_num:
			        		if self.debug:
			        			print '\n\npress_num clear'
			        		reset_press_num=False
			        		press_num=0
			        elif value==0 and fl_diff>max_press_duration:
			        		reset_press_num=True
			        if value==1:
			        		if self.debug:
			        			print("pressed, press_num: "+str(press_num)+" , fl_diff: "+str(fl_diff))
			        		pass

			        elif value==0:
			        		if self.debug:
			        			print("released, fl_diff: "+str(fl_diff)+"\n")
			        		if fl_diff<=max_press_duration:
			        			self.buttonhandler.do_command('s'*(press_num+1))

				l_tv_sec=tv_sec
				l_tv_usec=tv_usec
				l_fl_sec=fl_sec
				prev_value=value
			   #else:
			        # Events with code, type and value == 0 are "separator" events
			    #    print("===========================================")	
			    #time.sleep(0.5)
			    #s=in_file.peek(EVENT_SIZE)
			    #print("s"+s)
			    event = in_file.read(EVENT_SIZE)
			
			in_file.close()
			



jhsbd=JollaHeadsetButtonD()

if len(sys.argv)==1 or sys.argv[1]=="start":
  jhsbd.start()

elif sys.argv[1]=="debug":
	jhsbd=JollaHeadsetButtonD(debug=True)
	jhsbd.run()

elif sys.argv[1]=="stop":
  jhsbd.stop()

elif sys.argv[1]=="restart":
  jhsbd.restart()
else:
  print "unknown argument :"+sys.argv[1]