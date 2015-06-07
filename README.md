# macmounter

A very light weight python daemon that keeps your remote servers mounted. Can be used for *any* protocol, sshfs, samba, afp, ftp, ntfs, webdav etc. 

It is written for a OS X, but should be portable to any system that runs python 2.7.X.

This is completely command line driven and is not moron friendly. Though, for g33ks, it is a two step install, and a one step per server.

## Install

### Step 1 - Get code
```
git clone 
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
```

But, it can be simpler, you only need to specify MOUNT_CMD.
```
[example.com]
MOUNT_CMD=/usr/local/bin/sshfs roubles@example.com:/someremotefolder /Users/prmehta/somelocalfolder/ -oauto_cache,reconnect,volname=auto
```

More detailed documentation is coming.
