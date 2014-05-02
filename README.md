TODO:
=======

1) demonize and add startup script

2) separate click processing from detection

3) add install instructions

4) package and upload to openrepos.net ?


USAGE:
======

1) You need to have python and dbus-python installed.

2) Patch /usr/lib/qt5/qml/com/jolla/mediaplayer/AudioPlayer.qml using audioplayer_dbus.patch, to make the stock jolla-mediaplayer MPRIS compatible ( http://specifications.freedesktop.org/mpris-spec/latest/ ). 

3) run tmp.py and leave it runnig

4) 1 press will hangup an active call, answer an incomming one or pause/play the music player ( only for MPRIS compatible players ). 2 presses skip to the next song. 3 presses go to the previous song.
