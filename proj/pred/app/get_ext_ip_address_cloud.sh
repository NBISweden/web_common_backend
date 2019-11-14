#/bin/bash

# Description: 
#   get the IP address of the running computer.
#   This is useful to get the public (floating) IP within a virutal machine    
dig +short myip.opendns.com @resolver1.opendns.com
