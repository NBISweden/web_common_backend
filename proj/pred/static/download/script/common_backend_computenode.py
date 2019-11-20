#!/usr/bin/env python

# Developed with Python 3.6+

# Description: access the common backend  via WSDL service
# Copyright Nanjiang Shu (nanjiang.shu@scilifelab.se)

import os
import sys
import json
import logging
import hashlib
import logging.config
import yaml
progname =  os.path.basename(sys.argv[0])
wspace = ''.join([" "]*len(progname))
rundir = os.path.dirname(os.path.realpath(__file__))

no_suds_message="""\
suds is not installed!
Please install suds by

$ pip install suds-jurko
"""

try:
    from suds.client import Client
except ImportError:
    print(no_suds_message, file=sys.stderr)
    sys.exit(1)

from suds.transport.https import HttpAuthenticated
from urllib.request import HTTPSHandler

import urllib.request, urllib.parse, urllib.error
import ssl

class CustomTransport(HttpAuthenticated):#{{{
    def u2handlers(self):

        # use handlers from superclass
        handlers = HttpAuthenticated.u2handlers(self)

        # create custom ssl context, e.g.:
        ctx = ssl._create_unverified_context()
        # configure context as needed...
        ctx.check_hostname = False

        # add a https handler using the custom context
        handlers.append(HTTPSHandler(context=ctx))
        return handlers
#}}}
def GetSeqIDFromAnnotation(line, method_seqid=1):#{{{
    """
    get the ID from the annotation line of the fasta  file
    method_seqid
        0: return the first word in the annotation line
        1: more complited way, default: 1
    ===updated 2013-03-06
    """
    if not line or line.lstrip == "" or line.lstrip() == ">":
        return ""

    if method_seqid == 0:
        return line.partition(" ")[0]
    elif method_seqid == 1:
        seqID = ""
        try:
            line = line.lstrip('>').split()[0]; #get the first word after '>'
            # if the annotation line has |, e.g. >sp|P0AE31|ARTM_ECOL6 Arginine ABC
            # transporter permease
        except:
            return ""
        if line and line.find('|') >= 0:
            strs = line.split("|")
            if (strs[0] in ["sp", "lcl", "tr", "gi", "r", "p"]): 
                seqID = strs[1]
            else : 
                seqID = strs[0]
        else:
            seqID=line
        seqID = seqID.rstrip(",")
        if seqID.find("UniRef") != -1:
            try: 
                ss = seqID.split("_")
                seqID = ss[1]
            except IndexError:
                pass
        return seqID
    else:
        msg = "Unrecognized method (%d) in function %s"
        print(msg%(method, sys._getframe().f_code.co_name), file=sys.stderr)
        return ""
#}}}
def ReadSingleFasta(inFile):#{{{
# return seqID, annotation, aaSeq
# the leading '>' of the annotation is removed
    try:
        seqID=""
        aaSeq=""
        annotation=""
        fpin = open(inFile, "r")
        lines = fpin.readlines()
        fpin.close()
        for line in lines:
            if line[0] == ">":
                seqID = GetSeqIDFromAnnotation(line)
                annotation = line.lstrip(">").strip()
            else:
                aaSeq+=line.strip()
        return (seqID, annotation, aaSeq)
    except IOError: 
        print("Failed to ReadSingleFasta for ", inFile, file=sys.stderr)
        return ("","", "")
#}}}

MAX_FILESIZE_IN_MB = 9
MAX_FILESIZE = MAX_FILESIZE_IN_MB*1024*1024

usage_short="""
Usage: %s -m submit|get [-seq SEQFILE] [-jobname NAME] [-soft-name NAME]
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

  -model  FILE   Supply model file in PDB format

  -jobname STR   Give the job a name

  -email   STR   Send a notification to the email when the result is ready

  -jobid   STR   Retrieve the result by supplying a valid jobid

  -outpath DIR   Save the retrieved data to outpath, (default: ./)

  -url     URL   provide the URL

  -soft-name STR supply the software name, .e.g
                 dummy, subcons, prodres, docker_subcons

  -log     FILE  supply custom logging configuration yaml file

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

  -proq3-deep         yes|no     Whether use deep learning for ProQ3, (default: yes)

  -proq3-quality      STR        Method for quality accessment for ProQ3, (default: sscore)

  Note that for the option sets {-jackhmmer_e-val, -jackhmmer_bitscore} and 
  {-pfamscan_e-val, -pfamscan_bitscore}, only one of them can be set.

Created 2017-02-06, updated 2018-05-07, Nanjiang Shu
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
def setup_logging(#{{{
    default_path='log.yml',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
#}}}

def main(g_params):#{{{
    argv = sys.argv
    numArgv = len(argv)
    if numArgv < 2:
        PrintHelp()
        return 1

    url = "https://130.239.81.116"
    mode = ""
    jobid = ""
    email = ""
    jobname = ""
    fixtopfile = ""
    seqfile = ""
    modelfile = ""
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
    query_para['isDeepLearning'] = True
    query_para['method_quality'] = "sscore"
    name_software = ""


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
            elif argv[i] in ["-model", "--model"]:
                (modelfile, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-soft-name", "--soft-name"]:
                (name_software, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-jobname", "--jobname"]:
                (jobname, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-log", "--log"]:
                (g_params['log_config_file'],i) = my_getopt_str(argv, i)
            elif argv[i] in ["-email", "--email"]:
                (email, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-jobid", "--jobid"]:
                (jobid, i) = my_getopt_str(argv, i)
            elif argv[i] in ["-url", "--url"]:
                (url, i) = my_getopt_str(argv, i)
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
            elif argv[i] in ["-proq3-deep", "--proq3-deep"]:
                (tmpstr, i) = my_getopt_str(argv,i)
                if tmpstr == "yes":
                    query_para['isDeepLearning'] = True
                elif tmpstr == "no":
                    query_para['isDeepLearning'] = False
                else:
                    print("Argument '-proq3-deep' should be followed by 'yes' or 'no', but %s was provided. Exit."%(tmpstr), file=sys.stderr)
                    return 1
            elif argv[i] in ["-proq3-quality", "--proq3-quality"]:
                (query_para['method_quality'], i) = my_getopt_str(argv, i)
                if not query_para['method_quality'] in ['sscore', 'lddt', "tmscore", "cad"]:
                    print("value of --proq3-quality should be one of [sscore, lddt, tmscore, cad],but %s was set. Exit."%(query_para['method_quality']), file=sys.stderr)
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
    setup_logging(g_params['log_config_file'])
    logger = logging.getLogger(__name__)

    wsdl_url = url + "/pred/api_submitseq/?wsdl"
    query_para['name_software'] = name_software
    g_ctx = ssl._create_unverified_context()

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


        if wsdl_url.startswith("https"):
            myclient = Client(wsdl_url, transport=CustomTransport(), cache=None)
        else:
            myclient = Client(wsdl_url, cache=None)

        if name_software in ["docker_proq3", "proq3"]:
            (t_seqid, t_seqanno, t_seq) = ReadSingleFasta(seqfile)
            md5_key = hashlib.md5(t_seq).hexdigest()
            subfoldername = md5_key[:2]
            url_profile = "http://proq3.bioinfo.se/static/result/profilecache/%s/%s.zip"%(subfoldername, md5_key)
            query_para['targetseq'] = t_seq
            query_para['url_profile'] = url_profile
            query_para['isRepack'] = True
            query_para['isKeepFiles'] = True
            query_para['pdb_model'] = ReadFile(modelfile)

        para_str = json.dumps(query_para, sort_keys=True)
        logger.debug("para_str=%s"%(str(para_str)))

        retValue = myclient.service.submitjob_remote(seq, para_str, jobname, email, str(1), "True")
        logger.debug("retValue=%s"% str(retValue))
        if len(retValue) >= 1:
            strs = retValue[0]
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
        myclient = Client(wsdl_url, transport=CustomTransport(), cache=None)
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
                if result_url.startswith("https"):
                    f = urllib.request.urlopen(result_url,  context=g_ctx)
                    with open(outfile, "wb") as local_file:
                        local_file.write(f.read())
                else:
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
    g_params['log_config_file'] = "%s/default_log.yml"%(rundir)
    return g_params
#}}}
if __name__ == '__main__' :
    g_params = InitGlobalParameter()
    sys.exit(main(g_params))

