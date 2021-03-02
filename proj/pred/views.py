import os
import sys
import tempfile
import re
import subprocess
from datetime import datetime
from dateutil import parser as dtparser
from pytz import timezone
import time
import math
import shutil
import json
import logging

# for dealing with IP address and country names
from geoip import geolite2
import pycountry

#import models for spyne
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.views.decorators.csrf import csrf_exempt  
from spyne.error import ResourceNotFoundError, ResourceAlreadyExistsError
from spyne.server.django import DjangoApplication
from spyne.model.primitive import Unicode, Integer
from spyne.model.complex import Iterable
from spyne.service import ServiceBase
from spyne.protocol.soap import Soap11
from spyne.application import Application
from spyne.decorator import rpc
from spyne.util.django import DjangoComplexModel, DjangoServiceBase
from spyne.server.wsgi import WsgiApplication

# for user authentication
from django.contrib.auth import authenticate, login, logout

# import variables from settings
from django.conf import settings

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
progname =  os.path.basename(__file__)
rootname_progname = os.path.splitext(progname)[0]
path_app = "%s/app"%(SITE_ROOT)
sys.path.append(path_app)
path_log = "%s/static/log"%(SITE_ROOT)
path_stat = "%s/stat"%(path_log)
path_result = "%s/static/result"%(SITE_ROOT)
path_tmp = "%s/static/tmp"%(SITE_ROOT)
path_md5 = "%s/static/md5"%(SITE_ROOT)
path_static = "%s/static"%(SITE_ROOT)
python_exec = "python"

from libpredweb import myfunc
from libpredweb import webserver_common as webcom

TZ = webcom.TZ
os.environ['TZ'] = TZ
time.tzset()

g_params = {}
# global parameters
g_params['BASEURL'] = "/pred/";
g_params['MAXSIZE_UPLOAD_FILE_IN_MB'] = 10
g_params['MIN_LEN_SEQ'] = 10      # minimum length of the query sequence
g_params['MAX_LEN_SEQ'] = 10000   # maximum length of the query sequence
g_params['MAX_DAYS_TO_SHOW'] = 30
g_params['BIG_NUMBER'] = 100000
g_params['MAX_NUMSEQ_FOR_FORCE_RUN'] = 100
g_params['MAX_NUMSEQ_PER_JOB'] = 100
g_params['AVERAGE_RUNTIME_PER_SEQ_IN_SEC'] = 120
g_params['MAX_ROWS_TO_SHOW_IN_TABLE'] = 2000
g_params['MAXSIZE_UPLOAD_FILE_IN_BYTE'] = g_params['MAXSIZE_UPLOAD_FILE_IN_MB'] * 1024*1024
g_params['FORMAT_DATETIME'] = webcom.FORMAT_DATETIME
g_params['STATIC_URL'] = settings.STATIC_URL
g_params['SUPER_USER_LIST'] = settings.SUPER_USER_LIST
g_params['path_static'] = path_static
g_params['path_stat'] = path_stat
g_params['SITE_ROOT'] = SITE_ROOT
g_params['path_result'] = path_result
g_params['MAX_ACTIVE_USER'] = 10
g_params['MAX_ALLOWD_NUMSEQ'] = 10


suq_basedir = "/tmp"
rundir = SITE_ROOT
suq_exec = "/usr/bin/suq";

qd_fe_scriptfile = "%s/qd_fe.py"%(path_app)
gen_errfile = "%s/static/log/%s.err"%(SITE_ROOT, progname)

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.views.static import serve


#from pred.models import Query
from proj.pred.models import SubmissionForm
from proj.pred.models import FieldContainer
from django.template import Context, loader


def index(request):#{{{
    if not os.path.exists(path_result):
        os.mkdir(path_result, 0o755)
    if not os.path.exists(path_result):
        os.mkdir(path_tmp, 0o755)
    if not os.path.exists(path_md5):
        os.mkdir(path_md5, 0o755)
    base_www_url_file = "%s/static/log/base_www_url.txt"%(SITE_ROOT)
    if not os.path.exists(base_www_url_file):
        base_www_url = webcom.get_url_scheme(request) + request.META['HTTP_HOST']
        myfunc.WriteFile(base_www_url, base_www_url_file, "w", True)

    # read the local config file if exists
    configfile = "%s/config/config.json"%(SITE_ROOT)
    config = {}
    if os.path.exists(configfile):
        text = myfunc.ReadFile(configfile)
        config = json.loads(text)

    if rootname_progname in config:
        g_params.update(config[rootname_progname])
        g_params['MAXSIZE_UPLOAD_FILE_IN_BYTE'] = g_params['MAXSIZE_UPLOAD_FILE_IN_MB'] * 1024*1024

    return submit_seq(request)
#}}}
def login(request):#{{{
    #logout(request)
    info = {}
    webcom.set_basic_config(request, info, g_params)
    info['jobcounter'] = webcom.GetJobCounter(info)
    return render(request, 'pred/login.html', info)
#}}}
def submit_seq(request):#{{{
    info = {}
    webcom.set_basic_config(request, info, g_params)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = SubmissionForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # redirect to a new URL:

            jobname = request.POST['jobname']
            email = request.POST['email']
            rawseq = request.POST['rawseq'] + "\n" # force add a new line
            isForceRun = False
            isKeepTempFile = False

            for tup in form.second_method_choices:
                if tup[0] == second_method:
                    second_method = tup[1]
                    break

            if 'pfamscan_clanoverlap' in request.POST:
                pfamscan_clanoverlap = True
            if 'forcerun' in request.POST:
                isForceRun = True
            if 'keeptmpfile' in request.POST:
                isKeepTempFile = True

            try:
                seqfile = request.FILES['seqfile']
            except KeyError as MultiValueDictKeyError:
                seqfile = ""
            date_str = time.strftime(g_params['FORMAT_DATETIME'])
            query = {}
            query['rawseq'] = rawseq
            query['seqfile'] = seqfile
            query['email'] = email
            query['jobname'] = jobname
            query['date'] = date_str
            query['client_ip'] = info['client_ip']
            query['errinfo'] = ""
            query['method_submission'] = "web"
            query['isForceRun'] = isForceRun
            query['isKeepTempFile'] = isKeepTempFile
            query['username'] = username

            is_valid_parameter = True
            if 'name_software' in query_para and query_para['name_software'] in ['prodres', 'docker_prodres']:
                is_valid_parameter = webcom.ValidateParameter_PRODRES(query)

            is_valid_query = False
            if is_valid_parameter:
                is_valid_query = webcom.ValidateQuery(request, query, g_params)


            if is_valid_parameter and is_valid_query:
                jobid = RunQuery(request, query)

                # type of method_submission can be web or wsdl
                #date, jobid, IP, numseq, size, jobname, email, method_submission
                log_record = "%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\n"%(query['date'], jobid,
                        query['client_ip'], query['numseq'],
                        len(query['rawseq']),query['jobname'], query['email'],
                        query['method_submission'])
                main_logfile_query = "%s/%s/%s"%(SITE_ROOT, "static/log", "submitted_seq.log")
                myfunc.WriteFile(log_record, main_logfile_query, "a")

                divided_logfile_query =  "%s/%s/%s"%(SITE_ROOT,
                        "static/log/divided", "%s_submitted_seq.log"%(query['client_ip']))
                divided_logfile_finished_jobid =  "%s/%s/%s"%(SITE_ROOT,
                        "static/log/divided", "%s_finished_job.log"%(query['client_ip']))
                if query['client_ip'] != "":
                    myfunc.WriteFile(log_record, divided_logfile_query, "a")


                file_seq_warning = "%s/%s/%s/%s"%(SITE_ROOT, "static/result", jobid, "query.warn.txt")
                query['file_seq_warning'] = os.path.basename(file_seq_warning)
                if query['warninfo'] != "":
                    myfunc.WriteFile(query['warninfo'], file_seq_warning, "a")

                query['jobid'] = jobid
                query['raw_query_seqfile'] = "query.raw.fa"
                query['BASEURL'] = g_params['BASEURL']

                # start the qd_fe if not, in the background
#                 cmd = [qd_fe_scriptfile]

                base_www_url = webcom.get_url_scheme(request) + request.META['HTTP_HOST']
                if webcom.IsFrontEndNode(base_www_url): #run the daemon only at the frontend
                    cmd = "nohup %s %s &"%(python_exec, qd_fe_scriptfile)
                    os.system(cmd)

                if query['numseq'] < 0: #go to result page anyway
                    query['jobcounter'] = webcom.GetJobCounter(info)
                    return render(request, 'pred/thanks.html', query)
                else:
                    return get_results(request, jobid)

            else:
                query['jobcounter'] = webcom.GetJobCounter(info)
                return render(request, 'pred/badquery.html', query)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = SubmissionForm()

    jobcounter = webcom.GetJobCounter(info)
    info['form'] = form
    info['jobcounter'] = jobcounter
    info['MAX_ALLOWD_NUMSEQ'] = g_params['MAX_ALLOWD_NUMSEQ']
    return render(request, 'pred/submit_seq.html', info)
#}}}

def RunQuery(request, query):#{{{
    errmsg = []
    tmpdir = tempfile.mkdtemp(prefix="%s/static/tmp/tmp_"%(SITE_ROOT))
    rstdir = tempfile.mkdtemp(prefix="%s/static/result/rst_"%(SITE_ROOT))
    os.chmod(tmpdir, 0o755)
    os.chmod(rstdir, 0o755)
    jobid = os.path.basename(rstdir)
    query['jobid'] = jobid

# write files for the query
    jobinfofile = "%s/jobinfo"%(rstdir)
    rawseqfile = "%s/query.raw.fa"%(rstdir)
    seqfile_t = "%s/query.fa"%(tmpdir)
    seqfile_r = "%s/query.fa"%(rstdir)
    warnfile = "%s/warn.txt"%(tmpdir)
    logfile = "%s/runjob.log"%(rstdir)

    query_para = {}
    for item in ['pfamscan_bitscore', 'pfamscan_evalue','pfamscan_clanoverlap','jackhmmer_threshold_type', 'jackhmmer_evalue','jackhmmer_bitscore', 'jackhmmer_iteration', 'psiblast_evalue', 'psiblast_iteration', 'psiblast_outfmt', 'second_method', 'isKeepTempFile']:
        if item in query:
            query_para[item] = query[item]

    query_parafile = "%s/query.para.txt"%(rstdir)

    myfunc.WriteFile("tmpdir = %s\n"%(tmpdir), logfile, "a")

    jobinfo_str = "%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\n"%(query['date'], jobid,
            query['client_ip'], query['numseq'],
            len(query['rawseq']),query['jobname'], query['email'],
            query['method_submission'])
    errmsg.append(myfunc.WriteFile(jobinfo_str, jobinfofile, "w"))
    errmsg.append(myfunc.WriteFile(query['rawseq'], rawseqfile, "w"))
    errmsg.append(myfunc.WriteFile(query['filtered_seq'], seqfile_t, "w"))
    errmsg.append(myfunc.WriteFile(query['filtered_seq'], seqfile_r, "w"))

    errmsg.append(myfunc.WriteFile(json.dumps(query_para, sort_keys=True), query_parafile, "w"))

    base_www_url = webcom.get_url_scheme(request) + request.META['HTTP_HOST']
    query['base_www_url'] = base_www_url


    # for single sequence job submitted via web interface, submit to local
    # queue
    if query['numseq'] <= 1: #single sequence jobs submitted via web interface queued in the front-end server
        query['numseq_this_user'] = 1
        SubmitQueryToLocalQueue(query, tmpdir, rstdir, isOnlyGetCache=False)
    else: #all other jobs are submitted to the frontend with isOnlyGetCache=True
        query['numseq_this_user'] = 1
        SubmitQueryToLocalQueue(query, tmpdir, rstdir, isOnlyGetCache=True)

    forceruntagfile = "%s/forcerun"%(rstdir)
    if query['isForceRun']:
        myfunc.WriteFile("", forceruntagfile)
    return jobid
#}}}
def RunQuery_wsdl_local(rawseq, filtered_seq, seqinfo):#{{{
# submit the wsdl job to the local queue
    errmsg = []
    tmpdir = tempfile.mkdtemp(prefix="%s/static/tmp/tmp_"%(SITE_ROOT))
    rstdir = tempfile.mkdtemp(prefix="%s/static/result/rst_"%(SITE_ROOT))
    os.chmod(tmpdir, 0o755)
    os.chmod(rstdir, 0o755)
    jobid = os.path.basename(rstdir)
    seqinfo['jobid'] = jobid
    numseq = seqinfo['numseq']
    para_str = seqinfo['para_str']

# write files for the query
    jobinfofile = "%s/jobinfo"%(rstdir)
    rawseqfile = "%s/query.raw.fa"%(rstdir)
    seqfile_t = "%s/query.fa"%(tmpdir)
    seqfile_r = "%s/query.fa"%(rstdir)
    query_parafile = "%s/query.para.txt"%(rstdir)
    warnfile = "%s/warn.txt"%(tmpdir)
    jobinfo_str = "%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\n"%(seqinfo['date'], jobid,
            seqinfo['client_ip'], seqinfo['numseq'],
            len(rawseq),seqinfo['jobname'], seqinfo['email'],
            seqinfo['method_submission'])
    errmsg.append(myfunc.WriteFile(jobinfo_str, jobinfofile, "w"))
    errmsg.append(myfunc.WriteFile(rawseq, rawseqfile, "w"))
    errmsg.append(myfunc.WriteFile(para_str, query_parafile, "w"))
    errmsg.append(myfunc.WriteFile(filtered_seq, seqfile_t, "w"))
    errmsg.append(myfunc.WriteFile(filtered_seq, seqfile_r, "w"))
    base_www_url = seqinfo['url_scheme'] + seqinfo['hostname']
    seqinfo['base_www_url'] = base_www_url

    rtvalue = SubmitQueryToLocalQueue(seqinfo, tmpdir, rstdir, isOnlyGetCache=False)
    if rtvalue != 0:
        return "None"
    else:
        return jobid
#}}}
def SubmitQueryToLocalQueue(query, tmpdir, rstdir, isOnlyGetCache=False):#{{{
    scriptfile = "%s/app/submit_job_to_queue.py"%(SITE_ROOT)
    rstdir = "%s/%s"%(path_result, query['jobid'])
    runjob_errfile = "%s/runjob.err"%(rstdir)
    debugfile = "%s/debug.log"%(rstdir) #this log only for debugging
    runjob_logfile = "%s/runjob.log"%(rstdir)
    failedtagfile = "%s/%s"%(rstdir, "runjob.failed")
    rmsg = ""

    cmd = [python_exec, scriptfile, "-nseq", "%d"%query['numseq'], "-nseq-this-user",
            "%d"%query['numseq_this_user'], "-jobid", query['jobid'],
            "-outpath", rstdir, "-datapath", tmpdir, "-baseurl",
            query['base_www_url'] ]
    if query['email'] != "":
        cmd += ["-email", query['email']]
    if query['client_ip'] != "":
        cmd += ["-host", query['client_ip']]
    if query['isForceRun']:
        cmd += ["-force"]
    if isOnlyGetCache:
        cmd += ["-only-get-cache"]

    (isSuccess, t_runtime) = webcom.RunCmd(cmd, runjob_logfile, runjob_errfile)
    if not isSuccess:
        webcom.WriteDateTimeTagFile(failedtagfile, runjob_logfile, runjob_errfile)
        return 1
    else:
        return 0
#}}}

def thanks(request):#{{{
    #print "request.POST at thanks:", request.POST
    return HttpResponse("Thanks")
#}}}

def get_queue(request):# {{{
    info = webcom.get_queue(request, g_params)
    return render(request, 'pred/queue.html', info)
# }}}
def get_running(request):# {{{
    info = webcom.get_running(request, g_params)
    return render(request, 'pred/running.html', info)
# }}}
def get_finished_job(request):# {{{
    info = webcom.get_finished_job(request, g_params)
    return render(request, 'pred/finished_job.html', info)
# }}}
def get_failed_job(request):# {{{
    info = webcom.get_failed_job(request, g_params)
    return render(request, 'pred/failed_job.html', info)
# }}}

def get_countjob_country(request):# {{{
    info = webcom.get_countjob_country(request, g_params)
    return render(request, 'pred/countjob_country.html', info)
# }}}
def get_help(request):# {{{
    info = webcom.get_help(request, g_params)
    return render(request, 'pred/help.html', info)
# }}}
def get_news(request):# {{{
    info = webcom.get_news(request, g_params)
    return render(request, 'pred/news.html', info)
# }}}
def help_wsdl_api(request):# {{{
    g_params['api_script_rtname'] =  "subcons_wsdl"
    info = webcom.help_wsdl_api(request, g_params)
    return render(request, 'pred/help_wsdl_api.html', info)
# }}}

def get_reference(request):#{{{
    info = {}
    webcom.set_basic_config(request, info, g_params)
    info['jobcounter'] = webcom.GetJobCounter(info)
    return render(request, 'pred/reference.html', info)
#}}}
def get_example(request):#{{{
    info = {}
    webcom.set_basic_config(request, info, g_params)
    info['jobcounter'] = webcom.GetJobCounter(info)
    return render(request, 'pred/example.html', info)
#}}}

def get_serverstatus(request):# {{{
    g_params['isShowLocalQueue'] = False
    info = webcom.get_serverstatus(request, g_params)
    return render(request, 'pred/serverstatus.html', info)
# }}}
def download(request):#{{{
    info = {}
    webcom.set_basic_config(request, info, g_params)
    info['jobcounter'] = webcom.GetJobCounter(info)
    return render(request, 'pred/download.html', info)
#}}}

def get_results(request, jobid="1"):#{{{
    resultdict = {}
    webcom.set_basic_config(request, resultdict, g_params)

    #img1 = "%s/%s/%s/%s"%(SITE_ROOT, "result", jobid, "PconsC2.s400.jpg")
    #url_img1 =  serve(request, os.path.basename(img1), os.path.dirname(img1))
    rstdir = "%s/%s"%(path_result, jobid)
    outpathname = jobid
    resultfile = "%s/%s/%s/%s"%(rstdir, jobid, outpathname, "query.result.txt")
    tarball = "%s/%s.tar.gz"%(rstdir, outpathname)
    zipfile = "%s/%s.zip"%(rstdir, outpathname)
    starttagfile = "%s/%s"%(rstdir, "runjob.start")
    finishtagfile = "%s/%s"%(rstdir, "runjob.finish")
    failtagfile = "%s/%s"%(rstdir, "runjob.failed")
    errfile = "%s/%s"%(rstdir, "runjob.err")
    query_seqfile = "%s/%s"%(rstdir, "query.fa")
    raw_query_seqfile = "%s/%s"%(rstdir, "query.raw.fa")
    seqid_index_mapfile = "%s/%s/%s"%(rstdir,jobid, "seqid_index_map.txt")
    finished_seq_file = "%s/%s/finished_seqs.txt"%(rstdir, jobid)
    statfile = "%s/%s/stat.txt"%(rstdir, jobid)
    method_submission = "web"

    jobinfofile = "%s/jobinfo"%(rstdir)
    jobinfo = myfunc.ReadFile(jobinfofile).strip()
    jobinfolist = jobinfo.split("\t")
    if len(jobinfolist) >= 8:
        submit_date_str = jobinfolist[0]
        numseq = int(jobinfolist[3])
        jobname = jobinfolist[5]
        email = jobinfolist[6]
        method_submission = jobinfolist[7]
    else:
        submit_date_str = ""
        numseq = 1
        jobname = ""
        email = ""
        method_submission = "web"

    isValidSubmitDate = True
    try:
        submit_date = webcom.datetime_str_to_time(submit_date_str)
    except ValueError:
        isValidSubmitDate = False
    current_time = datetime.now(timezone(TZ))

    resultdict['isResultFolderExist'] = True
    resultdict['errinfo'] = ""
    if os.path.exists(errfile):
        resultdict['errinfo'] = myfunc.ReadFile(errfile)

    status = ""
    queuetime = ""
    runtime = ""
    queuetime_in_sec = 0
    runtime_in_sec = 0
    if not os.path.exists(rstdir):
        resultdict['isResultFolderExist'] = False
        resultdict['isFinished'] = False
        resultdict['isFailed'] = True
        resultdict['isStarted'] = False
    elif os.path.exists(failtagfile):
        resultdict['isFinished'] = False
        resultdict['isFailed'] = True
        resultdict['isStarted'] = True
        status = "Failed"
        start_date_str = ""
        if os.path.exists(starttagfile):
            start_date_str = myfunc.ReadFile(starttagfile).strip()
        isValidStartDate = True
        isValidFailedDate = True
        try:
            start_date = webcom.datetime_str_to_time(start_date_str)
        except ValueError:
            isValidStartDate = False
        failed_date_str = myfunc.ReadFile(failtagfile).strip()
        try:
            failed_date = webcom.datetime_str_to_time(failed_date_str)
        except ValueError:
            isValidFailedDate = False
        if isValidSubmitDate and isValidStartDate:
            queuetime = myfunc.date_diff(submit_date, start_date)
            queuetime_in_sec = (start_date - submit_date).total_seconds()
        if isValidStartDate and isValidFailedDate:
            runtime = myfunc.date_diff(start_date, failed_date)
            runtime_in_sec = (failed_date - start_date).total_seconds()
    else:
        resultdict['isFailed'] = False
        if os.path.exists(finishtagfile):
            resultdict['isFinished'] = True
            resultdict['isStarted'] = True
            status = "Finished"
            isValidStartDate = True
            isValidFinishDate = True
            if os.path.exists(starttagfile):
                start_date_str = myfunc.ReadFile(starttagfile).strip()
            else:
                start_date_str = ""
            try:
                start_date = webcom.datetime_str_to_time(start_date_str)
            except ValueError:
                isValidStartDate = False
            finish_date_str = myfunc.ReadFile(finishtagfile).strip()
            try:
                finish_date = webcom.datetime_str_to_time(finish_date_str)
            except ValueError:
                isValidFinishDate = False
            if isValidSubmitDate and isValidStartDate:
                queuetime = myfunc.date_diff(submit_date, start_date)
                queuetime_in_sec = (start_date - submit_date).total_seconds()
            if isValidStartDate and isValidFinishDate:
                runtime = myfunc.date_diff(start_date, finish_date)
                runtime_in_sec = (finish_date - start_date).total_seconds()
        else:
            resultdict['isFinished'] = False
            if os.path.exists(starttagfile):
                isValidStartDate = True
                start_date_str = ""
                if os.path.exists(starttagfile):
                    start_date_str = myfunc.ReadFile(starttagfile).strip()
                try:
                    start_date = webcom.datetime_str_to_time(start_date_str)
                except ValueError:
                    isValidStartDate = False
                resultdict['isStarted'] = True
                status = "Running"
                if isValidSubmitDate and isValidStartDate:
                    queuetime = myfunc.date_diff(submit_date, start_date)
                    queuetime_in_sec = (start_date - submit_date).total_seconds()
                if isValidStartDate:
                    runtime = myfunc.date_diff(start_date, current_time)
                    runtime_in_sec = (current_time - start_date).total_seconds()
            else:
                resultdict['isStarted'] = False
                status = "Wait"
                if isValidSubmitDate:
                    queuetime = myfunc.date_diff(submit_date, current_time)
                    queuetime_in_sec = (current_time - submit_date).total_seconds()

    color_status = webcom.SetColorStatus(status)

    file_seq_warning = "%s/%s/%s/%s"%(SITE_ROOT, "static/result", jobid, "query.warn.txt")
    seqwarninfo = ""
    if os.path.exists(file_seq_warning):
        seqwarninfo = myfunc.ReadFile(file_seq_warning)
        seqwarninfo = seqwarninfo.strip()

    resultdict['file_seq_warning'] = os.path.basename(file_seq_warning)
    resultdict['seqwarninfo'] = seqwarninfo
    resultdict['jobid'] = jobid
    resultdict['subdirname'] = "seq_0"
    resultdict['jobname'] = jobname
    resultdict['outpathname'] = os.path.basename(outpathname)
    resultdict['resultfile'] = os.path.basename(resultfile)
    resultdict['tarball'] = os.path.basename(tarball)
    resultdict['zipfile'] = os.path.basename(zipfile)
    resultdict['submit_date'] = submit_date_str
    resultdict['queuetime'] = queuetime
    resultdict['runtime'] = runtime
    resultdict['BASEURL'] = g_params['BASEURL']
    resultdict['status'] = status
    resultdict['color_status'] = color_status
    resultdict['numseq'] = numseq
    resultdict['query_seqfile'] = os.path.basename(query_seqfile)
    resultdict['raw_query_seqfile'] = os.path.basename(raw_query_seqfile)
    base_www_url = "http://" + request.META['HTTP_HOST']
#   note that here one must add http:// in front of the url
    resultdict['url_result'] = "%s/pred/result/%s"%(base_www_url, jobid)

    sum_run_time = 0.0
    average_run_time = float(g_params['AVERAGE_RUNTIME_PER_SEQ_IN_SEC'])  # default average_run_time
    num_finished = 0
    cntnewrun = 0
    cntcached = 0
    newrun_table_list = [] # this is used for calculating the remaining time
# get seqid_index_map
    if os.path.exists(finished_seq_file):
        resultdict['index_table_header'] = ["No.", "Length", "LOC_DEF", "LOC_DEF_SCORE",
                "RunTime(s)", "SequenceName", "Source", "FinishDate" ]
        index_table_content_list = []
        indexmap_content = myfunc.ReadFile(finished_seq_file).split("\n")
        cnt = 0
        for line in indexmap_content:
            strs = line.split("\t")
            if len(strs)>=7:
                subfolder = strs[0]
                length_str = strs[1]
                loc_def_str = strs[2]
                loc_def_score_str = strs[3]
                source = strs[4]
                try:
                    finishdate = strs[7]
                except IndexError:
                    finishdate = "N/A"

                try:
                    runtime_in_sec_str = "%.1f"%(float(strs[5]))
                    if source == "newrun":
                        sum_run_time += float(strs[5])
                        cntnewrun += 1
                    elif source == "cached":
                        cntcached += 1
                except:
                    runtime_in_sec_str = ""
                desp = strs[6]
                rank = "%d"%(cnt+1)
                if cnt < g_params['MAX_ROWS_TO_SHOW_IN_TABLE']:
                    index_table_content_list.append([rank, length_str, loc_def_str,
                        loc_def_score_str, runtime_in_sec_str, desp[:30], subfolder, source, finishdate])
                if source == "newrun":
                    newrun_table_list.append([rank, subfolder])
                cnt += 1
        if cntnewrun > 0:
            average_run_time = sum_run_time / float(cntnewrun)

        resultdict['index_table_content_list'] = index_table_content_list
        resultdict['indexfiletype'] = "finishedfile"
        resultdict['num_finished'] = cnt
        num_finished = cnt
        resultdict['percent_finished'] = "%.1f"%(float(cnt)/numseq*100)
    else:
        resultdict['index_table_header'] = []
        resultdict['index_table_content_list'] = []
        resultdict['indexfiletype'] = "finishedfile"
        resultdict['num_finished'] = 0
        resultdict['percent_finished'] = "%.1f"%(0.0)

    num_remain = numseq - num_finished
    time_remain_in_sec = num_remain * average_run_time # set default value

    # re-define runtime as the sum of all real running time 
    if sum_run_time > 0.0:
        resultdict['runtime'] = myfunc.second_to_human(int(sum_run_time+0.5))

    resultdict['num_row_result_table'] = len(resultdict['index_table_content_list'])

    # calculate the remaining time based on the average_runtime of the last x
    # number of newrun sequences

    avg_newrun_time = webcom.GetAverageNewRunTime(finished_seq_file, window=10)

    if cntnewrun > 0 and avg_newrun_time >= 0:
        time_remain_in_sec = int(avg_newrun_time*num_remain+0.5)

    time_remain = myfunc.second_to_human(int(time_remain_in_sec+0.5))
    resultdict['time_remain'] = time_remain
    qdinittagfile = "%s/runjob.qdinit"%(rstdir)

    if os.path.exists(rstdir):
        resultdict['isResultFolderExist'] = True
    else:
        resultdict['isResultFolderExist'] = False

    if numseq <= 1:
        resultdict['refresh_interval'] = webcom.GetRefreshInterval(
                queuetime_in_sec, runtime_in_sec, method_submission)
    else:
        if os.path.exists(qdinittagfile):
            addtime = int(math.sqrt(max(0,min(num_remain, num_finished))))+1
            resultdict['refresh_interval'] = average_run_time + addtime
        else:
            resultdict['refresh_interval'] = webcom.GetRefreshInterval(
                    queuetime_in_sec, runtime_in_sec, method_submission)

    # get stat info
    if os.path.exists(statfile):#{{{
        content = myfunc.ReadFile(statfile)
        lines = content.split("\n")
        for line in lines:
            strs = line.split()
            if len(strs) >= 2:
                resultdict[strs[0]] = strs[1]
                percent =  "%.1f"%(int(strs[1])/float(numseq)*100)
                newkey = strs[0].replace('num_', 'per_')
                resultdict[newkey] = percent
#}}}
    resultdict['MAX_ROWS_TO_SHOW_IN_TABLE'] = g_params['MAX_ROWS_TO_SHOW_IN_TABLE']
    resultdict['jobcounter'] = webcom.GetJobCounter(resultdict)
    return render(request, 'pred/get_results.html', resultdict)
#}}}
def get_results_eachseq(request, jobid="1", seqindex="1"):#{{{
    resultdict = {}
    webcom.set_basic_config(request, resultdict, g_params)

    rstdir = "%s/%s"%(path_result, jobid)
    outpathname = jobid

    jobinfofile = "%s/jobinfo"%(rstdir)
    jobinfo = myfunc.ReadFile(jobinfofile).strip()
    jobinfolist = jobinfo.split("\t")
    if len(jobinfolist) >= 8:
        submit_date_str = jobinfolist[0]
        numseq = int(jobinfolist[3])
        jobname = jobinfolist[5]
        email = jobinfolist[6]
        method_submission = jobinfolist[7]
    else:
        submit_date_str = ""
        numseq = 1
        jobname = ""
        email = ""
        method_submission = "web"

    status = ""

    resultdict['jobid'] = jobid
    resultdict['subdirname'] = seqindex
    resultdict['jobname'] = jobname
    resultdict['outpathname'] = os.path.basename(outpathname)
    resultdict['BASEURL'] = g_params['BASEURL']
    resultdict['status'] = status
    resultdict['numseq'] = numseq
    base_www_url = "http://" + request.META['HTTP_HOST']

    resultfile = "%s/%s/%s/%s"%(rstdir, outpathname, seqindex, "query.result.txt")
    htmlfigure_file =  "%s/%s/%s/plot/%s"%(rstdir, outpathname, seqindex, "query_0.html")
    if os.path.exists(htmlfigure_file):
        resultdict['htmlfigure'] = "%s/%s/%s/%s/plot/%s"%(
                "result", jobid, jobid, seqindex,
                os.path.basename(htmlfigure_file))
    else:
        resultdict['htmlfigure'] = ""

    if os.path.exists(rstdir):
        resultdict['isResultFolderExist'] = True
    else:
        resultdict['isResultFolderExist'] = False


    if os.path.exists(resultfile):
        resultdict['resultfile'] = os.path.basename(resultfile)
    else:
        resultdict['resultfile'] = ""

    resultdict['jobcounter'] = webcom.GetJobCounter(resultdict)
    return render(request, 'pred/get_results_eachseq.html', resultdict)
#}}}

# enabling wsdl service

#{{{ The actual wsdl api
class Container_submitseq(DjangoComplexModel):
    class Attributes(DjangoComplexModel.Attributes):
        django_model = FieldContainer
        django_exclude = ['excluded_field']


class Service_submitseq(ServiceBase):

    @rpc(Unicode,  Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Iterable(Unicode))
# submitted_remote will be called by the daemon
# sequences are submitted one by one by the daemon, but the numseq_of_job is
# for the number of sequences of the whole job submitted to the front end
# isforcerun is set as string, "true" or "false", case insensitive
    def submitjob_remote(ctx, seq="", para_str="", jobname="", email="",#{{{
            numseq_this_user="", isforcerun=""):
        logger = logging.getLogger(__name__)
        seq = seq + "\n" #force add a new line for correct parsing the fasta file

        seqinfo = {}
        query_para = json.loads(para_str)
        is_valid_parameter = True
        if query_para['name_software'] in ['prodres', 'docker_prodres']:
            is_valid_parameter = webcom.ValidateParameter_PRODRES(query_para)
        seqinfo.update(query_para)

        filtered_seq = ""
        if is_valid_parameter:
            filtered_seq = webcom.ValidateSeq(seq, seqinfo, g_params)

        if numseq_this_user != "" and numseq_this_user.isdigit():
            seqinfo['numseq_this_user'] = int(numseq_this_user)
        else:
            seqinfo['numseq_this_user'] = 1

        numseq_str = "%d"%(seqinfo['numseq'])
        warninfo = seqinfo['warninfo']
        if warninfo == "":
            warninfo = "None"
        jobid = "None"
        url = "None"
        if filtered_seq == "":
            errinfo = seqinfo['errinfo']
        else:
            soap_req = ctx.transport.req
            try:
                client_ip = soap_req.META['REMOTE_ADDR']
            except:
                client_ip = ""


            try:
                hostname = soap_req.META['HTTP_HOST']
            except:
                hostname = ""

            url_scheme = webcom.get_url_scheme(soap_req)
            seqinfo['jobname'] = jobname
            seqinfo['email'] = email
            seqinfo['para_str'] = para_str
            seqinfo['date'] = time.strftime(g_params['FORMAT_DATETIME'])
            seqinfo['client_ip'] = client_ip
            seqinfo['hostname'] = hostname
            seqinfo['method_submission'] = "wsdl"
            seqinfo['url_scheme'] = url_scheme
            # for this method, wsdl is called only by the daemon script, isForceRun can be
            # set by the argument
            if isforcerun.upper()[:1] == "T":
                seqinfo['isForceRun'] = True
            else:
                seqinfo['isForceRun'] = False
            jobid = RunQuery_wsdl_local(seq, filtered_seq, seqinfo)
            if jobid == "None":
                errinfo = "Failed to submit your job to the queue\n"+seqinfo['errinfo']
            else:
                log_record = "%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\n"%(seqinfo['date'], jobid,
                        seqinfo['client_ip'], seqinfo['numseq'],
                        len(seq),seqinfo['jobname'], seqinfo['email'],
                        seqinfo['method_submission'])
                main_logfile_query = "%s/%s/%s"%(SITE_ROOT, "static/log", "submitted_seq.log")
                myfunc.WriteFile(log_record, main_logfile_query, "a")

                divided_logfile_query =  "%s/%s/%s"%(SITE_ROOT, "static/log/divided",
                        "%s_submitted_seq.log"%(seqinfo['client_ip']))
                if seqinfo['client_ip'] != "":
                    myfunc.WriteFile(log_record, divided_logfile_query, "a")

                url = url_scheme + hostname +   g_params['BASEURL'] + "result/%s"%(jobid)

                file_seq_warning = "%s/%s/%s/%s"%(SITE_ROOT, "static/result", jobid, "query.warn.txt")
                if seqinfo['warninfo'] != "":
                    myfunc.WriteFile(seqinfo['warninfo'], file_seq_warning, "a")
                errinfo = seqinfo['errinfo']

        for s in [jobid, url, numseq_str, errinfo, warninfo]:
            yield s
#}}}

    @rpc(Unicode, _returns=Iterable(Unicode))
    def checkjob(ctx, jobid=""):#{{{
        logger = logging.getLogger(__name__)
        rstdir = "%s/%s"%(path_result, jobid)
        soap_req = ctx.transport.req

        url_scheme = webcom.get_url_scheme(soap_req)
        hostname = soap_req.META['HTTP_HOST']
        result_url = url_scheme + hostname + "/static/" + "result/%s/%s.zip"%(jobid, jobid)
        status = "None"
        url = ""
        errinfo = ""
        if not os.path.exists(rstdir):
            status = "None"
            errinfo = "Error! jobid %s does not exist."%(jobid)
        else:
            starttagfile = "%s/%s"%(rstdir, "runjob.start")
            finishtagfile = "%s/%s"%(rstdir, "runjob.finish")
            failtagfile = "%s/%s"%(rstdir, "runjob.failed")
            runjob_errfile = "%s/%s"%(rstdir, "runjob.err")
            if os.path.exists(failtagfile):
                status = "Failed"
                errinfo = ""
                if os.path.exists(runjob_errfile):
                    errinfo = myfunc.ReadFile(runjob_errfile)
            elif os.path.exists(finishtagfile):
                status = "Finished"
                url = result_url
                errinfo = ""
            elif os.path.exists(starttagfile):
                status = "Running"
            else:
                status = "Wait"
        for s in [status, url, errinfo]:
            yield s
#}}}
    @rpc(Unicode, _returns=Iterable(Unicode))
    def deletejob(ctx, jobid=""):#{{{
        rstdir = "%s/%s"%(path_result, jobid)
        status = "None"
        errinfo = ""
        try: 
            shutil.rmtree(rstdir)
            status = "Succeeded"
        except OSError as e:
            errinfo = str(e)
            status = "Failed"
        for s in [status, errinfo]:
            yield s
#}}}

class ContainerService_submitseq(ServiceBase):
    @rpc(Integer, _returns=Container_submitseq)
    def get_container(ctx, pk):
        try:
            return FieldContainer.objects.get(pk=pk)
        except FieldContainer.DoesNotExist:
            raise ResourceNotFoundError('Container_submitseq')

    @rpc(Container_submitseq, _returns=Container_submitseq)
    def create_container(ctx, container):
        try:
            return FieldContainer.objects.create(**container.as_dict())
        except IntegrityError:
            raise ResourceAlreadyExistsError('Container_submitseq')

class ExceptionHandlingService_submitseq(DjangoServiceBase):
    """Service for testing exception handling."""

    @rpc(_returns=Container_submitseq)
    def raise_does_not_exist(ctx):
        return FieldContainer.objects.get(pk=-1)

    @rpc(_returns=Container_submitseq)
    def raise_validation_error(ctx):
        raise ValidationError('Is not valid.')


app_submitseq = Application([Service_submitseq, ContainerService_submitseq,
    ExceptionHandlingService_submitseq], 'commonbackend.bioinfo.se',
    in_protocol=Soap11(validator='soft'), out_protocol=Soap11())
#wsgi_app_submitseq = WsgiApplication(app_submitseq)

submitseq_service = csrf_exempt(DjangoApplication(app_submitseq))

#}}}
