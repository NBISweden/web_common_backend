#!/usr/bin/perl -w
# test runjob

use CGI qw(:standard);
use CGI qw(:cgi-lib);
use CGI qw(:upload);

use Cwd 'abs_path';
use File::Basename;
my $rundir = dirname(abs_path(__FILE__));
# at proj
my $basedir = abs_path("$rundir/../");
my $progname = basename(__FILE__);
my $logpath = "$basedir/pred/static/log";
my $errfile = "$logpath/$progname.err";
my $auth_ip_file = "$basedir/pred/config/auth_iplist.txt";#ip address which allows to run cgi script
my $suq = "/usr/bin/suq";
my $suqbase = "/tmp";
my $suqworkdir = "/tmp";

my $runjobscript = "$basedir/pred/app/run_job.py";

print header();
print start_html(-title => "test run job",
    -author => "nanjiang.shu\@scilifelab.se",
    -meta   => {'keywords'=>''});

# if(!param())
# {
#     print "<pre>\n";
#     print "usage: curl get_suqlist.cgi -d base=suqbasedir \n\n";
#     print "       or in the browser\n\n";
#     print "       get_suqlist.cgi?base=suqbasedir\n\n";
#     print "Example\n";
#     print "       get_suqlist.cgi?base=log\n";
#     print "</pre>\n";
#     print end_html();
# }
my $remote_host = $ENV{'REMOTE_ADDR'};

my @auth_iplist = ();
open(IN, "<", $auth_ip_file) or die;
while(<IN>) {
    chomp;
    push @auth_iplist, $_;
}
close IN;

if (grep { $_ eq $remote_host } @auth_iplist) {
    my $command =  "cd /scratch; for i in 1 2 3 4 5 6; do sbatch /home/ubuntu/test/slurm/test_submit.sh; done >>$errfile";
    $output = `$command`;
    print "<pre>";
    print "Host IP: $remote_host\n\n";
    print "command: $command\n\n";
    print "$output\n";
    $output = `squeue >> $errfile`;

    print "</pre>";
}else{
    print "Permission denied!\n";
}

print '<br>';
print end_html();

