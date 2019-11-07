#!/usr/bin/env python

# Description:
#   A collection of classes and functions used by web-servers
#
# Author: Nanjiang Shu (nanjiang.shu@scilifelab.se)
#
# Address: Science for Life Laboratory Stockholm, Box 1031, 17121 Solna, Sweden

import os
import sys
import myfunc
rundir = os.path.dirname(os.path.realpath(__file__))
from datetime import datetime
from dateutil import parser as dtparser
from pytz import timezone
import tabulate
import time
import sqlite3
import logging
import shutil
import subprocess
import re
FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S %Z"
TZ = "Europe/Stockholm"
basedir = os.path.realpath("%s/.."%(rundir)) # path of the application, i.e. pred/
path_log = "%s/static/log"%(basedir)
path_stat = "%s/stat"%(path_log)
path_result = "%s/static/result"%(basedir)

def IsFrontEndNode(base_www_url):#{{{
    """
    check if the base_www_url is front-end node
    if base_www_url is ip address, then not the front-end
    otherwise yes
    """
    base_www_url = base_www_url.lstrip("http://").lstrip("https://").split("/")[0]
    if base_www_url == "":
        return False
    elif base_www_url.find("computenode") != -1:
        return False
    else:
        arr =  [x.isdigit() for x in base_www_url.split('.')]
        if all(arr):
            return False
        else:
            return True
#}}}
def RunCmd(cmd, logfile, errfile, verbose=False):# {{{
    """Input cmd in list
       Run the command and also output message to logs
    """
    begin_time = time.time()

    isCmdSuccess = False
    cmdline = " ".join(cmd)
    date_str = time.strftime(FORMAT_DATETIME)
    rmsg = ""
    try:
        rmsg = subprocess.check_output(cmd)
        if verbose:
            msg = "workflow: %s"%(cmdline)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  logfile, "a", True)
        isCmdSuccess = True
    except subprocess.CalledProcessError, e:
        msg = "cmdline: %s\nFailed with message \"%s\""%(cmdline, str(e))
        myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  errfile, "a", True)
        isCmdSuccess = False
        pass

    end_time = time.time()
    runtime_in_sec = end_time - begin_time

    return (isCmdSuccess, runtime_in_sec)
# }}}
def datetime_str_to_epoch(date_str):# {{{
    """convert the datetime in string to epoch
    The string of datetime may with or without the zone info
    """
    return dtparser.parse(date_str).strftime("%s")
# }}}
def datetime_str_to_time(date_str):# {{{
    """convert the datetime in string to datetime type
    The string of datetime may with or without the zone info
    """
    strs = date_str.split()
    dt = dtparser.parse(date_str)
    if len(strs) == 2:
        dt = dt.replace(tzinfo=timezone('UTC'))
    return dt
# }}}

def WriteSubconsTextResultFile(outfile, outpath_result, maplist,#{{{
        runtime_in_sec, base_www_url, statfile=""):
    try:
        fpout = open(outfile, "w")
        if statfile != "":
            fpstat = open(statfile, "w")

        date_str = time.strftime(FORMAT_DATETIME)
        print >> fpout, "##############################################################################"
        print >> fpout, "Subcons result file"
        print >> fpout, "Generated from %s at %s"%(base_www_url, date_str)
        print >> fpout, "Total request time: %.1f seconds."%(runtime_in_sec)
        print >> fpout, "##############################################################################"
        cnt = 0
        for line in maplist:
            strs = line.split('\t')
            subfoldername = strs[0]
            length = int(strs[1])
            desp = strs[2]
            seq = strs[3]
            seqid = myfunc.GetSeqIDFromAnnotation(desp)
            print >> fpout, "Sequence number: %d"%(cnt+1)
            print >> fpout, "Sequence name: %s"%(desp)
            print >> fpout, "Sequence length: %d aa."%(length)
            print >> fpout, "Sequence:\n%s\n\n"%(seq)

            rstfile1 = "%s/%s/%s/query_0_final.csv"%(outpath_result, subfoldername, "plot")
            rstfile2 = "%s/%s/query_0_final.csv"%(outpath_result, subfoldername)
            if os.path.exists(rstfile1):
                rstfile = rstfile1
            elif os.path.exists(rstfile2):
                rstfile = rstfile2
            else:
                rstfile = ""

            if os.path.exists(rstfile):
                content = myfunc.ReadFile(rstfile).strip()
                lines = content.split("\n")
                if len(lines) >= 6:
                    header_line = lines[0].split("\t")
                    if header_line[0].strip() == "":
                        header_line[0] = "Method"
                        header_line = [x.strip() for x in header_line]

                    data_line = []
                    for i in xrange(1, len(lines)):
                        strs1 = lines[i].split("\t")
                        strs1 = [x.strip() for x in strs1]
                        data_line.append(strs1)

                    content = tabulate.tabulate(data_line, header_line, 'plain')
            else:
                content = ""
            if content == "":
                content = "***No prediction could be produced with this method***"

            print >> fpout, "Prediction results:\n\n%s\n\n"%(content)

            print >> fpout, "##############################################################################"
            cnt += 1

    except IOError:
        print "Failed to write to file %s"%(outfile)
#}}}
def WriteTOPCONSTextResultFile(outfile, outpath_result, maplist,#{{{
        runtime_in_sec, base_www_url, statfile=""):
    try:
        methodlist = ['TOPCONS', 'OCTOPUS', 'Philius', 'PolyPhobius', 'SCAMPI',
                'SPOCTOPUS', 'Homology']
        fpout = open(outfile, "w")

        fpstat = None
        num_TMPro_cons = 0
        num_TMPro_any = 0
        num_nonTMPro_cons = 0
        num_nonTMPro_any = 0
        num_SPPro_cons = 0
        num_SPPro_any = 0

        if statfile != "":
            fpstat = open(statfile, "w")

        date_str = time.strftime(FORMAT_DATETIME)
        print >> fpout, "##############################################################################"
        print >> fpout, "TOPCONS2 result file"
        print >> fpout, "Generated from %s at %s"%(base_www_url, date_str)
        print >> fpout, "Total request time: %.1f seconds."%(runtime_in_sec)
        print >> fpout, "##############################################################################"
        cnt = 0
        for line in maplist:
            strs = line.split('\t')
            subfoldername = strs[0]
            length = int(strs[1])
            desp = strs[2]
            seq = strs[3]
            print >> fpout, "Sequence number: %d"%(cnt+1)
            print >> fpout, "Sequence name: %s"%(desp)
            print >> fpout, "Sequence length: %d aa."%(length)
            print >> fpout, "Sequence:\n%s\n\n"%(seq)

            is_TM_cons = False
            is_TM_any = False
            is_nonTM_cons = True
            is_nonTM_any = True
            is_SP_cons = False
            is_SP_any = False

            for i in xrange(len(methodlist)):
                method = methodlist[i]
                seqid = ""
                seqanno = ""
                top = ""
                if method == "TOPCONS":
                    topfile = "%s/%s/%s/topcons.top"%(outpath_result, subfoldername, "Topcons")
                elif method == "Philius":
                    topfile = "%s/%s/%s/query.top"%(outpath_result, subfoldername, "philius")
                elif method == "SCAMPI":
                    topfile = "%s/%s/%s/query.top"%(outpath_result, subfoldername, method+"_MSA")
                else:
                    topfile = "%s/%s/%s/query.top"%(outpath_result, subfoldername, method)
                if os.path.exists(topfile):
                    (seqid, seqanno, top) = myfunc.ReadSingleFasta(topfile)
                else:
                    top = ""
                if top == "":
                    #top = "***No topology could be produced with this method topfile=%s***"%(topfile)
                    top = "***No topology could be produced with this method***"

                if fpstat != None:
                    if top.find('M') >= 0:
                        is_TM_any = True
                        is_nonTM_any = False
                        if method == "TOPCONS":
                            is_TM_cons = True
                            is_nonTM_cons = False
                    if top.find('S') >= 0:
                        is_SP_any = True
                        if method == "TOPCONS":
                            is_SP_cons = True

                if method == "Homology":
                    showtext_homo = method
                    if seqid != "":
                        showtext_homo = seqid
                    print >> fpout, "%s:\n%s\n\n"%(showtext_homo, top)
                else:
                    print >> fpout, "%s predicted topology:\n%s\n\n"%(method, top)


            if fpstat:
                num_TMPro_cons += is_TM_cons
                num_TMPro_any += is_TM_any
                num_nonTMPro_cons += is_nonTM_cons
                num_nonTMPro_any += is_nonTM_any
                num_SPPro_cons += is_SP_cons
                num_SPPro_any += is_SP_any

            dgfile = "%s/%s/dg.txt"%(outpath_result, subfoldername)
            dg_content = ""
            if os.path.exists(dgfile):
                dg_content = myfunc.ReadFile(dgfile)
            lines = dg_content.split("\n")
            dglines = []
            for line in lines:
                if line and line[0].isdigit():
                    dglines.append(line)
            if len(dglines)>0:
                print >> fpout,  "\nPredicted Delta-G-values (kcal/mol) "\
                        "(left column=sequence position; right column=Delta-G)\n"
                print >> fpout, "\n".join(dglines)

            reliability_file = "%s/%s/Topcons/reliability.txt"%(outpath_result, subfoldername)
            reliability = ""
            if os.path.exists(reliability_file):
                reliability = myfunc.ReadFile(reliability_file)
            if reliability != "":
                print >> fpout, "\nPredicted TOPCONS reliability (left "\
                        "column=sequence position; right column=reliability)\n"
                print >> fpout, reliability
            print >> fpout, "##############################################################################"
            cnt += 1

        fpout.close()

        if fpstat:
            out_str_list = []
            out_str_list.append("num_TMPro_cons %d"% num_TMPro_cons)
            out_str_list.append("num_TMPro_any %d"% num_TMPro_any)
            out_str_list.append("num_nonTMPro_cons %d"% num_nonTMPro_cons)
            out_str_list.append("num_nonTMPro_any %d"% num_nonTMPro_any)
            out_str_list.append("num_SPPro_cons %d"% num_SPPro_cons)
            out_str_list.append("num_SPPro_any %d"% num_SPPro_any)
            fpstat.write("%s"%("\n".join(out_str_list)))

            fpstat.close()

        rstdir = os.path.realpath("%s/.."%(outpath_result))
        runjob_logfile = "%s/%s"%(rstdir, "runjob.log")
        runjob_errfile = "%s/%s"%(rstdir, "runjob.err")
        finishtagfile = "%s/%s"%(rstdir, "write_result_finish.tag")
        WriteDateTimeTagFile(finishtagfile, runjob_logfile, runjob_errfile)
    except IOError:
        print "Failed to write to file %s"%(outfile)
#}}}
def WriteProQ3TextResultFile(outfile, query_para, modelFileList, #{{{
        runtime_in_sec, base_www_url, proq3opt, statfile=""):
    try:
        fpout = open(outfile, "w")


        try:
            isDeepLearning = query_para['isDeepLearning']
        except KeyError:
            isDeepLearning = True

        if isDeepLearning:
            m_str = "proq3d"
        else:
            m_str = "proq3"

        try:
            method_quality = query_para['method_quality']
        except KeyError:
            method_quality = 'sscore'

        fpstat = None
        numTMPro = 0

        if statfile != "":
            fpstat = open(statfile, "w")
        numModel = len(modelFileList)

        date_str = time.strftime(FORMAT_DATETIME)
        print >> fpout, "##############################################################################"
        print >> fpout, "# ProQ3 result file"
        print >> fpout, "# Generated from %s at %s"%(base_www_url, date_str)
        print >> fpout, "# Options for Proq3: %s"%(str(proq3opt))
        print >> fpout, "# Total request time: %.1f seconds."%(runtime_in_sec)
        print >> fpout, "# Number of finished models: %d"%(numModel)
        print >> fpout, "##############################################################################"
        print >> fpout
        print >> fpout, "# Global scores"
        fpout.write("# %10s"%("Model"))

        cnt = 0
        for i  in xrange(numModel):
            modelfile = modelFileList[i]
            globalscorefile = "%s.%s.%s.global"%(modelfile, m_str, method_quality)
            if not os.path.exists(globalscorefile):
                globalscorefile = "%s.proq3.%s.global"%(modelfile, method_quality)
                if not os.path.exists(globalscorefile):
                    globalscorefile = "%s.proq3.global"%(modelfile)
            (globalscore, itemList) = ReadProQ3GlobalScore(globalscorefile)
            if i == 0:
                for ss in itemList:
                    fpout.write(" %12s"%(ss))
                fpout.write("\n")

            try:
                if globalscore:
                    fpout.write("%2s %10s"%("", "model_%d"%(i)))
                    for jj in xrange(len(itemList)):
                        fpout.write(" %12f"%(globalscore[itemList[jj]]))
                    fpout.write("\n")
                else:
                    print >> fpout, "%2s %10s"%("", "model_%d"%(i))
            except:
                pass

        print >> fpout, "\n# Local scores"
        for i  in xrange(numModel):
            modelfile = modelFileList[i]
            localscorefile = "%s.%s.%s.local"%(modelfile, m_str, method_quality)
            if not os.path.exists(localscorefile):
                localscorefile = "%s.proq3.local"%(modelfile)
            print >> fpout, "\n# Model %d"%(i)
            content = myfunc.ReadFile(localscorefile)
            print >> fpout, content

    except IOError:
        print "Failed to write to file %s"%(outfile)
#}}}
def WriteTextResultFile(name_software, outfile, outpath_result, maplist,#{{{
        runtime_in_sec, base_www_url, statfile=""):
    if name_software in ["subcons", "docker_subcons"]:
        WriteSubconsTextResultFile(outfile, outpath_result, maplist,
                runtime_in_sec, base_www_url, statfile)
    elif name_software in ["topcons2", "docker_topcons2"]:
        WriteTOPCONSTextResultFile(outfile, outpath_result, maplist,
                runtime_in_sec, base_www_url, statfile)

#}}}

def WriteDateTimeTagFile(outfile, logfile, errfile):# {{{
    if not os.path.exists(outfile):
        date_str = time.strftime(FORMAT_DATETIME)
        try:
            myfunc.WriteFile(date_str, outfile)
            msg = "Write tag file %s succeeded"%(outfile)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  logfile, "a", True)
        except Exception as e:
            msg = "Failed to write to file %s with message: \"%s\""%(outfile, str(e))
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  errfile, "a", True)
# }}}

def GetLocDef(predfile):#{{{
    """
    Read in LocDef and its corresponding score from the subcons prediction file
    """
    content = ""
    if os.path.exists(predfile):
        content = myfunc.ReadFile(predfile)

    loc_def = None
    loc_def_score = None
    if content != "":
        lines = content.split("\n")
        if len(lines)>=2:
            strs0 = lines[0].split("\t")
            strs1 = lines[1].split("\t")
            strs0 = [x.strip() for x in strs0]
            strs1 = [x.strip() for x in strs1]
            if len(strs0) == len(strs1) and len(strs0) > 2:
                if strs0[1] == "LOC_DEF":
                    loc_def = strs1[1]
                    dt_score = {}
                    for i in xrange(2, len(strs0)):
                        dt_score[strs0[i]] = strs1[i]
                    if loc_def in dt_score:
                        loc_def_score = dt_score[loc_def]

    return (loc_def, loc_def_score)
#}}}
def IsFrontEndNode(base_www_url):#{{{
    """
    check if the base_www_url is front-end node
    if base_www_url is ip address, then not the front-end
    otherwise yes
    """
    base_www_url = base_www_url.lstrip("http://").lstrip("https://").split("/")[0]
    if base_www_url == "":
        return False
    elif base_www_url.find("computenode") != -1:
        return False
    else:
        arr =  [x.isdigit() for x in base_www_url.split('.')]
        if all(arr):
            return False
        else:
            return True
#}}}
def ReadProQ3GlobalScore(infile):#{{{
    #return globalscore and itemList
    #itemList is the name of the items
    globalscore = {}
    keys = []
    values = []
    try:
        fpin = open(infile, "r")
        lines = fpin.read().split("\n")
        fpin.close()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().find("proq") != -1:
                keys = line.strip().split()
            elif myfunc.isnumeric(line.strip().split()[0]):
                values = line.split()
                try:
                    values = [float(x) for x in values]
                except:
                    values = []
        if len(keys) == len(values):
            for i in xrange(len(keys)):
                globalscore[keys[i]] = values[i]
    except IOError:
        pass
    return (globalscore, keys)
#}}}
def GetProQ3Option(query_para):#{{{
    """Return the proq3opt in list
    """
    yes_or_no_opt = {}
    for item in ['isDeepLearning', 'isRepack', 'isKeepFiles']:
        if query_para[item]:
            yes_or_no_opt[item] = "yes"
        else:
            yes_or_no_opt[item] = "no"

    proq3opt = [
            "-r", yes_or_no_opt['isRepack'],
            "-deep", yes_or_no_opt['isDeepLearning'],
            "-k", yes_or_no_opt['isKeepFiles'],
            "-quality", query_para['method_quality'],
            "-output_pdbs", "yes"         #always output PDB file (with proq3 written at the B-factor column)
            ]
    if 'targetlength' in query_para:
        proq3opt += ["-t", str(query_para['targetlength'])]

    if 'submitter' in query_para and query_para['submitter'] in ['CAMEO', 'VIP']:
        proq3opt += ["-return_dist", "yes"]

    return proq3opt

#}}}
def ValidateParameter_PRODRES(query_para):#{{{
    """Validate the input parameters for PRODRES
    query_para is a dictionary
    """
    is_valid = True
    if not 'errinfo' in query_para:
        query_para['errinfo'] = ""
    if query_para['pfamscan_evalue'] != "" and query_para['pfamscan_bitscore'] != "":
        query_para['errinfo'] += "Parameter setting error!"
        query_para['errinfo'] += "Both PfamScan E-value and PfamScan Bit-score "\
                "are set! One and only one of them should be set!"
        is_valid = False

    if query_para['jackhmmer_bitscore'] != "" and query_para['jackhmmer_evalue'] != "":
        query_para['errinfo'] += "Parameter setting error!"
        query_para['errinfo'] += "Both Jackhmmer E-value and Jackhmmer Bit-score "\
                "are set! One and only one of them should be set!"
        is_valid = False
    query_para['isValidSeq'] = is_valid
    return is_valid
#}}}
def ValidateQuery(request, query, g_params):#{{{
    query['errinfo_br'] = ""
    query['errinfo_content'] = ""
    query['warninfo'] = ""

    has_pasted_seq = False
    has_upload_file = False
    if query['rawseq'].strip() != "":
        has_pasted_seq = True
    if query['seqfile'] != "":
        has_upload_file = True

    if has_pasted_seq and has_upload_file:
        query['errinfo_br'] += "Confused input!"
        query['errinfo_content'] = "You should input your query by either "\
                "paste the sequence in the text area or upload a file."
        return False
    elif not has_pasted_seq and not has_upload_file:
        query['errinfo_br'] += "No input!"
        query['errinfo_content'] = "You should input your query by either "\
                "paste the sequence in the text area or upload a file "
        return False
    elif query['seqfile'] != "":
        try:
            fp = request.FILES['seqfile']
            fp.seek(0,2)
            filesize = fp.tell()
            if filesize > g_params['MAXSIZE_UPLOAD_FILE_IN_BYTE']:
                query['errinfo_br'] += "Size of uploaded file exceeds limit!"
                query['errinfo_content'] += "The file you uploaded exceeds "\
                        "the upper limit %g Mb. Please split your file and "\
                        "upload again."%(g_params['MAXSIZE_UPLOAD_FILE_IN_MB'])
                return False

            fp.seek(0,0)
            content = fp.read()
        except KeyError:
            query['errinfo_br'] += ""
            query['errinfo_content'] += """
            Failed to read uploaded file \"%s\"
            """%(query['seqfile'])
            return False
        query['rawseq'] = content

    query['filtered_seq'] = ValidateSeq(query['rawseq'], query, g_params)
    is_valid = query['isValidSeq']
    return is_valid
#}}}
def ValidateSeq(rawseq, seqinfo, g_params):#{{{
# seq is the chunk of fasta file
# seqinfo is a dictionary
# return (filtered_seq)
    rawseq = re.sub(r'[^\x00-\x7f]',r' ',rawseq) # remove non-ASCII characters
    rawseq = re.sub(r'[\x0b]',r' ',rawseq) # filter invalid characters for XML
    filtered_seq = ""
    # initialization
    for item in ['errinfo_br', 'errinfo', 'errinfo_content', 'warninfo']:
        if item not in seqinfo:
            seqinfo[item] = ""

    seqinfo['isValidSeq'] = True

    seqRecordList = []
    myfunc.ReadFastaFromBuffer(rawseq, seqRecordList, True, 0, 0)
# filter empty sequences and any sequeces shorter than MIN_LEN_SEQ or longer
# than MAX_LEN_SEQ
    newSeqRecordList = []
    li_warn_info = []
    isHasEmptySeq = False
    isHasShortSeq = False
    isHasLongSeq = False
    isHasDNASeq = False
    cnt = 0
    for rd in seqRecordList:
        seq = rd[2].strip()
        seqid = rd[0].strip()
        if len(seq) == 0:
            isHasEmptySeq = 1
            msg = "Empty sequence %s (SeqNo. %d) is removed."%(seqid, cnt+1)
            li_warn_info.append(msg)
        elif len(seq) < g_params['MIN_LEN_SEQ']:
            isHasShortSeq = 1
            msg = "Sequence %s (SeqNo. %d) is removed since its length is < %d."%(seqid, cnt+1, g_params['MIN_LEN_SEQ'])
            li_warn_info.append(msg)
        elif len(seq) > g_params['MAX_LEN_SEQ']:
            isHasLongSeq = True
            msg = "Sequence %s (SeqNo. %d) is removed since its length is > %d."%(seqid, cnt+1, g_params['MAX_LEN_SEQ'])
            li_warn_info.append(msg)
        elif myfunc.IsDNASeq(seq):
            isHasDNASeq = True
            msg = "Sequence %s (SeqNo. %d) is removed since it looks like a DNA sequence."%(seqid, cnt+1)
            li_warn_info.append(msg)
        else:
            newSeqRecordList.append(rd)
        cnt += 1
    seqRecordList = newSeqRecordList

    numseq = len(seqRecordList)

    if numseq < 1:
        seqinfo['errinfo_br'] += "Number of input sequences is 0!\n"
        t_rawseq = rawseq.lstrip()
        if t_rawseq and t_rawseq[0] != '>':
            seqinfo['errinfo_content'] += "Bad input format. The FASTA format should have an annotation line start with '>'.\n"
        if len(li_warn_info) >0:
            seqinfo['errinfo_content'] += "\n".join(li_warn_info) + "\n"
        if not isHasShortSeq and not isHasEmptySeq and not isHasLongSeq and not isHasDNASeq:
            seqinfo['errinfo_content'] += "Please input your sequence in FASTA format.\n"

        seqinfo['isValidSeq'] = False
    elif numseq > g_params['MAX_NUMSEQ_PER_JOB']:
        seqinfo['errinfo_br'] += "Number of input sequences exceeds the maximum (%d)!\n"%(
                g_params['MAX_NUMSEQ_PER_JOB'])
        seqinfo['errinfo_content'] += "Your query has %d sequences. "%(numseq)
        seqinfo['errinfo_content'] += "However, the maximal allowed sequences per job is %d. "%(
                g_params['MAX_NUMSEQ_PER_JOB'])
        seqinfo['errinfo_content'] += "Please split your query into smaller files and submit again.\n"
        seqinfo['isValidSeq'] = False
    else:
        li_badseq_info = []
        if 'isForceRun' in seqinfo and seqinfo['isForceRun'] and numseq > g_params['MAX_NUMSEQ_FOR_FORCE_RUN']:
            seqinfo['errinfo_br'] += "Invalid input!"
            seqinfo['errinfo_content'] += "You have chosen the \"Force Run\" mode. "\
                    "The maximum allowable number of sequences of a job is %d. "\
                    "However, your input has %d sequences."%(g_params['MAX_NUMSEQ_FOR_FORCE_RUN'], numseq)
            seqinfo['isValidSeq'] = False


# checking for bad sequences in the query

    if seqinfo['isValidSeq']:
        for i in xrange(numseq):
            seq = seqRecordList[i][2].strip()
            anno = seqRecordList[i][1].strip().replace('\t', ' ')
            seqid = seqRecordList[i][0].strip()
            seq = seq.upper()
            seq = re.sub("[\s\n\r\t]", '', seq)
            li1 = [m.start() for m in re.finditer("[^ABCDEFGHIKLMNPQRSTUVWYZX*-]", seq)]
            if len(li1) > 0:
                for j in xrange(len(li1)):
                    msg = "Bad letter for amino acid in sequence %s (SeqNo. %d) "\
                            "at position %d (letter: '%s')"%(seqid, i+1,
                                    li1[j]+1, seq[li1[j]])
                    li_badseq_info.append(msg)

        if len(li_badseq_info) > 0:
            seqinfo['errinfo_br'] += "There are bad letters for amino acids in your query!\n"
            seqinfo['errinfo_content'] = "\n".join(li_badseq_info) + "\n"
            seqinfo['isValidSeq'] = False

# convert some non-classical letters to the standard amino acid symbols
# Scheme:
#    out of these 26 letters in the alphabet, 
#    B, Z -> X
#    U -> C
#    *, - will be deleted
    if seqinfo['isValidSeq']:
        li_newseq = []
        for i in xrange(numseq):
            seq = seqRecordList[i][2].strip()
            anno = seqRecordList[i][1].strip()
            seqid = seqRecordList[i][0].strip()
            seq = seq.upper()
            seq = re.sub("[\s\n\r\t]", '', seq)
            anno = anno.replace('\t', ' ') #replace tab by whitespace


            li1 = [m.start() for m in re.finditer("[BZ]", seq)]
            if len(li1) > 0:
                for j in xrange(len(li1)):
                    msg = "Amino acid in sequence %s (SeqNo. %d) at position %d "\
                            "(letter: '%s') has been replaced by 'X'"%(seqid,
                                    i+1, li1[j]+1, seq[li1[j]])
                    li_warn_info.append(msg)
                seq = re.sub("[BZ]", "X", seq)

            li1 = [m.start() for m in re.finditer("[U]", seq)]
            if len(li1) > 0:
                for j in xrange(len(li1)):
                    msg = "Amino acid in sequence %s (SeqNo. %d) at position %d "\
                            "(letter: '%s') has been replaced by 'C'"%(seqid,
                                    i+1, li1[j]+1, seq[li1[j]])
                    li_warn_info.append(msg)
                seq = re.sub("[U]", "C", seq)

            li1 = [m.start() for m in re.finditer("[*]", seq)]
            if len(li1) > 0:
                for j in xrange(len(li1)):
                    msg = "Translational stop in sequence %s (SeqNo. %d) at position %d "\
                            "(letter: '%s') has been deleted"%(seqid,
                                    i+1, li1[j]+1, seq[li1[j]])
                    li_warn_info.append(msg)
                seq = re.sub("[*]", "", seq)

            li1 = [m.start() for m in re.finditer("[-]", seq)]
            if len(li1) > 0:
                for j in xrange(len(li1)):
                    msg = "Gap in sequence %s (SeqNo. %d) at position %d "\
                            "(letter: '%s') has been deleted"%(seqid,
                                    i+1, li1[j]+1, seq[li1[j]])
                    li_warn_info.append(msg)
                seq = re.sub("[-]", "", seq)

            # check the sequence length again after potential removal of
            # translation stop
            if len(seq) < g_params['MIN_LEN_SEQ']:
                isHasShortSeq = 1
                msg = "Sequence %s (SeqNo. %d) is removed since its length is < %d (after removal of translation stop)."%(seqid, i+1, g_params['MIN_LEN_SEQ'])
                li_warn_info.append(msg)
            else:
                li_newseq.append(">%s\n%s"%(anno, seq))

        filtered_seq = "\n".join(li_newseq) # seq content after validation
        seqinfo['numseq'] = len(li_newseq)
        seqinfo['warninfo'] = "\n".join(li_warn_info) + "\n"

    seqinfo['errinfo'] = seqinfo['errinfo_br'] + seqinfo['errinfo_content']
    return filtered_seq
#}}}
def GetJobCounter(info): #{{{
# get job counter for the client_ip
# get the table from runlog, 
# for queued or running jobs, if source=web and numseq=1, check again the tag file in
# each individual folder, since they are queued locally
    logfile_query = info['divided_logfile_query']
    logfile_finished_jobid = info['divided_logfile_finished_jobid']
    isSuperUser = info['isSuperUser']
    client_ip = info['client_ip']
    maxdaystoshow = info['MAX_DAYS_TO_SHOW']

    jobcounter = {}

    jobcounter['queued'] = 0
    jobcounter['running'] = 0
    jobcounter['finished'] = 0
    jobcounter['failed'] = 0
    jobcounter['nojobfolder'] = 0 #of which the folder jobid does not exist

    jobcounter['queued_idlist'] = []
    jobcounter['running_idlist'] = []
    jobcounter['finished_idlist'] = []
    jobcounter['failed_idlist'] = []
    jobcounter['nojobfolder_idlist'] = []

    hdl = myfunc.ReadLineByBlock(logfile_query)
    if hdl.failure:
        return jobcounter
    else:
        finished_job_dict = myfunc.ReadFinishedJobLog(logfile_finished_jobid)
        finished_jobid_set = set([])
        failed_jobid_set = set([])
        for jobid in finished_job_dict:
            status = finished_job_dict[jobid][0]
            rstdir = "%s/%s"%(path_result, jobid)
            if status == "Finished":
                finished_jobid_set.add(jobid)
            elif status == "Failed":
                failed_jobid_set.add(jobid)
        lines = hdl.readlines()
        current_time = datetime.now(timezone(TZ))
        while lines != None:
            for line in lines:
                strs = line.split("\t")
                if len(strs) < 7:
                    continue
                ip = strs[2]
                if not isSuperUser and ip != client_ip:
                    continue

                submit_date_str = strs[0]
                isValidSubmitDate = True
                try:
                    submit_date = datetime_str_to_time(submit_date_str)
                except ValueError:
                    isValidSubmitDate = False

                if not isValidSubmitDate:
                    continue

                diff_date = current_time - submit_date
                if diff_date.days > maxdaystoshow:
                    continue
                jobid = strs[1]
                rstdir = "%s/%s"%(path_result, jobid)

                if jobid in finished_jobid_set:
                    jobcounter['finished'] += 1
                    jobcounter['finished_idlist'].append(jobid)
                elif jobid in failed_jobid_set:
                    jobcounter['failed'] += 1
                    jobcounter['failed_idlist'].append(jobid)
                else:
                    finishtagfile = "%s/%s"%(rstdir, "runjob.finish")
                    failtagfile = "%s/%s"%(rstdir, "runjob.failed")
                    starttagfile = "%s/%s"%(rstdir, "runjob.start")
                    if not os.path.exists(rstdir):
                        jobcounter['nojobfolder'] += 1
                        jobcounter['nojobfolder_idlist'].append(jobid)
                    elif os.path.exists(failtagfile):
                        jobcounter['failed'] += 1
                        jobcounter['failed_idlist'].append(jobid)
                    elif os.path.exists(finishtagfile):
                        jobcounter['finished'] += 1
                        jobcounter['finished_idlist'].append(jobid)
                    elif os.path.exists(starttagfile):
                        jobcounter['running'] += 1
                        jobcounter['running_idlist'].append(jobid)
                    else:
                        jobcounter['queued'] += 1
                        jobcounter['queued_idlist'].append(jobid)
            lines = hdl.readlines()
        hdl.close()
    return jobcounter
#}}}
def SendEmail_on_finish(jobid, base_www_url, finish_status, name_server, from_email, to_email, contact_email, logfile="", errfile=""):# {{{
    """Send notification email to the user for the web-server, the name
    of the web-server is specified by the var 'name_server'
    """
    err_msg = ""
    if os.path.exists(errfile):
        err_msg = myfunc.ReadFile(errfile)

    subject = "Your result for %s JOBID=%s"%(name_server, jobid)
    if finish_status == "success":
        bodytext = """
Your result is ready at %s/pred/result/%s

Thanks for using %s

    """%(base_www_url, jobid, name_server)
    elif finish_status == "failed":
        bodytext="""
We are sorry that your job with jobid %s is failed.

Please contact %s if you have any questions.

Attached below is the error message:
%s
        """%(jobid, contact_email, err_msg)
    else:
        bodytext="""
Your result is ready at %s/pred/result/%s

We are sorry that %s failed to predict some sequences of your job.

Please re-submit the queries that have been failed.

If you have any further questions, please contact %s.

Attached below is the error message:
%s
        """%(base_www_url, jobid, name_server, contact_email, err_msg)

    date_str = time.strftime(FORMAT_DATETIME)
    msg =  "Sendmail %s -> %s, %s"%(from_email, to_email, subject)
    myfunc.WriteFile("[%s] %s\n"% (date_str, msg), logfile, "a", True)
    rtValue = myfunc.Sendmail(from_email, to_email, subject, bodytext)
    if rtValue != 0:
        msg =  "Sendmail to {} failed with status {}".format(to_email, rtValue)
        myfunc.WriteFile("[%s] %s\n"%(date_str, msg), errfile, "a", True)
        return 1
    else:
        return 0
# }}}

def DeleteOldResult(path_result, path_log, logfile, MAX_KEEP_DAYS=180):#{{{
    """Delete jobdirs that are finished > MAX_KEEP_DAYS
    """
    finishedjoblogfile = "%s/finished_job.log"%(path_log)
    finished_job_dict = myfunc.ReadFinishedJobLog(finishedjoblogfile)
    for jobid in finished_job_dict:
        li = finished_job_dict[jobid]
        try:
            finish_date_str = li[8]
        except IndexError:
            finish_date_str = ""
            pass
        if finish_date_str != "":
            isValidFinishDate = True
            try:
                finish_date = datetime_str_to_time(finish_date_str)
            except ValueError:
                isValidFinishDate = False

            if isValidFinishDate:
                current_time = datetime.now(timezone(TZ))
                timeDiff = current_time - finish_date
                if timeDiff.days > MAX_KEEP_DAYS:
                    rstdir = "%s/%s"%(path_result, jobid)
                    date_str = time.strftime(FORMAT_DATETIME)
                    msg = "\tjobid = %s finished %d days ago (>%d days), delete."%(jobid, timeDiff.days, MAX_KEEP_DAYS)
                    myfunc.WriteFile("[%s] "%(date_str)+ msg + "\n", logfile, "a", True)
                    shutil.rmtree(rstdir)
#}}}
def CleanServerFile(logfile, errfile):#{{{
    """Clean old files on the server"""
# clean tmp files
    msg = "CleanServerFile..."
    date_str = time.strftime(FORMAT_DATETIME)
    myfunc.WriteFile("[%s] %s\n"%(date_str, msg), logfile, "a", True)
    cmd = ["bash", "%s/clean_server_file.sh"%(rundir)]
    RunCmd(cmd, logfile, errfile)
#}}}
def CleanJobFolder_TOPCONS2(rstdir):# {{{
    """Clean the jobfolder for TOPCONS2 after finishing"""
    flist =[
            "%s/remotequeue_seqindex.txt"%(rstdir),
            "%s/torun_seqindex.txt"%(rstdir)
            ]
    for f in flist:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass
# }}}
def CleanJobFolder_PRODRES(rstdir):# {{{
    """Clean the jobfolder for PRODRES after finishing"""
    flist =[
            "%s/remotequeue_seqindex.txt"%(rstdir),
            "%s/torun_seqindex.txt"%(rstdir)
            ]
    for f in flist:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass
# }}}
def loginfo(msg, outfile):# {{{
    """Write loginfo to outfile, appending current time"""
    date_str = time.strftime(FORMAT_DATETIME)
    myfunc.WriteFile("[%s] %s\n"%(date_str, msg), outfile, "a", True)
# }}}
