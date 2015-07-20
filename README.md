# macmounter

A light weight, scalable, python daemon that **automatically mounts** remote servers on login, and **keeps them mounted**. macmounter can be used for *any* protocol, sshfs, samba, afp, ftp, ntfs, webdav etc. 

It is written for a OS X, but, should be portable to any system that runs python 2.7.X.

This is completely command line driven and is **not** moron friendly. For g33ks, it is a two step install, and a one step configuration per server. The logs are very verbose and should indicate any issues.

## Install

### Step 1 - Get code
```
git clone https://github.com/roubles/macmounter.git
```

### Step 2 - Install
```
cd macmounter
sudo ./install.sh
```

## Configure
Add config files in the directory ~/.macmounter/

A simple config file looks like:
```
[example.com]
MOUNT_TEST_CMD=ls -l /Users/roubles/somelocalfolder/
PING_CMD=/sbin/ping -q -c3 -o example.com 
PRE_MOUNT_CMD=/bin/mkdir -p /Users/roubles/somelocalfolder/
MOUNT_CMD=/usr/local/bin/sshfs roubles@example.com:/someremotefolder /Users/roubles/somelocalfolder/ -oauto_cache,reconnect,volname=example
MOUNT_SUCCESS_CMD=/bin/echo "" | /usr/bin/mail -s "mounted example.com!" roubles@github.com
```

But, it can be simpler. The simplest config only needs to specify MOUNT_CMD, though this may be inefficient.
```
[example.com]
MOUNT_CMD=/usr/local/bin/sshfs roubles@example.com:/someremotefolder /Users/prmehta/somelocalfolder/ -oauto_cache,reconnect,volname=auto
```

## Starting/Stopping

The macmounter service should start when it is installed. 

The macmounter service starts everytime you login, and dies everytime you log off. 

You can manually startup macmounter using the commandline:
```
launchctl load -w ~/Library/LaunchAgents/com.irouble.macmounter.plist
```

or, logout and log back in.

## Logs

Detailed logs can be found here: ~/Library/Application Support/macmounter/macmounter.log

## Basic example

https://github.com/roubles/macmounter/wiki/basic-example

## Testing mounts examples and options

https://github.com/roubles/macmounter/wiki/testing-mounts

## Waking up servers example

https://github.com/roubles/macmounter/wiki/wakeup-server-before-mounting

## Unmounting before mounting example

https://github.com/roubles/macmounter/wiki/unmount-before-mount

## Full Blown example

https://github.com/roubles/macmounter/wiki/configure-polling-intervals

## Sample configs

A good list of sample configs can be found here: 
https://github.com/roubles/macmounter/wiki/Sample-configs

## Password management

It is not recommended to store your password in cleartext in the config files. macmounter provides simple shell scripts to use OSX's keychain to store passwords. More information is here: https://github.com/roubles/macmounter/wiki/password-management

## Architecture/Wiki

More detailed documentation can be found on the wiki here: https://github.com/roubles/macmounter/wiki

## Uninstall
```
cd macmounter
sudo ./uninstall.sh
```
