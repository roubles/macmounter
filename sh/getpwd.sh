#!/usr/bin/env bash

PWD=`security find-generic-password -wa $1`
printf "$PWD"
#printf %q "$PWD" #Escaped PWD!
