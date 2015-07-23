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

A basic configuration example that should get you started can be found [here](https://github.com/roubles/macmounter/wiki/basic-example).

## More examples

### Testing mounts before remounting
It is prudent to test if the mount is active and functioning before blindly remounting. [These examples](https://github.com/roubles/macmounter/wiki/testing-mounts) show the various options for testing mounts.

### Waking up servers before mounting
Sometimes NAS boxes go to sleep when idle. [These examples](https://github.com/roubles/macmounter/wiki/wakeup-server-before-mounting) show the various options for waking up remote drives on the LAN. 

### Unmounting before mounting
If your mount test fails, it is very likely that the mount is in a weird state. It is recommended that you force an unmount before trying to remount. [These examples](https://github.com/roubles/macmounter/wiki/unmount-before-mount) show the various options for unmounting before remounting.

### Success/Failure commands
Sometimes it is desirable to run commands on success or failure. One good reason is to notify someone of the success or failure. [These examples](https://github.com/roubles/macmounter/wiki/status-notification-commands) show the various options of running commands on success or failure.

### Custom retry timers
macmounter by default uses a five minute timer to retry for every case. However, it is written to be very configurable, and you can fine tune the retry time for pretty much every state. [These examples](https://github.com/roubles/macmounter/wiki/configure-polling-intervals) show the various options for fine tuning the retry timers per state.

### Miscellaneous examples
[This](https://github.com/roubles/macmounter/wiki/Example-Configs) is a full list of example configs.

## Password management

It is not recommended to store your password in cleartext in the config files. macmounter provides simple shell scripts to use OSX's keychain to store passwords. More information is [here](https://github.com/roubles/macmounter/wiki/password-management).

## Architecture/Wiki

More detailed documentation can be found on the wiki [here](https://github.com/roubles/macmounter/wiki).

## Uninstall
```
cd macmounter
sudo ./uninstall.sh
```
