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
import datetime
import tabulate
import time
def WriteSubconsTextResultFile(outfile, outpath_result, maplist,#{{{
        runtime_in_sec, base_www_url, statfile=""):
    try:
        fpout = open(outfile, "w")
        if statfile != "":
            fpstat = open(statfile, "w")

        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print >> fpout, "##############################################################################"
        print >> fpout, "Subcons result file"
        print >> fpout, "Generated from %s at %s"%(base_www_url, date)
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

        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print >> fpout, "##############################################################################"
        print >> fpout, "TOPCONS2 result file"
        print >> fpout, "Generated from %s at %s"%(base_www_url, date)
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

    except IOError:
        print "Failed to write to file %s"%(outfile)
#}}}
def WriteProQ3TextResultFile(outfile, query_para, modelFileList, #{{{
        runtime_in_sec, base_www_url, proq3opt, statfile=""):
    try:
        fpout = open(outfile, "w")

        try:
            method_quality = query_para['method_quality']
        except KeyError:
            method_quality = 'sscore'

        fpstat = None
        numTMPro = 0

        if statfile != "":
            fpstat = open(statfile, "w")
        numModel = len(modelFileList)

        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print >> fpout, "##############################################################################"
        print >> fpout, "# ProQ3 result file"
        print >> fpout, "# Generated from %s at %s"%(base_www_url, date)
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
            localscorefile = "%s.proq3.%s.local"%(modelfile, method_quality)
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
    try:
        fpin = open(infile, "r")
        lines = fpin.read().split("\n")
        fpin.close()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line[0] == "P":
                keys = line.split()
            elif line[0].isdigit():
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

    return proq3opt

#}}}
def WriteDateTimeTagFile(outfile, g_params):# {{{
    datetime = time.strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(outfile):
        rt_msg = myfunc.WriteFile(datetime, outfile)
        if rt_msg:
            datetime = time.strftime("%Y-%m-%d %H:%M:%S")
            g_params['runjob_err'].append("[%s] %s"%(datetime, rt_msg))
# }}}
