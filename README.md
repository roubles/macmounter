# macmounter

A very light weight python daemon that mounts remote servers, and keeps them mounted. macmounter can be used for *any* protocol, sshfs, samba, afp, ftp, ntfs, webdav etc. 

It is written for a OS X, but should be portable to any system that runs python 2.7.X.

This is completely command line driven and is not moron friendly. Though, for g33ks, it is a two step install, and a one step per server.

## Install

### Step 1 - Get code
```
git clone https://github.com/roubles/macmounter.git
```

### Step 2 - Install script
```
cd macmounter
sudo ./install.sh
```

## Configure
Add config files in the directory ~/.macmounter/

A simple config file looks like:
```
[example.com]
PING_CMD=/sbin/ping -q -c3 -o example.com 
MOUNT_TEST_CMD=/sbin/mount | grep -q "sshfs/somelocalfolder"
PRE_MOUNT_CMD=/bin/mkdir -p /Users/roubles/somelocalfolder/
MOUNT_CMD=/usr/local/bin/sshfs roubles@example.com:/someremotefolder /Users/roubles/somelocalfolder/ -oauto_cache,reconnect,volname=auto
MOUNT_SUCCESS_CMD=/bin/echo "" | /usr/bin/mail -s "mounted example.com!" roubles@github.com
```

But, it can be simpler. The simplest config only needs to specify MOUNT_CMD.
```
[example.com]
MOUNT_CMD=/usr/local/bin/sshfs roubles@example.com:/someremotefolder /Users/prmehta/somelocalfolder/ -oauto_cache,reconnect,volname=auto
```

## Starting

The macmounter service will start when it is installed. But you can manually startup macmounter using the commandline:
```
launchctl load -w ~/Library/LaunchAgents/com.irouble.macmounter.plist
```

or, logout and log back in (recommended).

## Logs

Detailed logs can be found here: ~/Library/Application Support/macmounter/macmounter.log

More detailed documentation can be found on the wiki here: https://github.com/roubles/macmounter/wiki
