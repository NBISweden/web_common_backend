#!/usr/bin/env python
# Description: run job for the backend. result will not be cached
import os
import sys
import subprocess
import myfunc
import webserver_common as webcom
import glob
import hashlib
import shutil
from datetime import datetime
from dateutil import parser as dtparser
from pytz import timezone
import time
import site
import fcntl
import json
import urllib

FORMAT_DATETIME = webcom.FORMAT_DATETIME
TZ = webcom.TZ

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

def CleanResult(name_software, query_para, outpath_this_seq, runjob_logfile, runjob_errfile):#{{{
    date_str = time.strftime(FORMAT_DATETIME)
    if name_software in ["prodres", "docker_prodres"]:
        if not 'isKeepTempFile' in query_para or query_para['isKeepTempFile'] == False:
            temp_result_folder = "%s/temp"%(outpath_this_seq)
            if os.path.exists(temp_result_folder):
                try:
                    shutil.rmtree(temp_result_folder)
                except Exception as e:
                    msg = "Failed to delete the folder %s with message \"%s\""%(temp_result_folder, str(e))
                    myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)

            flist = [
                    "%s/outputs/%s"%(outpath_this_seq, "Alignment.txt"),
                    "%s/outputs/%s"%(outpath_this_seq, "tableOut.txt"),
                    "%s/outputs/%s"%(outpath_this_seq, "fullOut.txt")
                    ]
            for f in flist:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        msg =  "Failed to delete the file %s with message \"%s\""%(f, str(e))
                        myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
    elif name_software in ["subcons", "docker_subcons"]:
        if not 'isKeepTempFile' in query_para or query_para['isKeepTempFile'] == False:
            temp_result_folder = "%s/tmp"%(outpath_this_seq)
            if os.path.exists(temp_result_folder):
                try:
                    shutil.rmtree(temp_result_folder)
                except Exception as e:
                    msg = "Failed to delete the folder %s with message \"%s\""%(
                            temp_result_folder, str(e))
                    myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)

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
        cmd =  ["/usr/bin/docker", "exec", "--user", "user", containerID, 
                "script", "/dev/null", "-c", 
                "cd %s; export HOME=/home/user; /app/subcons/master_subcons.sh %s %s"%(
                    docker_tmp_outpath_result, docker_seqfile_this_seq,
                    docker_tmp_outpath_this_seq)]

    elif name_software in ['docker_pathopred']:
        if not os.path.exists(tmp_outpath_this_seq):
            os.makedirs(tmp_outpath_this_seq)
        variant_text = query_para['variants']
        variant_file = "%s/variants.fa" % tmp_outpath_result
        myfunc.WriteFile(variant_text, variant_file)
        docker_variant_file = os.sep + os.sep.join(variant_file.split(os.sep)[variant_file.split(os.sep).index("static"):])
        identifier_name = query_para['identifier_name']
        containerID = 'pathopred'
        cmd =  ["docker", "exec", "--user", "user", containerID, 
                "script", "/dev/null", "-c", 
                "cd %s; export HOME=/home/user; /app/pathopred/master_pathopred.sh %s %s %s %s"%(
                    docker_tmp_outpath_result, docker_seqfile_this_seq, 
                    docker_variant_file, docker_tmp_outpath_this_seq, identifier_name)]

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
def RunJob_proq3(modelfile, targetseq, outpath, tmpdir, email, jobid, query_para, g_params):# {{{
    all_begin_time = time.time()
    rootname = os.path.basename(os.path.splitext(modelfile)[0])
    starttagfile   = "%s/runjob.start"%(outpath)
    runjob_errfile = "%s/runjob.err"%(outpath)
    runjob_logfile = "%s/runjob.log"%(outpath)
    app_logfile = "%s/app.log"%(outpath)
    finishtagfile = "%s/runjob.finish"%(outpath)
    failtagfile = "%s/runjob.failed"%(outpath)
    rmsg = ""

    try:
        method_quality = query_para['method_quality']
    except KeyError:
        method_quality = 'sscore'

    try:
        isDeepLearning = query_para['isDeepLearning']
    except KeyError:
        isDeepLearning = True

    if isDeepLearning:
        m_str = "proq3d"
    else:
        m_str = "proq3"

    try:
        name_software = query_para['name_software']
    except KeyError:
        name_software = ""

    resultpathname = jobid

    outpath_result = "%s/%s"%(outpath, resultpathname)
    tmp_outpath_result = "%s/%s"%(tmpdir, resultpathname)

    zipfile = "%s.zip"%(resultpathname)
    zipfile_fullpath = "%s.zip"%(outpath_result)
    resultfile_text = "%s/%s"%(outpath_result, "query.proq3.txt")
    finished_model_file = "%s/finished_models.txt"%(outpath_result)

    for folder in [tmp_outpath_result]:
        date_str = time.strftime(FORMAT_DATETIME)
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                msg = "Failed to delete folder %s with message %s"%(folder, str(e))
                myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
                webcom.WriteDateTimeTagFile(failtagfile, runjob_logfile, runjob_errfile)
                return 1

        try:
            os.makedirs(folder)
        except Exception as e:
            msg = "Failed to create folder %s with return message \"%s\""%(folder, str(e))
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
            webcom.WriteDateTimeTagFile(failtagfile, runjob_logfile, runjob_errfile)
            return 1

    tmp_outpath_this_model = "%s/%s"%(tmp_outpath_result, "model_%d"%(0))
    outpath_this_model = "%s/%s"%(outpath_result, "model_%d"%(0))

    # First try to retrieve the profile from archive
    isGetProfileSuccess = False# {{{
    if 'url_profile' in query_para:
        date_str = time.strftime(FORMAT_DATETIME)
        # try to retrieve the profile
        url_profile = query_para['url_profile']
        remote_id = os.path.splitext(os.path.basename(url_profile))[0]
        outfile_zip = "%s/%s.zip"%(tmp_outpath_result, remote_id)

        msg = "Trying to retrieve profile from %s"%(url_profile)
        myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_logfile, "a", True)

        isRetrieveSuccess = False
        if myfunc.IsURLExist(url_profile,timeout=5):
            try: 
                urllib.urlretrieve (url_profile, outfile_zip)
                isRetrieveSuccess = True 
            except Exception as e:
                msg = "Failed to retrieve profile from  %s. Err = %s"%(url_profile, e)
                myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_logfile, "a", True)
                pass
        if os.path.exists(outfile_zip) and isRetrieveSuccess:
            msg = "Retrieved profile from %s"%(url_profile)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_logfile, "a", True)
            cmd = ["unzip", outfile_zip, "-d", tmp_outpath_result]
            try:
                subprocess.check_output(cmd)
                try:
                    os.rename("%s/%s"%(tmp_outpath_result, remote_id), 
                            "%s/profile_0"%(tmp_outpath_result))
                    isGetProfileSuccess = True
                    try:
                        os.remove(outfile_zip)
                    except:
                        pass
                except:
                    pass
            except:
                pass 
# }}}

    tmp_seqfile = "%s/query.fasta"%(tmp_outpath_result)
    tmp_outpath_profile = "%s/profile_0"%(tmp_outpath_result)

    docker_tmp_seqfile = os.sep + os.sep.join(tmp_seqfile.split(os.sep)[tmp_seqfile.split(os.sep).index("static"):])
    docker_modelfile= os.sep + os.sep.join(modelfile.split(os.sep)[modelfile.split(os.sep).index("static"):])
    docker_tmp_outpath_profile = os.sep + os.sep.join(tmp_outpath_profile.split(os.sep)[tmp_outpath_profile.split(os.sep).index("static"):])
    docker_tmp_outpath_this_model = os.sep + os.sep.join(tmp_outpath_this_model.split(os.sep)[tmp_outpath_this_model.split(os.sep).index("static"):])
    docker_tmp_outpath_result = os.sep + os.sep.join(tmp_outpath_result.split(os.sep)[tmp_outpath_result.split(os.sep).index("static"):])

    timefile = "%s/time.txt"%(tmp_outpath_result)
    runtime_in_sec_profile = -1.0
    runtime_in_sec_model = -1.0


    if name_software in ['docker_proq3']:
        myfunc.WriteFile(">query\n%s\n"%(targetseq), tmp_seqfile)

        containerID = 'proq3'
        if not isGetProfileSuccess:
            # try to generate profile
            cmd =  ["/usr/bin/docker", "exec", "--user", "user", containerID, 
                "script", "/dev/null", "-c", 
                "cd %s; export HOME=/home/user; /app/proq3/run_proq3.sh -fasta %s -outpath %s -only-build-profile"%(
                    docker_tmp_outpath_result, docker_tmp_seqfile,
                    docker_tmp_outpath_profile)]
            runtime_in_sec = webcom.RunCmd(cmd, runjob_logfile, runjob_errfile)
            myfunc.WriteFile("%s;%f\n"%("profile_0",runtime_in_sec), timefile, "a", True)
            runtime_in_sec_profile = runtime_in_sec

        # then run with the pre-created profile
        proq3opt = webcom.GetProQ3Option(query_para)
        cmd =  ["/usr/bin/docker", "exec",  "--user", "user", containerID, 
            "script", "/dev/null", "-c", 
            "cd %s; export HOME=/home/user; /app/proq3/run_proq3.sh --profile %s %s -outpath %s -verbose %s"%(
                docker_tmp_outpath_result, "%s/query.fasta"%(docker_tmp_outpath_profile),
                docker_modelfile, docker_tmp_outpath_this_model, " ".join(proq3opt))]
        runtime_in_sec = webcom.RunCmd(cmd, runjob_logfile, runjob_errfile)
        cmdline = " ".join(cmd)
        msg = "cmdline: %s"%(cmdline)
        myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_logfile, "a", True)

        myfunc.WriteFile("%s;%f\n"%("model_0",runtime_in_sec), timefile, "a", True)
        runtime_in_sec_model = runtime_in_sec

    if os.path.exists(tmp_outpath_result):
        cmd = ["mv","-f", tmp_outpath_result, outpath_result]
        isCmdSuccess = False
        try:
            subprocess.check_output(cmd)
            isCmdSuccess = True
        except subprocess.CalledProcessError, e:
            date_str = time.strftime(FORMAT_DATETIME)
            msg =  "Failed to run proq3 for this model with message \"%s\""%(str(e))
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
            pass
        # copy time.txt to within the model folder
        shutil.copyfile("%s/time.txt"%(outpath_result), "%s/model_0/time.txt"%(outpath_result))

        CleanResult(name_software, query_para, outpath_result, runjob_logfile, runjob_errfile)

        if isCmdSuccess:
            globalscorefile = "%s/%s.%s.%s.global"%(outpath_this_model,  "query.pdb", m_str, method_quality)
            (globalscore, itemList) = webcom.ReadProQ3GlobalScore(globalscorefile)
            modelseqfile = "%s/%s.fasta"%(outpath_this_model, "query.pdb")
            modellength = myfunc.GetSingleFastaLength(modelseqfile)

            modelinfo = ["model_0", str(modellength), str(runtime_in_sec_model)]
            if globalscore:
                for i in xrange(len(itemList)):
                    modelinfo.append(str(globalscore[itemList[i]]))
            myfunc.WriteFile("\t".join(modelinfo)+"\n", finished_model_file, "a")
            modelFileList = ["%s/%s"%(outpath_this_model, "query.pdb")]
            webcom.WriteProQ3TextResultFile(resultfile_text, query_para, modelFileList,
                    runtime_in_sec_model, g_params['base_www_url'], proq3opt, statfile="")

    # make the zip file for all result
    os.chdir(outpath)
    cmd = ["zip", "-rq", zipfile, resultpathname]
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError, e:
        date_str = time.strftime(FORMAT_DATETIME)
        msg = "Failed to run zip for %s with message \"%s\""%(resultpathname, str(e))
        myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
        pass

    # write finish tag file
    webcom.WriteDateTimeTagFile(finishtagfile, runjob_logfile, runjob_errfile)

    isSuccess = False
    if (os.path.exists(finishtagfile) and os.path.exists(zipfile_fullpath)):
        isSuccess = True
    else:
        isSuccess = False
        webcom.WriteDateTimeTagFile(failtagfile, runjob_logfile, runjob_errfile)

    if os.path.exists(runjob_errfile) and os.stat(runjob_errfile).st_size > 0:
        try:
            date_str = time.strftime(FORMAT_DATETIME)
            msg =  "shutil.rmtree(%s)"%(tmpdir)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_logfile, "a", True)
            shutil.rmtree(tmpdir)
        except Exception as e:
            msg =  "Failed to delete tmpdir %s with message \"%s\""%(tmpdir, str(e))
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
        return 1
    return 0

# }}}
def RunJob(infile, outpath, tmpdir, email, jobid, query_para, g_params):#{{{
    all_begin_time = time.time()

    rootname = os.path.basename(os.path.splitext(infile)[0])
    starttagfile   = "%s/runjob.start"%(outpath)
    runjob_errfile = "%s/runjob.err"%(outpath)
    runjob_logfile = "%s/runjob.log"%(outpath)
    app_logfile = "%s/app.log"%(outpath)
    finishtagfile = "%s/runjob.finish"%(outpath)
    failtagfile = "%s/runjob.failed"%(outpath)

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

    date_str = time.strftime(FORMAT_DATETIME)
    for folder in [outpath_result, tmp_outpath_result]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                msg = "Failed to delete folder %s with message %s"%(folder, str(e))
                myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
                webcom.WriteDateTimeTagFile(failtagfile, runjob_logfile, runjob_errfile)
                return 1

        try:
            os.makedirs(folder)
        except Exception as e:
            msg = "Failed to create folder %s with message %s"%(folder, str(e))
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
            webcom.WriteDateTimeTagFile(failtagfile, runjob_logfile, runjob_errfile)
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
            date_str = time.strftime(FORMAT_DATETIME)
            msg = "Failed to generate seq index %d"%(origIndex)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
            continue


        cmd  = GetCommand(name_software, seqfile_this_seq, tmp_outpath_result, tmp_outpath_this_seq, query_para)
        if len(cmd) < 1:
            date_str = time.strftime(FORMAT_DATETIME)
            msg = "empty cmd for name_software = %s"%(name_software)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
            pass

        runtime_in_sec = webcom.RunCmd(cmd, runjob_logfile, runjob_errfile)

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
                date_str = time.strftime(FORMAT_DATETIME)
                msg =  "Failed to run prediction for sequence No. %d\n"%(origIndex)
                myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
                pass


            CleanResult(name_software, query_para, outpath_this_seq, runjob_logfile, runjob_errfile)

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
                webcom.WriteTextResultFile(name_software, resultfile_text_this_seq,
                        outpath_result,
                        [info_this_seq], runtime_in_sec,
                        g_params['base_www_url'])

    all_end_time = time.time()
    all_runtime_in_sec = all_end_time - all_begin_time

    # make the zip file for all result
    statfile = "%s/%s"%(outpath_result, "stat.txt")
    os.chdir(outpath)
    cmd = ["zip", "-rq", zipfile, resultpathname]
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError, e:
        date_str = time.strftime(FORMAT_DATETIME)
        msg = "Failed to run zip for %s with message \"%s\""%(resultpathname, str(e))
        myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
        pass

    # write finish tag file
    webcom.WriteDateTimeTagFile(finishtagfile, runjob_logfile, runjob_errfile)

    isSuccess = False
    if (os.path.exists(finishtagfile) and os.path.exists(zipfile_fullpath)):
        isSuccess = True
    else:
        isSuccess = False
        webcom.WriteDateTimeTagFile(failtagfile, runjob_logfile, runjob_errfile)

    # try to delete the tmpdir if there is no error
    if not (os.path.exists(runjob_errfile) and os.stat(runjob_errfile).st_size > 0):
        try:
            date_str = time.strftime(FORMAT_DATETIME)
            msg =  "shutil.rmtree(%s)"%(tmpdir)
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_logfile, "a", True)
            shutil.rmtree(tmpdir)
        except Exception as e:
            msg =  "Failed to delete tmpdir %s with message \"%s\""%(tmpdir, str(e))
            myfunc.WriteFile("[%s] %s\n"%(date_str, msg),  runjob_errfile, "a", True)
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


    query_parafile = "%s/query.para.txt"%(outpath)
    query_para = {}
    content = myfunc.ReadFile(query_parafile)
    if content != "":
        query_para = json.loads(content)
    try:
        name_software = query_para['name_software']
    except KeyError:
        name_software = ""

    status = 0

    if name_software in ["proq3", "docker_proq3"]:
        # for proq3, model is provided in query_para
        # provided in the query_para
        try:
            model = query_para['pdb_model']
        except:
            myfunc.WriteFile("key pdb_model is empty. Aborted.\n", gen_errfile, "a", True)
            return 1
        modelfile = "%s/query.pdb"%(outpath)
        myfunc.WriteFile(model, modelfile)
        try:
            targetseq = query_para['targetseq']
        except:
            seqList = myfunc.PDB2Seq(modelfile)
            if len(seqList) >= 1:
                targetseq = seqList[0]
        print "Run proq3"
        status =  RunJob_proq3(modelfile, targetseq, outpath, tmpdir, email, jobid, query_para, g_params)
    else:
        status =  RunJob(infile, outpath, tmpdir, email, jobid, query_para, g_params)

    return status
#}}}

def InitGlobalParameter():#{{{
    g_params = {}
    g_params['isQuiet'] = True
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
