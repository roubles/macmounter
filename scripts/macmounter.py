#!/usr/bin/env python
# Author: Rouble Matta (@roubles)

import os
import sys
import ConfigParser
import argparse
import logging
import logging.handlers
import itertools
import subprocess
from subprocess import CalledProcessError
import time
import threading
import signal
import traceback
import shlex

def ctrlc_handler (signal, frame):
    global running
    logger.info('You pressed Ctrl+C!')
    running = False
    killMounters()

def hup_handler (signal, frame):
    logger.info('Caught signal HUP. macmounter restarted!')
    launchMounters(updateConfig())
    for mounter in mounterMap.values():
        mounter.reload = True # This triggers the mounter to restart

# Global variables are evil. Except these.
logger = logging.getLogger("macmounter")

# Constants
DEFAULT_RECHECK_INTERVAL_SECONDS = 300
DEFAULT_WAKE_ATTEMPTS = 2
DEFAULT_MOUNT_TEST_CMD = None
DEFAULT_PING_CMD = None
DEFAULT_PING_SUCCESS_CMD = None
DEFAULT_PING_FAILURE_CMD = None
DEFAULT_WAKE_CMD = None
DEFAULT_PRE_MOUNT_CMD = None
DEFAULT_MOUNT_CMD = None
DEFAULT_POST_MOUNT_CMD = None
DEFAULT_LOST_MOUNT_CMD = None
DEFAULT_FOUND_MOUNT_CMD = None
DEFAULT_MOUNT_SUCCESS_CMD = None
DEFAULT_MOUNT_FAILURE_CMD = None
homeConfigFolder = os.path.join(os.path.expanduser("~"), ".macmounter")
homeConfigFile = os.path.join(os.path.expanduser("~"), ".macmounter.conf")

# Actual global variables
mounterMap = dict()
running = True

# global configs
conffile = None
confdir = None
confFileMtime = None
confDirMtime = None
dotMacMounterFileConfMtime = None
dotMacMounterDirConfMtime = None

def setupParser ():
    #Setup argparse
    loglevel = ['critical', 'error', 'warning', 'info', 'debug']
    parser = argparse.ArgumentParser(description='Mac Mounter. Keeps external drives mounted.')
    parser.add_argument('-c', '--conffile', help='Full path to conf file')
    parser.add_argument('-d', '--confdir', help='Full path to conf file directory')
    parser.add_argument('-l', '--logfile', help="Logging file", action="store", default=None)
    parser.add_argument("-v", "--loglevel", help="Set log level", choices=loglevel, default='info')
    parser.add_argument("-m", "--macdefaults", help="Use mac defaults for logs", action="store_true", default=False)
    parser.add_argument("-o", "--nostdout", help="Do not display logs to stdout", action="store_true", default=False)
    parser.add_argument("-r", "--reload", help="Reload currently running daemon (or mount all configured mounts now!)", action="store_true", default=False)
    return parser

def setupLogger (logger, loglevel, logfile, stdout = False, rollover = False, rotate = False, backupCount = 3, maxBytes = 2097152):
    logger.setLevel(logging.DEBUG)

    #create a steam handler
    stdouthandler = logging.StreamHandler(sys.stdout)
    if stdout:
        stdouthandler.setLevel(logging.getLevelName(loglevel.upper()))
    else:
        # We want to output errors to stdout no matter what
        stdouthandler.setLevel(logging.WARNING)

    # create a logging format for stdout
    # stdoutformatter = logging.Formatter('%(message)s')
    stdoutformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(thread)d - %(message)s')
    stdouthandler.setFormatter(stdoutformatter)

    # add the stdout handler to the logger
    logger.addHandler(stdouthandler)

    if logfile is not None:
        # create a file handler
        # We rotate the log file when it hits 2MB, and we save at most 3 log
        # files, so 6MB of total log data.
        if rotate:
            filehandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=maxBytes, backupCount=backupCount)
            # On startup rollover the last file
            if rollover:
                if os.path.isfile(logfile):
                    filehandler.doRollover()
        else:
            filehandler = logging.FileHandler(logfile)

        filehandler.setLevel(logging.getLevelName(loglevel.upper()))
        # create a logging format for the log file
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(thread)d - %(message)s')
        filehandler.setFormatter(formatter)

        # add the file handler to the logger
        logger.addHandler(filehandler)

    return logger

def getConfFilesFromFolder (foldername, newerThanTime=0):
    logger.info("Looking for config files in: " + foldername)
    configFiles = []

    if (os.path.isdir(foldername)):
        for dirname,subdirs,files in os.walk(foldername):
            for fname in files:
                if fname.endswith(".conf"):
                    full_path = os.path.join(dirname, fname)
                    mtime = os.path.getmtime(full_path)
                    if mtime > newerThanTime:
                        configFiles.append(full_path)

    return configFiles

def operateOnSection(section, filename):
    mounterthread = mounter(section, filename)
    logger.info("Created thread: " + str(mounterthread))
    mounterthread.start()
    return mounterthread

def operateOnFile(filename):
    config = ConfigParser.ConfigParser()
    config.read(filename)
    threads = []
    for section in config.sections():
        logger.info("Found Section: " + section + ", filename: " + str(filename))
        if section + filename not in mounterMap:
            threads.append(operateOnSection(section, filename))
        else:
            logger.info("Not recreating thread for section: " + section + " in file: " + filename)
    return threads

def get_absolute_path (path):
    if path is None:
        return path
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))

def getConfFileMTime ():
    if os.path.isfile(conffile):
        return getFileMTime(conffile)
    else:
        return None

def getFileMTime (filename):
    return os.path.getmtime(filename)

def getDirMTime (directory):
    max_mtime = 0
    dirmtime = os.path.getmtime(directory)
    for dirname,subdirs,files in os.walk(directory):
        for fname in files:
            full_path = os.path.join(dirname, fname)
            mtime = os.path.getmtime(full_path)
            if mtime > max_mtime:
                max_mtime = mtime
                max_dir = dirname
                max_file = fname
    if (dirmtime > max_mtime):
        return dirmtime
    else:
        return max_mtime

def getConfDirMTime ():
    if os.path.isdir(confdir):
        return getDirMTime(confdir)
    else:
        return None

def getDotMacMounterFileConfMtime ():
    if os.path.isfile(homeConfigFile): 
        return getFileMTime(homeConfigFile)
    else:
        return None

def getDotMacMounterDirConfMtime ():
    if os.path.isdir(homeConfigFolder): 
        return getDirMTime(homeConfigFolder)
    else:
        return None

def updateConfig ():
    global dotMacMounterDirConfMtime
    global dotMacMounterFileConfMtime
    global confFileMtime
    global confDirMtime

    configFiles = []
    if conffile or confdir:
        if conffile:
            logger.info("Got conf file: " + conffile)
            configFiles.append(conffile)
            confFileMtime = getConfFileMTime()
            logger.info("Config file modification time: " + time.ctime(confFileMtime))
        if confdir:
            logger.info("Got conf dir: " + confdir)
            configFiles.extend(getConfFilesFromFolder(confdir))
            confDirMtime = getConfDirMTime()
            logger.info("Config directory modification time: " + time.ctime(confDirMtime))
    else:
        if os.path.isfile(homeConfigFile): 
            logger.info("Looking for configs in " + homeConfigFile)
            configFiles.append(homeConfigFile)
            dotMacMounterFileConfMtime = getDotMacMounterFileConfMtime()
            logger.info("~/.macmounter.conf modification time: " + time.ctime(dotMacMounterFileConfMtime))

        if os.path.isdir(homeConfigFolder):
            logger.info("Looking for configs in " + homeConfigFolder)
            configFiles.extend(getConfFilesFromFolder(homeConfigFolder))
            dotMacMounterDirConfMtime = getDotMacMounterDirConfMtime()
            logger.info("~/.macmounter/ modification time: " + time.ctime(dotMacMounterDirConfMtime))


    return configFiles

def killMounters ():
    for mounter in mounterMap.values():
        mounter.stop()

def monitorConfigs ():
    global dotMacMounterDirConfMtime
    global dotMacMounterFileConfMtime
    global confFileMtime
    global confDirMtime

    logger.info("Monitoring configs.")
    while running:
        configFiles = []
        if conffile or confdir:
            if conffile:
                newConfFileMtime = getConfFileMTime()
                if newConfFileMtime > confFileMtime:
                    logger.info("config file changed!")
                    logger.info("new time: " + time.ctime(newConfFileMtime))
                    logger.info("old time: " + time.ctime(confFileMtime))
                    configFiles.append(conffile)
                    confFileMtime = newConfFileMtime
            if confdir:
                newConfDirMtime = getConfDirMTime()
                if newConfDirMtime > confDirMtime:
                    logger.info("config directory changed!")
                    logger.info("new time: " + time.ctime(newConfDirMtime))
                    logger.info("old time: " + time.ctime(confDirMtime))
                    configFiles.extend(getConfFilesFromFolder(confdir, confDirMtime))
                    confDirMtime = newConfDirMtime
        else:
            if os.path.isfile(homeConfigFile): 
                newDotMacMounterFileConfMtime = getDotMacMounterFileConfMtime()
                if newDotMacMounterFileConfMtime > dotMacMounterFileConfMtime:
                    logger.info("~/.macmounter.conf file changed!")
                    logger.info("new time: " + time.ctime(newDotMacMounterFileConfMtime))
                    logger.info("old time: " + time.ctime(dotMacMounterFileConfMtime))
                    configFiles.append(homeConfigFile)
                    dotMacMounterFileConfMtime = newDotMacMounterFileConfMtime
            if os.path.isdir(homeConfigFolder):
                newDotMacMounterDirConfMtime = getDotMacMounterDirConfMtime()
                if newDotMacMounterDirConfMtime > dotMacMounterDirConfMtime:
                    logger.info("~/.macmounter directory changed!")
                    logger.info("new time: " + time.ctime(newDotMacMounterDirConfMtime))
                    logger.info("old time: " + time.ctime(dotMacMounterDirConfMtime))
                    configFiles.extend(getConfFilesFromFolder(homeConfigFolder, dotMacMounterDirConfMtime))
                    dotMacMounterDirConfMtime = newDotMacMounterDirConfMtime
        if configFiles:
            logger.info("Configs have changed!")
            launchMounters(configFiles)
        #logger.info("Sleeping...")
        time.sleep(float(1))
        #logger.info("Done sleeping...")
    logger.info("Tango down. Config monitor thread dead.")

def waitOnMounters ():
    logger.info("Waiting on mounters: " + str(mounterMap.keys()))
    mounterMapCount = len(mounterMap)
    if mounterMapCount > 0:
        logger.info("Waiting on " + str(mounterMapCount) + " mounters!")
        time.sleep(float(1))
    logger.info("Mounters eliminated.")
    logger.info("Dave, this conversation can serve no purpose anymore. Goodbye.")

def launchMounters (configFiles):
    logger.info("Launching mounters... for configFiles: " + str(configFiles))
    for filename in configFiles:
        logger.info("Found file: " + str(filename))
        operateOnFile(filename)

def getConfig(config, section, option, default=None, ctype=str, logPrefix=""):
    ret = None
    try:
        ret = config.get(section, option)
    except:
        pass
    if isBlank(ret):
        ret = default
    logger.info(logPrefix + "For config: " + option + "=>" + str(ret))
    if ret:
        return ctype(ret)
    else:
        return None

# int main(int argc, char *argv[]);
def crux ():
    global conffile
    global confdir

    parser = setupParser()
    args = parser.parse_args()

    conffile = get_absolute_path(args.conffile)
    if conffile and not os.path.isfile(conffile):
        logger.error(conffile + " is not a valid file. Ignoring")
        conffile = None

    confdir = get_absolute_path(args.confdir)
    if confdir and not os.path.isdir(confdir):
        logger.error(confdir + " is not a valid dir. Ignoring")
        confdir = None

    # Apply mac defaults
    if args.macdefaults and not args.logfile:
        args.logfile = os.path.join(os.path.expanduser("~"), "Library/Application Support/macmounter/macmounter.log")

    args.logfile = get_absolute_path(args.logfile)
    setupLogger (logger, args.loglevel, args.logfile, not args.nostdout, False, True, 10)
    logger.info("===> Starting macmounter on " + time.strftime("%Y-%m-%dT%H.%M.%S") + "with pid " + str(os.getpid()) + "<===")

    if args.reload:
        # BSD Specific?
        cmd = "launchctl list | grep com.irouble.macmounter | cut -f1"
        pid = executeCommand(cmd, "", True)
        if isNotBlank(pid):
            logger.info("Restarting PID="+pid)
            os.kill(int(pid), signal.SIGHUP)
        return

    launchMounters(updateConfig())
    monitorConfigs()
    waitOnMounters()

def executeCommand(cmd, logPrefix="", returnstdout=False):
    rc = None
    #args = shlex.split(cmd) 
    args = cmd
    logger.info(logPrefix + "Running cmd: " + str(args))
    try:
        child = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        streamdata = child.communicate()[0]
        child.wait()
        rc = child.returncode
        #print "SD: " + streamdata
        #print "here RC"
    except CalledProcessError as e:
        #print "here2 RC"
        rc = e.returncode
    except OSError as ose:
        #print "here3 RC"
        rc = ose.errno
    except:
        #print "here4 RC"
        print traceback.format_exc()
        print sys.exc_info()[0]
    finally:
        #print "here5 RC"
        logger.info(logPrefix + "RC=" + str(rc))
        if returnstdout:
            return streamdata
        else:
            return rc

def isBlank (myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return False
    #myString is None OR myString is empty or blank
    return True

def isNotBlank (myString):
    if myString and myString.strip():
        #myString is not None AND myString is not empty or blank
        return True
    #myString is None OR myString is empty or blank
    return False

def runCmd (cmd, logPrefix=""):
    if cmd and (executeCommand(cmd, logPrefix) == 0):
        return True
    else:
        return False

class mounter (threading.Thread):
     def __init__ (self, section, filename):
         threading.Thread.__init__( self )
         logger.info("Setting up thread for resource " + section)
         logger.info("Added thread to mounter map: " + section + filename + "=>" + str(self))
         mounterMap[section + filename] = self
         self.states = ['INIT', 'PING_SUCCESS', 'PING_FAILURE', 'MOUNT_SUCCESS', 'MOUNT_FAILURE']
         self.state = 'INIT'
         self.modifyTime = os.path.getmtime(filename)
         self.filename = filename
         self.section = section
         self.logprefix = "[" + self.section + "] "
         self.config = ConfigParser.ConfigParser()
         self.mounted = False
         self.reload = False
         self.updateConfigs()

     # Should be called *after* changing state
     def updateCurrentInterval (self):
         logger.info(self.logprefix + "Updating current interval in state [" + self.state + "]")
         if self.state is 'PING_SUCCESS':
             self.setCurrentInterval(self.intervalpingsuccess)
         elif self.state is 'PING_FAILURE':
             self.setCurrentInterval(self.intervalpingfailure)
         elif self.state is 'MOUNT_SUCCESS':
             self.setCurrentInterval(self.intervalmountsuccess)
         elif self.state is 'MOUNT_FAILURE':
             self.setCurrentInterval(self.intervalmountfailure)
         else:
             self.setCurrentInterval(self.interval)

     def setCurrentInterval (self, currentinterval):
         logger.info(self.logprefix + "Setting current interval to [" + str(currentinterval) + "]")
         self.currentinterval = currentinterval

     def changeState (self, toState):
         if self.state not in self.states:
             logger.error(self.logprefix + "Unknown state [" + toState + "]")
             return
         logger.info(self.logprefix + "Changing state from [" + self.state + "] to [" + toState + "]")
         self.state = toState

     def updateConfigs (self):
         logger.info(self.logprefix + "Updating configs from file: " + self.filename + " and section: " + self.section)
         self.config = ConfigParser.ConfigParser()
         self.config.read(self.filename)
         if not self.config.has_section(self.section):
             logger.info(self.logprefix + "Section has been removed from config file.")
             self.stop()
             return
         self.interval = getConfig(self.config, self.section, 'RECHECK_INTERVAL_SECONDS', DEFAULT_RECHECK_INTERVAL_SECONDS, int, logPrefix=self.logprefix)
         self.intervalpingsuccess = getConfig(self.config, self.section, 'RECHECK_INTERVAL_SECONDS_PING_SUCCESS', self.interval, int, logPrefix=self.logprefix)
         self.intervalpingfailure = getConfig(self.config, self.section, 'RECHECK_INTERVAL_SECONDS_PING_FAILURE', self.interval, int, logPrefix=self.logprefix)
         self.intervalmountsuccess = getConfig(self.config, self.section, 'RECHECK_INTERVAL_SECONDS_MOUNT_SUCCESS', self.interval, int, logPrefix=self.logprefix)
         self.intervalmountfailure = getConfig(self.config, self.section, 'RECHECK_INTERVAL_SECONDS_MOUNT_FAILURE', self.interval, int, logPrefix=self.logprefix)
         self.mounttestcmd = getConfig(self.config, self.section, 'MOUNT_TEST_CMD', DEFAULT_MOUNT_TEST_CMD, logPrefix=self.logprefix)
         self.pingcmd = getConfig(self.config, self.section, 'PING_CMD', DEFAULT_PING_CMD, logPrefix=self.logprefix)
         self.premountcmd = getConfig(self.config, self.section, 'PRE_MOUNT_CMD', DEFAULT_PRE_MOUNT_CMD, logPrefix=self.logprefix)
         self.wakecmd = getConfig(self.config, self.section, 'WAKE_CMD', DEFAULT_WAKE_CMD, logPrefix=self.logprefix)
         self.wakeattempts = getConfig(self.config, self.section, 'WAKE_ATTEMPTS', DEFAULT_WAKE_ATTEMPTS, int, logPrefix=self.logprefix)
         self.mountcmd = getConfig(self.config, self.section, 'MOUNT_CMD', DEFAULT_MOUNT_CMD, logPrefix=self.logprefix)
         self.mountsuccesscmd = getConfig(self.config, self.section, 'MOUNT_SUCCESS_CMD', DEFAULT_MOUNT_SUCCESS_CMD, logPrefix=self.logprefix)
         self.mountfailurecmd = getConfig(self.config, self.section, 'MOUNT_FAILURE_CMD', DEFAULT_MOUNT_FAILURE_CMD, logPrefix=self.logprefix)
         self.postmountcmd = getConfig(self.config, self.section, 'POST_MOUNT_CMD', DEFAULT_POST_MOUNT_CMD, logPrefix=self.logprefix)
         self.lostmountcmd = getConfig(self.config, self.section, 'LOST_MOUNT_CMD', DEFAULT_LOST_MOUNT_CMD, logPrefix=self.logprefix)
         self.foundmountcmd = getConfig(self.config, self.section, 'FOUND_MOUNT_CMD', DEFAULT_FOUND_MOUNT_CMD, logPrefix=self.logprefix)

     def stop (self):
         logger.info(self.logprefix + "Stopping thread: " + str(threading.current_thread()))
         self.running = False

     def mountFailure (self, reason=""):
         logger.info(self.logprefix + "Mount failure!")
         if isNotBlank(self.mountfailurecmd):
             logger.info(self.logprefix + "Mount failure command specified. Running.")
             runCmd("export REASON=\"" + reason + "\"; " + self.mountfailurecmd, self.logprefix)
         if self.mounted:
             if isNotBlank(self.lostmountcmd):
                 logger.info(self.logprefix + "Lost mount command specified. Running.")
                 runCmd("export REASON=\"" + reason + "\"; " + self.lostmountcmd, self.logprefix)
         self.mounted = False

     def mountSuccess (self):
         logger.info(self.logprefix + "Mount success!")
         if isNotBlank(self.mountsuccesscmd):
             logger.info(self.logprefix + "Mount success command specified. Running.")
             runCmd(self.mountsuccesscmd, self.logprefix)
         if not self.mounted:
             if isNotBlank(self.foundmountcmd):
                 logger.info(self.logprefix + "Found mount command specified. Running.")
                 runCmd(self.foundmountcmd, self.logprefix)
         self.mounted = True

     def run (self):
         seconds = 0
         self.updateCurrentInterval()
         self.running = True
         while self.running:
             try:
                 modifyTime = os.path.getmtime(self.filename)
                 if modifyTime > self.modifyTime:
                     logger.info(self.logprefix + "Configs have changed!")
                     logger.info(self.logprefix + "new config time: " + time.ctime(modifyTime))
                     logger.info(self.logprefix + "old config time: " + time.ctime(self.modifyTime))
                     self.updateConfigs()
                     self.modifyTime = modifyTime
                     self.configsmodified = True
                 else:
                     self.configsmodified = False
             except Exception as e:
                 logger.error(e)
                 logger.info("File " + self.filename + " is gone!")
                 break
             if (seconds % self.currentinterval == 0) or self.configsmodified or self.reload:
                 try:
                     self.reload = False
                     logger.info(self.logprefix + "Working on section [" + self.section + "] from file [" + self.filename + "]")
                     if isBlank(self.mountcmd):
                         #First make sure we have a mount command.
                         logger.info(self.logprefix + "No mount command specified. Nothing to do for")
                     else:
                         if isBlank(self.mounttestcmd):
                             logger.info(self.logprefix + "No mount test command specified. Can't test mount. Assume not mounted.")
                             # Assume not mounted!
                         else:
                             logger.info(self.logprefix + "Mount test command specified.")
                             if runCmd(self.mounttestcmd, self.logprefix):
                                 # Resource is already mounted. Do nothing.
                                 logger.info(self.logprefix + "Resource is already mounted. Nothing to do.")
                                 self.mountSuccess()
                                 self.changeState('MOUNT_SUCCESS')
                             else:
                                 logger.info(self.logprefix + "Resource is no longer mounted.")
                                 self.mountFailure()
                                 self.changeState('MOUNT_FAILURE')
                         if not self.mounted:
                             # Resource is not mounted.
                             logger.info(self.logprefix + "Resource is NOT mounted. Lets get to work.")
                             pingSuccess = False
                             if isNotBlank(self.pingcmd):
                                 logger.info(self.logprefix + "Ping command specified.")
                                 if isNotBlank(self.wakecmd):
                                     logger.info(self.logprefix + "Wake command specified.")
                                     wakeAttempts = self.wakeattempts
                                     while (True):
                                         logger.info(self.logprefix + "PING! Houston do you copy?")
                                         if not runCmd(self.pingcmd, self.logprefix):
                                             logger.info(self.logprefix + "Ping failed! Wake attempts left: " + str(wakeAttempts))
                                             if (wakeAttempts == 0):
                                                 self.mountFailure("Ping failed.")
                                                 self.changeState('PING_FAILURE')
                                                 break
                                             logger.info(self.logprefix + "Now try to wake the resource up.")
                                             runCmd(self.wakecmd, self.logprefix)
                                             wakeAttempts -= 1
                                         else:
                                             logger.info(self.logprefix + "Ping successful.")
                                             self.changeState('PING_SUCCESS')
                                             pingSuccess = True
                                             break
                                 else:
                                     logger.info(self.logprefix + "PING! Houston do you copy?")
                                     if runCmd(self.pingcmd, self.logprefix):
                                         logger.info(self.logprefix + "Ping successful.")
                                         self.changeState('PING_SUCCESS')
                                         pingSuccess = True
                                     else:
                                         self.mountFailure("Ping failed.")
                                         self.changeState('PING_FAILURE')
                                         logger.info(self.logprefix + "Resource is down. Will not attempt mount.")
                             else:
                                 # No ping command, we assume ping suceeds, and
                                 # we force mounting process
                                 logger.info(self.logprefix + "Ping command not specified. Assuming success.")
                                 pingSuccess = True
                             
                             if pingSuccess:
                                 if isNotBlank(self.premountcmd):
                                     logger.info(self.logprefix + "Pre mount command specified. Running.")
                                     if not runCmd(self.premountcmd, self.logprefix):
                                         logger.info(self.logprefix + "Pre mount command failed!")

                                 logger.info(self.logprefix + "Mounting...")
                                 if not runCmd(self.mountcmd, self.logprefix):
                                     self.mountFailure("Mount failed.")
                                     self.changeState('MOUNT_FAILURE')
                                 else:
                                     self.mountSuccess()
                                     self.changeState('MOUNT_SUCCESS')

                                 if isNotBlank(self.postmountcmd):
                                     logger.info(self.logprefix + "Post mount command specified. Running.")
                                     if not runCmd(self.postmountcmd, self.logprefix):
                                         logger.info(self.logprefix + "Post Mount command failed!")
                     self.updateCurrentInterval()
                     logger.info(self.logprefix + "Next test after " + str(self.currentinterval) + " seconds")
                 except Exception as e:
                     logger.error("Caught exception! Logging and continuing...")
                     logger.error(e)
                     logger.exception(e)
             time.sleep(float(1))
             seconds += 1
         logger.info(self.logprefix + "Hasta La Vista. Baby.")
         mounterMap.pop(self.section + self.filename, None)
         logger.info("Removed thread from mounter map: " + self.section + self.filename)

# Register signal handler
signal.signal(signal.SIGINT, ctrlc_handler)
signal.signal(signal.SIGHUP, hup_handler)

if __name__ == "__main__":  crux()
