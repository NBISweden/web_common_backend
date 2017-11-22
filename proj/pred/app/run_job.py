#!/usr/bin/env python
# Description: run job for the backend. result will not be cached
import os
import sys
import subprocess
import time
import myfunc
import webserver_common
import glob
import hashlib
import shutil
import datetime
import site
import fcntl
import json

progname =  os.path.basename(sys.argv[0])
wspace = ''.join([" "]*len(progname))
rundir = os.path.dirname(os.path.realpath(__file__))
webserver_root = os.path.realpath("%s/../../../"%(rundir))
activate_env="%s/env/bin/activate_this.py"%(webserver_root)
execfile(activate_env, dict(__file__=activate_env))

site.addsitedir("%s/env/lib/python2.7/site-packages/"%(webserver_root))
sys.path.append("/usr/local/lib/python2.7/dist-packages")

basedir = os.path.realpath("%s/.."%(rundir)) # path of the application, i.e. pred/
path_md5cache = "%s/static/md5"%(basedir)
path_cache = "%s/static/result/cache"%(basedir)
path_result = "%s/static/result/"%(basedir)
gen_errfile = "%s/static/log/%s.err"%(basedir, progname)
gen_logfile = "%s/static/log/%s.log"%(basedir, progname)

contact_email = "nanjiang.shu@scilifelab.se"
vip_email_file = "%s/config/vip_email.txt"%(basedir)
# note that here the url should be without http://

usage_short="""
Usage: %s seqfile_in_fasta 
       %s -jobid JOBID -outpath DIR -tmpdir DIR
       %s -email EMAIL -baseurl BASE_WWW_URL
       %s -only-get-cache
"""%(progname, wspace, wspace, wspace)

usage_ext="""\
Description:
    run job

OPTIONS:
  -h, --help        Print this help message and exit

Created 2016-12-01, 2017-05-26, Nanjiang Shu
"""
usage_exp="""
Examples:
    %s /data3/tmp/tmp_dkgSD/query.fa -outpath /data3/result/rst_mXLDGD -tmpdir /data3/tmp/tmp_dkgSD
"""%(progname)

def PrintHelp(fpout=sys.stdout):#{{{
    print >> fpout, usage_short
    print >> fpout, usage_ext
    print >> fpout, usage_exp#}}}

def CleanResult(name_software, query_para, outpath_this_seq):#{{{
    if name_software in ["prodres", "docker_prodres"]:
        if not 'isKeepTempFile' in query_para or query_para['isKeepTempFile'] == False:
            temp_result_folder = "%s/temp"%(outpath_this_seq)
            if os.path.exists(temp_result_folder):
                try:
                    shutil.rmtree(temp_result_folder)
                except:
                    g_params['runjob_err'].append("Failed to delete the folder %s"%(temp_result_folder)+"\n")

            flist = [
                    "%s/outputs/%s"%(outpath_this_seq, "Alignment.txt"),
                    "%s/outputs/%s"%(outpath_this_seq, "tableOut.txt"),
                    "%s/outputs/%s"%(outpath_this_seq, "fullOut.txt")
                    ]
            for f in flist:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        g_params['runjob_err'].append("Failed to delete the file %s"%(f)+"\n")
#}}}
def GetCommand(name_software, seqfile_this_seq, tmp_outpath_result, tmp_outpath_this_seq, query_para):#{{{
    """Return the command for subprocess
    """

    try:
        docker_tmp_outpath_result = os.sep + os.sep.join(tmp_outpath_result.split(os.sep)[tmp_outpath_result.split(os.sep).index("static"):])
        docker_seqfile_this_seq = os.sep + os.sep.join(seqfile_this_seq.split(os.sep)[seqfile_this_seq.split(os.sep).index("static"):])
        docker_tmp_outpath_this_seq = os.sep + os.sep.join(tmp_outpath_this_seq.split(os.sep)[tmp_outpath_this_seq.split(os.sep).index("static"):])
    except:
        raise

    cmd = []
    if name_software in ['dummy']:
        runscript = "%s/%s"%(rundir, "soft/dummyrun.sh")
        cmd = ["bash", runscript, seqfile_this_seq,  tmp_outpath_this_seq]
    elif name_software in ['scampi2-single']:
        if not os.path.exists(tmp_outpath_this_seq):
            os.makedirs(tmp_outpath_this_seq)
        runscript = "%s/%s"%(rundir, "soft/scampi2/bin/scampi/SCAMPI_run.pl")
        outtopfile = "%s/query.top"%(tmp_outpath_this_seq)
        cmd = [runscript, seqfile_this_seq,  outtopfile]
    elif name_software in ['scampi2-msa']:
        if not os.path.exists(tmp_outpath_this_seq):
            os.makedirs(tmp_outpath_this_seq)
        runscript = "%s/%s"%(rundir, 
                "soft/scampi2/bin/scampi-msa/run_SCAMPI_multi.pl")
        outtopfile = "%s/query.top"%(tmp_outpath_this_seq)
        blastdir = "%s/%s"%(rundir, "soft/blast/blast-2.2.26")
        os.environ['BLASTMAT'] = "%s/data"%(blastdir)
        os.environ['BLASTBIN'] = "%s/bin"%(blastdir)
        os.environ['BLASTDB'] = "%s/%s"%(rundir, "soft/blastdb")
        blastdb = "%s/%s"%(os.environ['BLASTDB'], "uniref90.fasta" )
        cmd = [runscript, seqfile_this_seq, outtopfile, blastdir, blastdb]
    elif name_software in ['topcons2']:
        runscript = "%s/%s"%(rundir, 
                "soft/topcons2_webserver/workflow/pfam_workflow.py")
        blastdir = "%s/%s"%(rundir, "soft/blast/blast-2.2.26")
        os.environ['BLASTMAT'] = "%s/data"%(blastdir)
        os.environ['BLASTBIN'] = "%s/bin"%(blastdir)
        os.environ['BLASTDB'] = "%s/%s"%(rundir, "soft/blastdb")
        blastdb = "%s/%s"%(os.environ['BLASTDB'], "uniref90.fasta" )
        cmd = ["python", runscript, seqfile_this_seq,  tmp_outpath_result, blastdir, blastdb]
    elif name_software in ['subcons']:
        runscript = "%s/%s"%(rundir, "soft/subcons/master_subcons.sh")
        cmd = ["bash", runscript, seqfile_this_seq,  tmp_outpath_this_seq,
                "-verbose"]
    elif name_software in ['docker_subcons']:
        containerID = 'subcons'
        cmd =  ["/usr/bin/docker", "exec", containerID, 
                "script", "/dev/null", "-c", 
                "cd %s; /home/app/subcons/master_subcons.sh %s %s"%(
                    docker_tmp_outpath_result, docker_seqfile_this_seq,
                    docker_tmp_outpath_this_seq)]
    elif name_software in ['prodres']:#{{{
        runscript = "%s/%s"%(rundir, "soft/PRODRES/PRODRES/PRODRES.py")
        path_pfamscan = "%s/misc/PfamScan"%(webserver_root)
        path_pfamdatabase = "%s/soft/PRODRES/databases"%(rundir)
        path_pfamscanscript = "%s/pfam_scan.pl"%(path_pfamscan)
        blastdb = "%s/soft/PRODRES/databases/blastdb/uniref90.fasta"%(rundir)
        if 'PERL5LIB' not in os.environ:
            os.environ['PERL5LIB'] = ""
        os.environ['PERL5LIB'] = os.environ['PERL5LIB'] + ":" + path_pfamscan

        cmd = ["python", runscript, "--input", seqfile_this_seq, "--output",
                tmp_outpath_this_seq, "--pfam-dir", path_pfamdatabase,
                "--pfamscan-script", path_pfamscanscript, "--fallback-db-fasta",
                blastdb]

        if 'second_method' in query_para and query_para['second_method'] != "":
            cmd += ['--second-search', query_para['second_method']]

        if 'pfamscan_evalue' in query_para and query_para['pfamscan_evalue'] != "":
            cmd += ['--pfamscan_e-val', query_para['pfamscan_evalue']]
        elif ('pfamscan_bitscore' in query_para and
                query_para['pfamscan_bitscore'] != ""):
            cmd += ['--pfamscan_bitscore', query_para['pfamscan_bitscore']]

        if 'pfamscan_clanoverlap' in query_para:
            if query_para['pfamscan_clanoverlap'] == False:
                cmd += ['--pfamscan_clan-overlap', 'no']
            else:
                cmd += ['--pfamscan_clan-overlap', 'yes']

        if ('jackhmmer_iteration' in query_para and
                query_para['jackhmmer_iteration'] != ""):
            cmd += ['--jackhmmer_max_iter', query_para['jackhmmer_iteration']]

        if ('jackhmmer_threshold_type' in query_para and
                query_para['jackhmmer_threshold_type'] != ""):
            cmd += ['--jackhmmer-threshold-type',
                    query_para['jackhmmer_threshold_type']]

        if 'jackhmmer_evalue' in query_para and query_para['jackhmmer_evalue'] != "":
            cmd += ['--jackhmmer_e-val', query_para['jackhmmer_evalue']]
        elif ('jackhmmer_bitscore' in query_para and
                query_para['jackhmmer_bitscore'] != ""):
            cmd += ['--jackhmmer_bit-score', query_para['jackhmmer_bitscore']]

        if ('psiblast_iteration' in query_para and
                query_para['psiblast_iteration'] != ""):
            cmd += ['--psiblast_iter', query_para['psiblast_iteration']]
        if 'psiblast_outfmt' in query_para and query_para['psiblast_outfmt'] != "":
            cmd += ['--psiblast_outfmt', query_para['psiblast_outfmt']]
#}}}

    return cmd

#}}}
def RunJob(infile, outpath, tmpdir, email, jobid, g_params):#{{{
    all_begin_time = time.time()

    rootname = os.path.basename(os.path.splitext(infile)[0])
    starttagfile   = "%s/runjob.start"%(outpath)
    runjob_errfile = "%s/runjob.err"%(outpath)
    runjob_logfile = "%s/runjob.log"%(outpath)
    app_logfile = "%s/app.log"%(outpath)
    finishtagfile = "%s/runjob.finish"%(outpath)
    query_parafile = "%s/query.para.txt"%(outpath)
    failtagfile = "%s/runjob.failed"%(outpath)

    query_para = {}
    content = myfunc.ReadFile(query_parafile)
    if content != "":
        query_para = json.loads(content)

    rmsg = ""

    try:
        name_software = query_para['name_software']
    except KeyError:
        name_software = ""



    resultpathname = jobid

    outpath_result = "%s/%s"%(outpath, resultpathname)
    tmp_outpath_result = "%s/%s"%(tmpdir, resultpathname)

    zipfile = "%s.zip"%(resultpathname)
    zipfile_fullpath = "%s.zip"%(outpath_result)
    resultfile_text = "%s/%s"%(outpath_result, "query.result.txt")
    finished_seq_file = "%s/finished_seqs.txt"%(outpath_result)

    for folder in [outpath_result, tmp_outpath_result]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except:
                datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                msg = "[%s] Failed to delete folder %s"%(datetime, folder)
                myfunc.WriteFile(msg+"\n", gen_errfile, "a")
                rt_msg = myfunc.WriteFile(datetime, failtagfile)
                if rt_msg:
                    g_params['runjob_err'].append("[%s] %s"%(datetime, rt_msg))
                return 1

        try:
            os.makedirs(folder)
        except OSError:
            datetime = time.strftime("%Y-%m-%d %H:%M:%S")
            msg = "[%s] Failed to create folder %s"%(datetime, folder)
            myfunc.WriteFile(msg+"\n", gen_errfile, "a")
            rt_msg = myfunc.WriteFile(datetime, failtagfile)
            if rt_msg:
                g_params['runjob_err'].append("[%s] %s"%(datetime, rt_msg))
            return 1

    try:
        open(finished_seq_file, 'w').close()
    except:
        pass

    (seqIDList , seqAnnoList, seqList) = myfunc.ReadFasta(infile)

    for ii in  xrange(len(seqIDList)):
        origIndex = ii
        seq = seqList[ii]
        seqid = seqIDList[ii]
        description = seqAnnoList[ii]

        subfoldername_this_seq = "seq_%d"%(origIndex)
        outpath_this_seq = "%s/%s"%(outpath_result, subfoldername_this_seq)
        tmp_outpath_this_seq = "%s/%s"%(tmp_outpath_result, "seq_%d"%(0))
        if os.path.exists(tmp_outpath_this_seq):
            try:
                shutil.rmtree(tmp_outpath_this_seq)
            except OSError:
                pass

        seqfile_this_seq = "%s/%s"%(tmp_outpath_result, "query_%d.fa"%(origIndex))
        seqcontent = ">query_%d\n%s\n"%(origIndex, seq)
        myfunc.WriteFile(seqcontent, seqfile_this_seq, "w")

        if not os.path.exists(seqfile_this_seq):
            g_params['runjob_err'].append("failed to generate seq index %d"%(origIndex))
            continue


        cmd = GetCommand(name_software, seqfile_this_seq, tmp_outpath_result, tmp_outpath_this_seq, query_para)
        if len(cmd) < 1:
            datetime = time.strftime("%Y-%m-%d %H:%M:%S")
            g_params['runjob_err'].append("[%s] empty cmd for name_software = %s"%(datetime, name_software))
            pass


        cmdline = " ".join(cmd)
        g_params['runjob_log'].append(" ".join(cmd))
        begin_time = time.time()
        try:
            rmsg = subprocess.check_output(cmd)
            g_params['runjob_log'].append("workflow:\n"+rmsg+"\n")
        except subprocess.CalledProcessError, e:
            g_params['runjob_err'].append(str(e)+"\n")
            g_params['runjob_err'].append("cmdline: "+ cmdline +"\n")
            g_params['runjob_err'].append(rmsg + "\n")
            pass
        end_time = time.time()
        runtime_in_sec = end_time - begin_time

        aaseqfile = "%s/seq.fa"%(tmp_outpath_this_seq)
        if not os.path.exists(aaseqfile):
            seqcontent = ">%s\n%s\n"%(description, seq)
            myfunc.WriteFile(seqcontent, aaseqfile, "w")
        timefile = "%s/time.txt"%(tmp_outpath_this_seq)
        if not os.path.exists(timefile):
            myfunc.WriteFile("%s;%f\n"%(seqid,runtime_in_sec), timefile, "w")


        if os.path.exists(tmp_outpath_this_seq):
            cmd = ["mv","-f", tmp_outpath_this_seq, outpath_this_seq]
            isCmdSuccess = False
            try:
                subprocess.check_output(cmd)
                isCmdSuccess = True
            except subprocess.CalledProcessError, e:
                datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                msg =  "[%s] Failed to run prediction for sequence No. %d\n"%(datetime, origIndex)
                g_params['runjob_err'].append(msg)
                g_params['runjob_err'].append(str(e)+"\n")
                pass


            CleanResult(name_software, query_para, outpath_this_seq)

            if isCmdSuccess:
                runtime = runtime_in_sec #in seconds
                timefile = "%s/time.txt"%(outpath_this_seq)
                if os.path.exists(timefile):
                    content = myfunc.ReadFile(timefile).split("\n")[0]
                    strs = content.split(";")
                    try:
                        runtime = "%.1f"%(float(strs[1]))
                    except:
                        pass
                extItem1 = None
                extItem2 = None
                info_finish = [ "seq_%d"%origIndex, str(len(seq)), 
                        str(extItem1), str(extItem2),
                        "newrun", str(runtime), description]
                myfunc.WriteFile("\t".join(info_finish)+"\n",
                        finished_seq_file, "a", isFlush=True)
                # now write the text output for this seq

                info_this_seq = "%s\t%d\t%s\t%s"%("seq_%d"%origIndex, len(seq), description, seq)
                resultfile_text_this_seq = "%s/%s"%(outpath_this_seq, "query.result.txt")
                webserver_common.WriteTextResultFile(name_software, resultfile_text_this_seq,
                        outpath_result,
                        [info_this_seq], runtime_in_sec,
                        g_params['base_www_url'])

    all_end_time = time.time()
    all_runtime_in_sec = all_end_time - all_begin_time

    if len(g_params['runjob_log']) > 0 :
        rt_msg = myfunc.WriteFile("\n".join(g_params['runjob_log'])+"\n", runjob_logfile, "a")
        if rt_msg:
            g_params['runjob_err'].append(rt_msg)


    # now write the text output to a single file
    statfile = "%s/%s"%(outpath_result, "stat.txt")
    os.chdir(outpath)
    cmd = ["zip", "-rq", zipfile, resultpathname]
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError, e:
        g_params['runjob_err'].append(str(e))
        pass

    # write finish tag file
    datetime = time.strftime("%Y-%m-%d %H:%M:%S")
    if os.path.exists(finished_seq_file):
        rt_msg = myfunc.WriteFile(datetime, finishtagfile)
        if rt_msg:
            datetime = time.strftime("%Y-%m-%d %H:%M:%S")
            g_params['runjob_err'].append("[%s] %s"%(datetime, rt_msg))

    isSuccess = False
    if (os.path.exists(finishtagfile) and os.path.exists(zipfile_fullpath)):
        isSuccess = True
    else:
        isSuccess = False
        datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        rt_msg = myfunc.WriteFile(datetime, failtagfile)
        if rt_msg:
            g_params['runjob_err'].append("[%s] %s"%(datetime, rt_msg))

    if g_params['runjob_err'] == []:
        try:
            datetime = time.strftime("%Y-%m-%d %H:%M:%S")
            g_params['runjob_log'].append("[%s] shutil.rmtree(%s)"% (datetime, tmpdir))
            shutil.rmtree(tmpdir)
        except:
            g_params['runjob_err'].append("[%s] Failed to delete tmpdir %s"%(datetime, tmpdir))
    if len(g_params['runjob_err']) > 0:
        rt_msg = myfunc.WriteFile("\n".join(g_params['runjob_err'])+"\n", runjob_errfile, "w")
        return 1
    return 0
#}}}
def main(g_params):#{{{
    argv = sys.argv
    numArgv = len(argv)
    if numArgv < 2:
        PrintHelp()
        return 1

    outpath = ""
    infile = ""
    tmpdir = ""
    email = ""
    jobid = ""

    i = 1
    isNonOptionArg=False
    while i < numArgv:
        if isNonOptionArg == True:
            infile = argv[i]
            isNonOptionArg = False
            i += 1
        elif argv[i] == "--":
            isNonOptionArg = True
            i += 1
        elif argv[i][0] == "-":
            if argv[i] in ["-h", "--help"]:
                PrintHelp()
                return 1
            elif argv[i] in ["-outpath", "--outpath"]:
                (outpath, i) = myfunc.my_getopt_str(argv, i)
            elif argv[i] in ["-tmpdir", "--tmpdir"] :
                (tmpdir, i) = myfunc.my_getopt_str(argv, i)
            elif argv[i] in ["-jobid", "--jobid"] :
                (jobid, i) = myfunc.my_getopt_str(argv, i)
            elif argv[i] in ["-baseurl", "--baseurl"] :
                (g_params['base_www_url'], i) = myfunc.my_getopt_str(argv, i)
            elif argv[i] in ["-email", "--email"] :
                (email, i) = myfunc.my_getopt_str(argv, i)
            elif argv[i] in ["-q", "--q"]:
                g_params['isQuiet'] = True
                i += 1
            else:
                print >> sys.stderr, "Error! Wrong argument:", argv[i]
                return 1
        else:
            infile = argv[i]
            i += 1

    if jobid == "":
        print >> sys.stderr, "%s: jobid not set. exit"%(sys.argv[0])
        return 1

    g_params['jobid'] = jobid
    # create a lock file in the resultpath when run_job.py is running for this
    # job, so that daemon will not run on this folder
    lockname = "runjob.lock"
    lock_file = "%s/%s/%s"%(path_result, jobid, lockname)
    g_params['lockfile'] = lock_file
    fp = open(lock_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print >> sys.stderr, "Another instance of %s is running"%(progname)
        return 1


    if myfunc.checkfile(infile, "infile") != 0:
        return 1
    if outpath == "":
        print >> sys.stderr, "outpath not set. exit"
        return 1
    elif not os.path.exists(outpath):
        try:
            subprocess.check_output(["mkdir", "-p", outpath])
        except subprocess.CalledProcessError, e:
            print >> sys.stderr, e
            return 1
    if tmpdir == "":
        print >> sys.stderr, "tmpdir not set. exit"
        return 1
    elif not os.path.exists(tmpdir):
        try:
            subprocess.check_output(["mkdir", "-p", tmpdir])
        except subprocess.CalledProcessError, e:
            print >> sys.stderr, e
            return 1

    if os.path.exists(vip_email_file):
        g_params['vip_user_list'] = myfunc.ReadIDList(vip_email_file)

    numseq = myfunc.CountFastaSeq(infile)
    g_params['debugfile'] = "%s/debug.log"%(outpath)
    return RunJob(infile, outpath, tmpdir, email, jobid, g_params)

#}}}

def InitGlobalParameter():#{{{
    g_params = {}
    g_params['isQuiet'] = True
    g_params['runjob_log'] = []
    g_params['runjob_err'] = []
    g_params['base_www_url'] = ""
    g_params['jobid'] = ""
    g_params['lockfile'] = ""
    g_params['vip_user_list'] = []
    return g_params
#}}}
if __name__ == '__main__' :
    g_params = InitGlobalParameter()
    status = main(g_params)
    if os.path.exists(g_params['lockfile']):
        try:
            os.remove(g_params['lockfile'])
        except:
            myfunc.WriteFile("Failed to delete lockfile %s\n"%(g_params['lockfile']), gen_errfile, "a", True)

    sys.exit(status)
