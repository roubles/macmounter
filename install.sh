#!/usr/bin/env bash

echo "Creating .macmounter folder..."
mkdir -p "$HOME/.macmounter"
if [ ! -d "$HOME/.macmounter" ]; then
    echo "Error creating .macmounter folder."
fi
cp ./sample/example.conf "$HOME/.macmounter"

echo "Creating application folder..."
mkdir -p "$HOME/Library/Application Support/macmounter"
if [ ! -d "$HOME/Library/Application Support/macmounter" ]; then
    echo "Error creating application folder."
fi

echo "Installing script..."
cp ./scripts/macmounter.py /usr/local/bin
if [ ! -f /usr/local/bin/macmounter.py ]; then
    echo "Error installing script."
fi

echo "Installing launcher"
cp ./launch/com.irouble.macmounter.plist ~/Library/LaunchAgents
if [ ! -f ~/Library/LaunchAgents/com.irouble.macmounter.plist ]; then
    echo "Error installing launcher."
fi
