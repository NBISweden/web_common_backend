#!/bin/bash 

platform_info=`python -mplatform |  tr '[:upper:]' '[:lower:]'`
platform=
case $platform_info in 
    *centos*)platform=centos;;
    *redhat*) platform=redhat;;
    *ubuntu*|*debian*)platform=ubuntu;;
    *)platform=other;;
esac

case $platform in 
    centos|redhat) user=apache;group=apache;;
    ubuntu) user=www-data;group=www-data;;
    other)echo Unrecognized platform $platform_info; exit 1;;
esac

id -u $user
