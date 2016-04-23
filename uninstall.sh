#!/usr/bin/env bash

USER=$(logname)
HOME=$(eval echo "~$USER")
echo "USER=$USER" 
echo "HOME=$HOME"

if [ -f "$HOME/Library/LaunchAgents/com.irouble.macmounter.plist" ]; then
    launchctl unload "$HOME/Library/LaunchAgents/com.irouble.macmounter.plist"
fi
rm -f "$HOME/Library/LaunchAgents/com.irouble.macmounter.plist"
rm -f /usr/local/bin/macmounter.py
rm -rf "$HOME/Library/Application Support/macmounter"

echo -n "Do you want delete user configs [y|n] (default:no)? "
read yesno
if [ "$yesno" == "y" ]; then
    rm -rf "$HOME/.macmounter"
else
    echo "Leaving configs in $HOME/.macmounter"
fi
