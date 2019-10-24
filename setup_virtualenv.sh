#!/bin/bash
# install virtualenv if not installed
# first install dependencies
# install python2.7 if not exists by
# sudo /big/src/install_python2.7_centos.sh
# sudo pip2.7 install virtualenv
# sudo pip2.7 install virtualenv virtualenvwrapper

# then install programs in the virtual environment
mkdir -p ~/.virtualenvs
rundir=`dirname $0`
rundir=`readlink -f $rundir`
cd $rundir
exec_virtualenv=virtualenv
if [ -f "/usr/local/bin/virtualenv" ];then
    exec_virtualenv=/usr/local/bin/virtualenv
fi
eval "$exec_virtualenv env"
source ./env/bin/activate

pip install --ignore-installed -r requirements.txt

##############################################
# for PRODRES
#############################################
echo -e "\nInstall hmmer to env\n"
tmpdir=$(mktemp -d /tmp/tmpdir.setup_virtualenv.XXXXXXXXX) || { echo "Failed to create temp dir" >&2; exit 1; }

cd $tmpdir
url=http://eddylab.org/software/hmmer3/3.1b2/hmmer-3.1b2-linux-intel-x86_64.tar.gz
curl -O $url
filename=$(basename $url)
tar -xzf $filename
foldername=$(find . -maxdepth 1 -type d -name "[^.]*")
/bin/cp -f $foldername/binaries/* $rundir/env/bin/
cd $rundir
/bin/rm -rf $tmpdir

tmpdir=$(mktemp -d /tmp/tmpdir.setup_virtualenv.XXXXXXXXX) || { echo "Failed to create temp dir" >&2; exit 1; }
cd $tmpdir

echo -e "\nInstall blast to env\n"
url=ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.6.0+-x64-linux.tar.gz
curl -O $url
filename=$(basename $url)
tar -xzf $filename
foldername=$(find . -maxdepth 1 -type d -name "[^.]*")
/bin/cp -f $foldername/bin/* $rundir/env/bin/
cd $rundir
/bin/rm -rf $tmpdir

##############################################
# Copy blast2 to pred/app/soft
foldername=blast-2.2.26
if [ ! -d $rundir/proj/pred/app/soft/blast/$foldername ];then
    if [ ! -d $rundir/proj/pred/app/soft/blast ];then
        mkdir -p $rundir/proj/pred/app/soft/blast/
    fi
    tmpdir=$(mktemp -d /tmp/tmpdir.setup_virtualenv.XXXXXXXXX) || { echo "Failed to create temp dir" >&2; exit 1; }
    cd $tmpdir
    echo -e "\nInstall blast-2.2.26 to proj/pred/app/soft/blast\n"
    url=ftp://ftp.ncbi.nlm.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz
    curl -O $url
    filename=$(basename $url)
    tar -xzf $filename
    foldername=$(find . -maxdepth 1 -type d -name "[^.]*")

    /bin/cp -r $foldername $rundir/proj/pred/app/soft/blast/
    cd $rundir
    /bin/rm -rf $tmpdir
fi
