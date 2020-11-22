import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import math

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')

try:
  import dbus 
except Exception as e:
   line1 = 'Missing DBUS dependeny. Please install python-dbus on your distro' 
   xbmc.executebuiltin('Notification(%s, %s, 5000, %s)'%(__addonname__,line1, __icon__))
   sys.exit(1)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


__settings__ = xbmcaddon.Addon(id="plugin.program.mount.usb")
addon_icon = 'special://home/addons/plugin.program.mount.usb/icon.png'


mode = args.get('mode', None)
currdisk = args.get('device', None)
# import web_pdb; web_pdb.set_trace() 

if currdisk:
    currdisk = currdisk[0]


def load_drive():


    bus = dbus.SystemBus()
    ud_manager_obj = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
    om = dbus.Interface(ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')


    try:
        # import web_pdb; web_pdb.set_trace()
        for k,v in om.GetManagedObjects().iteritems():

            drive_info = v.get('org.freedesktop.UDisks2.Block', {})

            if drive_info.get('IdUsage') == "filesystem" and drive_info.get('HintAuto'):
                device = drive_info.get('Device')
                          
                label = drive_info.get('IdLabel')
                
                device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                if not label:
                    size = int(drive_info.get('Size'))
                    label = '%s %s'%(convert_size(size), device)
                if 'mmcblk' not in device: 
                    disk = '/org/freedesktop/UDisks2/block_devices%s'%device[4:]
                    bd = bus.get_object('org.freedesktop.UDisks2', disk)
                
                    file_system = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
                    mountpoint = ''

                    if file_system:
                       file_system = bytearray(file_system[0]).replace(b'\x00', b'').decode('utf-8')
                       mountpoint = file_system

                    if mountpoint:
                        url = build_url({'mode': 'umount', 'device': disk})
                        li = xbmcgui.ListItem(label)
                        li.setInfo(type='video', infoLabels={'plot': "Mount ("+disk+")", 'playcount':1, 'overlay':5})
                    else:
                       url = build_url({'mode': 'mount', 'device': disk})
                       li = xbmcgui.ListItem(label)
                       li.setInfo(type='video', infoLabels={'plot': "Mount ("+disk+")", 'playcount': 0, 'overlay': 4})

                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    except:
        print("No device found...")

    xbmcplugin.endOfDirectory(addon_handle)


if mode is None:
    load_drive()

elif mode[0] == 'mount':
    bus = dbus.SystemBus()
    # import web_pdb; web_pdb.set_trace()
    obj = bus.get_object('org.freedesktop.UDisks2', currdisk)
    print(obj.Mount({}, dbus_interface='org.freedesktop.UDisks2.Filesystem'))
    xbmc.executebuiltin('Container.Refresh')

elif mode[0] == 'umount':
    bus = dbus.SystemBus()
    # import web_pdb; web_pdb.set_trace()
    obj = bus.get_object('org.freedesktop.UDisks2', currdisk)
    print(obj.Unmount({}, dbus_interface='org.freedesktop.UDisks2.Filesystem'))
    xbmc.executebuiltin('Container.Refresh')
