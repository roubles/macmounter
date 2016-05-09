#!/usr/bin/env bash

echo -n Account: 
read account

echo -n Service: 
read service

echo -n Password: 
read -s password
echo "$password"

security add-generic-password -a "${account}" -s "${service}" -w "${password}"
