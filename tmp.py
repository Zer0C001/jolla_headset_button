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
	def must_reset_command_string_on(self,command_dict={}):
		retval=False
		if ( not command_dict.has_key('command_string') ) or ( self.max_command_string_len<=len(command_dict['command_string']) ) :
			retval=True
		return retval
	def do_command(self,command_dict={}):
		if command_dict.has_key('command_string') and len(command_dict['command_string'])>0:
			command_str=command_dict['command_string']
		else:
			if self.debug:
				print 'no command string'
			return False
		if self.debug:
			print 'processing: '+command_str
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
	     		else:
	     			return False
		pass
		
		

class JollaHeadsetButtonD(Daemon):
	def __init__(self,button_handler_class=JollaHeadsetButtonHandler,debug=False,pidfile="/var/run/jolla_headset_button_d.pid",*args,**kwargs):
		super(JollaHeadsetButtonD,self).__init__(pidfile=pidfile,*args,**kwargs)
		self.debug=debug
		self.buttonhandler=button_handler_class(debug=self.debug)
	def run(self):
			max_presses=self.buttonhandler.get_max_command_string_len()-1
			press_num_inc_time=1.5
			long_press_duration=1.0
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
			commands_dict_list=[]
			while event:
			    (tv_sec, tv_usec, event_type, code, value) = struct.unpack(FORMAT, event)
			    fl_sec=tv_sec+float(0.000001*tv_usec)
			    if event_type != 0 or code != 0 or value != 0:
			        this_entry=None
			        this_entry_already_in_list=False
			        for entry in commands_dict_list:
			        		if entry['event_type']==event_type and entry['code']==code:
			        			this_entry=entry
			        			this_entry_already_in_list=True
			        if this_entry==None:
			        		this_entry={'event_type':event_type, 'code':code, 'current_value':value, 'current_time':fl_sec, 'command_string':''}
			        		commands_dict_list.append(this_entry)
			        this_entry_index=commands_dict_list.index(this_entry)
			        
			        
			        if this_entry_already_in_list:
			        		commands_dict_list[this_entry_index].update({ 'last_time':this_entry['current_time'], 'last_value':this_entry['current_value'], 'current_value':value, 'current_time':fl_sec })
			        		this_entry=commands_dict_list[this_entry_index]
			        		
			        			
			        if ( this_entry.has_key('last_time') and value==1 and this_entry['current_time']-this_entry['last_time']>press_num_inc_time )  or  ( this_entry.has_key('last_value') and this_entry['last_value']==value ) :
			        		this_entry['command_string']=''
			        		
			        elif this_entry.has_key('last_time') and value==0 and this_entry.has_key('last_value') and this_entry['last_value']==1:
			        		if self.buttonhandler.must_reset_command_string_on(this_entry):
			        			if self.debug:
			        				print 'clear command string because of buttonhandler'
			        			this_entry['command_string']=''
			        		if this_entry['current_time']-this_entry['last_time']>max_press_duration:
			        			if self.debug:
			        				print 'clear debug string because of max_press_duration'
			        			this_entry['command_string']=''
			        		elif this_entry['current_time']-this_entry['last_time']>long_press_duration:
			        			this_entry['command_string']+='l'
			        		else:
			        			this_entry['command_string']+='s'
			        		if len(this_entry['command_string'])>0:
			        			self.buttonhandler.do_command(this_entry)


			        if self.debug:
			        		print commands_dict_list
			        		print this_entry
			        		print this_entry_index
			        		if this_entry.has_key('last_time'):
			        			print this_entry['current_time']-this_entry['last_time']
			        		print "\n\n"
			   #else:
			        # Events with code, type and value == 0 are "separator" events
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