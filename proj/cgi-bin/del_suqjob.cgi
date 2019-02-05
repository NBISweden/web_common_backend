#!/usr/bin/perl -w
# delete suq job
#Created 2015-03-20, updated 2015-03-20, Nanjiang Shu
use CGI qw(:standard);
use CGI qw(:cgi-lib);
use CGI qw(:upload);

use Cwd 'abs_path';
use File::Basename;
my $rundir = dirname(abs_path(__FILE__));
my $suq = "/usr/bin/suq";
# at proj
my $basedir = abs_path("$rundir/../");
my $auth_ip_file = "$basedir/pred/config/auth_iplist.txt";#ip address which allows to run cgi script
my $suqbase = "/scratch";

print header();
print start_html(-title => "delete an suq job",
    -author => "nanjiang.shu\@scilifelab.se",
    -meta   => {'keywords'=>''});

if(!param())
{
    print "<pre>\n";
    print "usage: curl del_suqjob.cgi -d key=STR\n\n";
    print "       or in the browser\n\n";
    print "       del_suqjob.cgi?key=STR\n\n";
    print "Examples:\n";
    print "       del_suqjob.cgi?key=docker_subcons\n";
    print "       del_suqjob.cgi?key=docker_subcons&dryrun=true\n";
    print "</pre>\n";
    print end_html();
}
my $key = "";
my $isDryRun = "false";
my $remote_host = $ENV{'REMOTE_ADDR'};
if(param())
{
    if (param('key') ne ""){
        $key = param('key');
    }
    if (param('dryrun') ne ""){
        $isDryRun = param('dryrun');
    }

    my @auth_iplist = ();
    open(IN, "<", $auth_ip_file) or die;
    while(<IN>) {
        chomp;
        push @auth_iplist, $_;
    }
    close IN;

    if (grep { $_ eq $remote_host } @auth_iplist) {
        $jobidlist_str =`$suq -b $suqbase ls | grep $key | grep Wait | awk '{print \$1}'`;
        chomp($jobidlist_str);
        print "<pre>";
        print "Host IP: $remote_host\n\n";
        my @jobidlist = split "\n", $jobidlist_str;
# delete jobs
        my $numjob_to_delete = scalar(@jobidlist);
        if ($isDryRun ne "false"){
            print "[Dry Run]: ";
        }
        print "Number of jobs to be deleted: $numjob_to_delete\n";
        if ($numjob_to_delete > 0){
            for my $jobid (@jobidlist) {
                print "$suq -b $suqbase del $jobid\n";
                if ($isDryRun eq "false"){
                    `$suq -b $suqbase del $jobid`;
                }
            }

            $suqlist = `$suq -b $suqbase ls`;
            print "Suq list after deletion:\n\n";
            print "$suqlist\n";
        }else{
            print "No job to delete.\n";
        }

        print "</pre>";
    }else{
        print "Permission denied!\n";
    }

    print '<br>';
    print end_html();
}

