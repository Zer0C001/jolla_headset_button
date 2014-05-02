TODO:
=======

1) fix music managment: 

	separate music managment class
	use the dbus MPRIS spec

2) demonize and add startup script

3) separate click processing from detection

4) add install instructions

5) package and upload to openrepos.net ?


USAGE:
======

1) You need to have python and dbus-python installed.

2) Patch /usr/lib/qt5/qml/com/jolla/mediaplayer/AudioPlayer.qml using audioplayer_dbus.patch.

3) run tmp.py and leave it runnig

4) 1 press will hangup an active call, answer an incomming one or pause/play the music player ( only jolla-mediaplayer ). 2 presses skip to the next song. 3 presses go to the previous song.
