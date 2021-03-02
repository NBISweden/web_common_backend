#!/usr/bin/env python

# Description: access the PRODRES web-server http://prodres.bioinfo.se via WSDL service
# Copyright Nanjiang Shu (nanjiang.shu@scilifelab.se)

import os
import sys
import json
progname =  os.path.basename(sys.argv[0])
wspace = ''.join([" "]*len(progname))

no_suds_message="""\
suds is not installed!
Please install suds by

$ pip install suds
"""

try:
    from suds.client import Client
except ImportError:
    print(no_suds_message, file=sys.stderr)
    sys.exit(1)

import urllib.request, urllib.parse, urllib.error

MAX_FILESIZE_IN_MB = 9
MAX_FILESIZE = MAX_FILESIZE_IN_MB*1024*1024

usage_short="""
Usage: %s -m submit|get [-seq SEQFILE] [-jobname NAME] [-email EMAIL]
       %s               [-jobid JOBID] [-outpath DIR]
"""%(progname, wspace)

usage_ext="""
Description:
    Access the PRODRES web-server (http://prodres.bioinfo.se) through WSDL service

OPTIONS:
  -m submit|get  Set the mode
                 submit - submit a job to WSDL
                 get    - retrieve the result from the server

  -seq    FILE   Supply input sequence in FASTA format

  -jobname STR   Give the job a name

  -email   STR   Send a notification to the email when the result is ready

  -jobid   STR   Retrieve the result by supplying a valid jobid

  -outpath DIR   Save the retrieved data to outpath, (default: ./)

  -h, --help     Print this help message and exit

Advanced options:
  -second-search STR             Choose method for second round search,
                                 psiblast or jackhmmer (default: psiblast)
  -pfamscan_bitscore FLOAT       Set bit-score threshold for PfamScan, (default: 2)

  -pfamscan_e-val    FLOAT       Set e-value threshold for PfamScan, (default: None)

  -pfamscan_clan-overlap yes|no  Whether use PfamScan clan overlapping, (default: yes)

  -jackhmmer-threshold-type  e-value|bit-score
                                 Set the threshold type for jackhmmer, (default: bit-score)

  -jackhmmer_bitscore FLOAT      Set bit-score threshold for jackhmmer, (default: 25)

  -jackhmmer_e-val    FLOAT      Set e-value threshold for jackhmmer, (default: None)

  -jackhmmer_max_iter INT        Set maximum iterations for jackhmmer, (default: 3)

  -psiblast_e-val     FLOAT      Set e-value threshold for psiblast, (default: 0.1)

  -psiblast_iter      INT        Set maximum iterations for psiblast, (default: 3)

  -psiblast_outfmt    STR        Set output format for psiblast, (default: 0)

  Note that for the option sets {-jackhmmer_e-val, -jackhmmer_bitscore} and 
  {-pfamscan_e-val, -pfamscan_bitscore}, only one of them can be set.

Created 2017-02-06, updated 2017-02-07, Nanjiang Shu
"""
usage_exp="""
Examples:
    # submit test.fa with jobname 'test' to the server 
    %s -m submit -seq test.fa -jobname test

    # try to retrieve the result for jobid 'rst_TTT' and save it to the current
    # directory
    %s -m get -jobid rst_TTT

"""%(progname, progname)

def my_getopt_str(argv, i):#{{{
    """
    Get a string from the argument list, return the string and the updated
    index to the argument list
    """
    try:
        opt = argv[i+1]
        if opt[0] == "-":
            msg = "Error! option '%s' must be followed by a string"\
                    ", not an option arg."
            print(msg%(argv[i]), file=sys.stderr)
            sys.exit(1)
        return (opt, i+2)
    except IndexError:
        msg = "Error! option '%s' must be followed by a string"
        print(msg%(argv[i]), file=sys.stderr)
        sys.exit(1)
#}}}
def my_getopt_int(argv, i):#{{{
    """
    Get an integer value from the argument list, return the integer value and
    the updated index to the argument list
    """
    try:
        opt = argv[i+1]
        if opt[0] == "-":
            msg = "Error! option '%s' must be followed by an INT value"\
                    ", not an option arg."
            print(msg%(argv[i]), file=sys.stderr)
            sys.exit(1)
        try:
            opt = int(opt)
            return (opt, i+2)
        except (ValueError, TypeError):
            msg = "Error! option '%s' must be followed by an INT value"
            print(msg%(argv[i]), file=sys.stderr)
            sys.exit(1)
    except IndexError:
        msg = "Error! option '%s' must be followed by an INT value"
        print(msg%(argv[i]), file=sys.stderr)
        sys.exit(1)
#}}}
def my_getopt_float(argv, i):#{{{
    """
    Get an real number from the argument list, return the real number and
    the updated index to the argument list
    """
    try:
        opt = argv[i+1]
        if opt[0] == "-":
            msg = "Error! option '%s' must be followed by an FLOAT value"\
                    ", not an option arg."
            print(msg%(argv[i]), file=sys.stderr)
            sys.exit(1)
        try:
            opt = float(opt)
            return (opt, i+2)
        except (ValueError, TypeError):
            msg = "Error! option '%s' must be followed by an FLOAT value"
            print(msg%(argv[i]), file=sys.stderr)
            sys.exit(1)
    except IndexError:
        msg = "Error! option '%s' must be followed by an FLOAT value"
        print(msg%(argv[i]), file=sys.stderr)
        sys.exit(1)
#}}}
def PrintHelp(fpout=sys.stdout):#{{{
    print(usage_short, file=fpout)
    print(usage_ext, file=fpout)
    print(usage_exp, file=fpout)#}}}
def ReadFile(infile, mode="r"):#{{{
    try: 
        fpin = open(infile, mode)
        content = fpin.read()
        fpin.close()
        return content
    except IOError:
        print("Failed to read file %s with mode '%s'"%(infile,
                mode), file=sys.stderr)
        return ""
#}}}

def main(g_params):#{{{
    argv = sys.argv
    numArgv = len(argv)
    if numArgv < 2:
        PrintHelp()
        return 1

    wsdl_url = "http://prodres.bioinfo.se/pred/api_submitseq/?wsdl"
    mode = ""
    jobid = ""
    email = ""
    jobname = ""
    fixtopfile = ""
    seqfile = ""
    outpath = "./"

    query_para = {}
    query_para['isKeepTempFile'] = False
    query_para['second_method'] = 'psiblast'
    query_para['pfamscan_bitscore'] = "2"
    query_para['pfamscan_evalue'] = ""
    query_para['pfamscan_clanoverlap'] = True
    query_para['jackhmmer_threshold_type'] = "bit-score"
    query_para['jackhmmer_evalue'] = ""
    query_para['jackhmmer_bitscore'] = "25"
    query_para['jackhmmer_iteration'] = "3"
    query_para['psiblast_evalue'] = "0.1"
    query_para['psiblast_iteration'] = "3"
    query_para['psiblast_outfmt'] = "0"


    i = 1
    isNonOptionArg=False
    while i < numArgv:#{{{
        if isNonOptionArg == True:
            print("Error! Wrong argument:", argv[i], file=sys.stderr)
            return 1
            isNonOptionArg = False
            i += 1
        elif argv[i] == "--":
            isNonOptionArg = True
            i += 1
        elif argv[i][0] == "-":
            if argv[i] in ["-h", "--help"]:
                PrintHelp()
                return 0
            elif argv[i] in ["-m", "--m"]:
                (mode, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-seq", "--seq"]:
                (seqfile, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-jobname", "--jobname"]:
                (jobname, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-email", "--email"]:
                (email, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-jobid", "--jobid"]:
                (jobid, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-outpath", "--outpath"]:
                (outpath, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-outpath", "--outpath"]:
                (outpath, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-second-search", "--second-search"]:
                (query_para['second_method'], i) = my_getopt_str(argv, i)
                if not query_para['second_method'] in ['psiblast', 'jackhmmer']:
                    print("value of --second-search should be either psiblast or jackhmmer, but %s was set. Exit."%(query_para['second_method']), file=sys.stderr)
                return 1
            elif argv[i] in ["-pfamscan_bitscore", "--pfamscan_bitscore"]:
                (query_para['pfamscan_bitscore'], i) = my_getopt_float(argv, i)
                query_para['pfamscan_bitscore'] = "%g"%(query_para['pfamscan_bitscore'])
            elif argv[i] in ["-pfamscan_e-val", "--pfamscan_e-val"]:
                (query_para['pfamscan_evalue'], i) = my_getopt_float(argv, i)
                query_para['pfamscan_evalue'] = "%g"%(query_para['pfamscan_bitscore'])
            elif argv[i] in ["-pfamscan_clanoverlap", "--pfamscan_clanoverlap"]:
                (tmpstr, i) = my_getopt_str(argv,i)
                if tmpstr == "yes":
                    query_para['pfamscan_clanoverlap'] = True
                elif tmpstr == "no":
                    query_para['pfamscan_clanoverlap'] = False
                else:
                    print("Argument '-pfamscan_clanoverlap' should be followed by 'yes' or 'no', but %s was provided. Exit."%(tmpstr), file=sys.stderr)
                    return 1
            elif argv[i] in ["-jackhmmer_threshold_type", "--jackhmmer_threshold_type"]:
                (tmpstr, i) = my_getopt_str(argv,i)
                if tmpstr in ['bit-score', 'e-value']:
                    query_para['jackhmmer_threshold_type'] = tmpstr
                else:
                    print("Argument '-jackhmmer_threshold_type' should be followed by 'bit-score' or 'e-value', but %s was provided. Exit."%(tmpstr), file=sys.stderr)
                    return 1
            elif argv[i] in ["-jackhmmer_evalue", "--jackhmmer_evalue"]:
                (query_para['jackhmmer_evalue'], i) = my_getopt_float(argv, i)
                query_para['jackhmmer_evalue'] = "%g"%(query_para['jackhmmer_evalue'])
            elif argv[i] in ["-jackhmmer_bitscore", "--jackhmmer_bitscore"]:
                (query_para['jackhmmer_bitscore'], i) = my_getopt_float(argv, i)
                query_para['jackhmmer_bitscore'] = "%g"%(query_para['jackhmmer_bitscore'])
            elif argv[i] in ["-jackhmmer_iteration", "--jackhmmer_iteration"]:
                (query_para['jackhmmer_iteration'], i) = my_getopt_int(argv, i)
            elif argv[i] in ["-psiblast_evalue", "--psiblast_evalue"]:
                (query_para['psiblast_evalue'], i) = my_getopt_float(argv, i)
                query_para['psiblast_evalue'] = "%g"%(query_para['psiblast_evalue'])
            elif argv[i] in ["-psiblast_iteration", "--psiblast_iteration"]:
                (query_para['psiblast_iteration'], i) = my_getopt_int(argv, i)
                if  query_para['psiblast_iteration'] < 1:
                    print("Argument '-psiblast_iteration' should be followed by an integer >= 1, but %d was provided. Exit."%(query_para['psiblast_iteration']), file=sys.stderr)
                    return 1
                query_para['psiblast_iteration'] = str(query_para['psiblast_iteration'])
            elif argv[i] in ["-psiblast_outfmt", "--psiblast_outfmt"]:
                (query_para['psiblast_outfmt'], i) = my_getopt_str(argv, i)
                if not query_para['psiblast_outfmt'] in [str(x) for x in range(0,12)]:
                    print("Argument '-psiblast_outfmt' should have value 0-11, but %s was provided. Exit."%(query_para['psiblast_outfmt']), file=sys.stderr)
                    return 1
            else:
                print("Error! Wrong argument:", argv[i], file=sys.stderr)
                return 1
        else:
            print("Error! Wrong argument:", argv[i], file=sys.stderr)
            return 1
#}}}
    # validating arguments

    if mode == "":
        print("mode not set. exit!", file=sys.stderr)
        print(usage_short)
        return 1
    elif not mode in ["submit", "get"]:
        print("unrecognized mode. exit!", file=sys.stderr)
        print(usage_short)
        return 1

    if mode == "submit":
        if seqfile == "":
            print("You want to submit a job but seqfile not set. exit!", file=sys.stderr)
            print(usage_short)
            return 1
        elif not os.path.exists(seqfile):
            print("seqfile %s does not exist. exit!"%(seqfile), file=sys.stderr)
            return 1

        try:
            filesize = os.path.getsize(seqfile)
        except OSError:
            print("failed to get the size of seqfile %s. exit"%(seqfile), file=sys.stderr)
            return 1

        if filesize >= MAX_FILESIZE:
            print("You input seqfile %s exceeds the "\
                    "upper limit %d Mb."%(seqfile, MAX_FILESIZE_IN_MB), file=sys.stderr)
            print("Please split your seqfile and submit again.", file=sys.stderr)
            return 1
        seq = ReadFile(seqfile)

        para_str = json.dumps(query_para, sort_keys=True)
#         print para_str
        #return 0

        myclient = Client(wsdl_url, cache=None)
        retValue = myclient.service.submitjob(seq, para_str, jobname, email)
        if len(retValue) >= 1:
            strs = retValue[0]
            print(strs)
            jobid = strs[0]
            result_url = strs[1]
            numseq_str = strs[2]
            errinfo = strs[3]
            warninfo = strs[4]
            if jobid != "None" and jobid != "":
                print("You have successfully submitted your job "\
                        "with %s sequences. jobid = %s"%(numseq_str, jobid))
                if warninfo != "" and warninfo != "None":
                    print("Warning message:\n", warninfo)
            else:
                print("Failed to submit job to %s"%(wsdl_url))
                if errinfo != "" and errinfo != "None":
                    print("Error message:\n", errinfo)
                if warninfo != "" and warninfo != "None":
                    print("Warning message:\n", warninfo)
        else:
            print("Failed to submit job to %s"%(wsdl_url))
            return 1
    else:
        if jobid == "":
            print("You want to get the result of a job but jobid not set. exit!", file=sys.stderr)
            return 1
        myclient = Client(wsdl_url, cache=None)
        retValue = myclient.service.checkjob(jobid)
        if len(retValue) >= 1:
            strs = retValue[0]
            status = strs[0]
            result_url = strs[1]
            errinfo = strs[2]
            if status == "Failed":
                print("Your job with jobid %s is failed!")
                if errinfo != "" and errinfo != "None":
                    print("Error message:\n", errinfo)
            elif status == "Finished":
                print("Your job with jobid %s is finished!"%(jobid))
                if not os.path.exists(outpath):
                    try:
                        os.makedirs(outpath)
                    except OSError:
                        print("Failed to create the outpath %s"%(outpath))
                        return 1
                outfile = "%s/%s.zip"%(outpath, jobid)
                urllib.request.urlretrieve (result_url, outfile)
                if os.path.exists(outfile):
                    print("The result file %s has been retrieved for jobid %s"%(outfile, jobid))
                else:
                    print("Failed to retrieve result for jobid %s"%(jobid))
            elif status == "None":
                print("Your job with jobid %s does not exist! Please check you typing!"%(jobid))
            else:
                print("Your job with jobid %s is not ready, status = %s"%(jobid, status))
        else:
            print("Failed to get job!")
            return 1

    return 0

#}}}

def InitGlobalParameter():#{{{
    g_params = {}
    g_params['isQuiet'] = True
    return g_params
#}}}
if __name__ == '__main__' :
    g_params = InitGlobalParameter()
    sys.exit(main(g_params))

