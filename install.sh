#!/usr/bin/env bash

USER=`logname`

echo "Creating .macmounter folder..."
mkdir -p "$HOME/.macmounter"
if [ ! -d "$HOME/.macmounter" ]; then
    echo "Error creating .macmounter folder."
else
    chown $USER "$HOME/.macmounter"
fi
cp ./sample/example.conf "$HOME/.macmounter"
chown $USER "$HOME/.macmounter/example.conf"

echo "Creating application folder..."
mkdir -p "$HOME/Library/Application Support/macmounter"
if [ ! -d "$HOME/Library/Application Support/macmounter" ]; then
    echo "Error creating application folder."
else
    chown $USER "$HOME/Library/Application Support/macmounter"
fi

echo "Installing script..."
cp ./scripts/macmounter.py /usr/local/bin
if [ ! -f /usr/local/bin/macmounter.py ]; then
    echo "Error installing script."
fi

echo "Installing launcher"
cp ./launch/com.irouble.macmounter.plist "$HOME/Library/LaunchAgents"
if [ ! -f "$HOME/Library/LaunchAgents/com.irouble.macmounter.plist" ]; then
    echo "Error installing launcher."
else
    echo "Stopping service"
    launchctl unload "$HOME/Library/LaunchAgents/com.irouble.macmounter.plist"
    echo "Starting service"
    launchctl load -w "$HOME/Library/LaunchAgents/com.irouble.macmounter.plist"
fi
