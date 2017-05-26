#!/bin/bash

usage="
USAGE: $0 SEQFILE OUTDIR
"

VERBOSE=1

domain=euka

rundir=`dirname $0`
rundir=$(readlink -f $rundir)

#cd $rundir

if [ $# -lt 2 ];then
	echo "$usage"
	exit 1
fi

SEQFILE=$1
OUTDIR=$2


SEQFILE=$(readlink -f $SEQFILE)
OUTDIR=$(readlink -f $OUTDIR)


RUNTOOL=$rundir/TOOLS

exec_cmd(){
    case $VERBOSE in 
        yes|1)
        echo -e "\n$*\n"
    esac
    eval "$*"
}


basename_seqfile=$(basename $SEQFILE)
rootname_seqfile=${basename_seqfile%.*}


#CREATE FOLDER:
if [ ! -d "$OUTDIR/prediction" ]; then
	mkdir -p $OUTDIR/prediction
fi

if [ ! -d "$OUTDIR/for-dat" ]; then
	mkdir -p $OUTDIR/for-dat
fi
if [ ! -d "$OUTDIR/dat-files" ]; then
	mkdir -p $OUTDIR/dat-files
fi
if [ ! -d "$OUTDIR/final-prediction" ]; then
	mkdir -p $OUTDIR/final-prediction
fi

if [ ! -d "$OUTDIR/plot" ]; then
	mkdir -p $OUTDIR/plot
fi


exec_cmd "cat > $SEQFILE > $OUTDIR/query.result.txt"

success5=1
