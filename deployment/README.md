# Server architecture at the Arne Elofsson Lab 

# Hardware

## Servers at SciLifeLab

### vault.bioinfo.se
RAID (file raid 10 Tb). File system is full. Users have had the possibility to copy backups there (manually with scp or rsync).

### pcons1.scilifelab.se

4 cores 16 GiB RAM

cpubenchmark.net E3-1240 v3 = 9704
```
[eriksjolund@pcons1 ~]$ date
mån jun  5 14:51:50 CEST 2017
[eriksjolund@pcons1 ~]$ free -g
             total       used       free     shared    buffers     cached
Mem:            15         14          1          0          6          1
-/+ buffers/cache:          6          8
Swap:            7          0          7
[eriksjolund@pcons1 ~]$ cat /proc/cpuinfo |grep "model name" | head -1
model name	    : Intel(R) Xeon(R) CPU E3-1240 v3 @ 3.40GHz
[eriksjolund@pcons1 ~]$ cat /proc/cpuinfo |grep "model name" | wc -l
8
[eriksjolund@pcons1 ~]$ df -h
Filesystem            Size  Used Avail Use% Mounted on
/dev/mapper/vg_pcons1-lv_root
                       50G   21G   26G  45% /
tmpfs                 7,8G     0  7,8G   0% /dev/shm
/dev/mapper/vg_pcons2-lv_big
                      2,7T  2,3T  314G  88% /big
/dev/sda1             477M  172M  280M  38% /boot
/dev/mapper/vg_pcons1-lv_home
                      172G  3,9G  160G   3% /home
AFS                   8,6G     0  8,6G   0% /afs
[eriksjolund@pcons1 ~]$ 
```


### pcons2.scilifelab.se
4 cores 16 GiB RAM

cpubenchmark.net E3-1240 v3 = 9704

```
[eriksjolund@pcons3 ~]$ date
mån jun  5 14:40:28 CEST 2017
[eriksjolund@pcons3 ~]$ cat /proc/cpuinfo |grep "model name"|wc -l
32
[eriksjolund@pcons3 ~]$ cat /proc/cpuinfo |grep "model name"|head -1
model name	    : Intel(R) Xeon(R) CPU E5-2630 v3 @ 2.40GHz
[eriksjolund@pcons3 ~]$ free -g
             total       used       free     shared    buffers     cached
Mem:           315         37        277          0         19          2
-/+ buffers/cache:         15        299
Swap:           49          0         49
[eriksjolund@pcons3 ~]$ df -h
Filesystem            Size  Used Avail Use% Mounted on
/dev/mapper/vg_pcons3-lv_root
                       50G  5,9G   41G  13% /
tmpfs                 158G     0  158G   0% /dev/shm
/dev/sda2             976M  115M  810M  13% /boot
/dev/sdb2             976M  115M  810M  13% /boot2
/dev/sdc2             976M  115M  810M  13% /boot3
/dev/sda1             127M  256K  127M   1% /boot/efi
/dev/sdb1             127M  256K  127M   1% /boot2/efi
/dev/sdc1             127M  256K  127M   1% /boot3/efi
/dev/mapper/vg_pcons3-lv_home
                      148G  1,4G  139G   1% /home
/dev/mapper/vg_pcons3-lv_big
                      5,1T  1,5T  3,3T  32% /big
AFS                   2,0T     0  2,0T   0% /afs
[eriksjolund@pcons3 ~]$ 
```

### pcons3.scilifelab.se
32 cores  315 GiB RAM       (is not used right now)   
cpubenchmark.net E5-2630 = 8906

```
[eriksjolund@pcons2 ~]$ date
mån jun  5 14:46:05 CEST 2017
[eriksjolund@pcons2 ~]$ free -g
             total       used       free     shared    buffers     cached
Mem:            15         15          0          0          0         13
-/+ buffers/cache:          1         13
Swap:           15          2         13
[eriksjolund@pcons2 ~]$ cat /proc/cpuinfo |grep "model name"|head -1
model name	    : Intel(R) Xeon(R) CPU E3-1240 v3 @ 3.40GHz
[eriksjolund@pcons2 ~]$ cat /proc/cpuinfo |grep "model name"|wc -l
8
[eriksjolund@pcons2 ~]$ df -h
Filesystem            Size  Used Avail Use% Mounted on
/dev/mapper/vg_pcons2-lv_root
                       50G  5,3G   42G  12% /
tmpfs                 7,8G     0  7,8G   0% /dev/shm
/dev/mapper/vg_pcons2-lv_big
                      2,5T  1,3T  1,2T  53% /big
/dev/md0              477M  105M  347M  24% /boot
/dev/mapper/vg_pcons2-lv_home
                      148G  271M  140G   1% /home
[eriksjolund@pcons2 ~]$ 
```


### EGI cluster
Right now 100 CPU cores from EGI are used (https://www.egi.eu) but Arne Elofsson's EGI project will expire December 31 2017.
The compute nodes have been allocated through an OpenStack API.


# Online web services

The online web services

- http://topcons.net/
- http://subcons.bioinfo.se/
- http://c3.pcons.net/
- http://c.pcons.net/
- http://pcons.net/
- http://proq3.bioinfo.se/
- http://boctopus.bioinfo.se/
- http://prodres.bioinfo.se/

are all running on the pcons1 frontend.

## Disk usage

topcons makes use of 450 Gb disk space.
A number of the other web services makes use of 100 Gb each.

## Architectural overview

1. Do a short search (about 1 minute)
2. If not found, do long search (about 1 core hour)

pcons3 does cache lookup. Has this sequence been run before?
If it is a short sequence, run on pcons3.

If job is too big, then put in queue.

## Possible improvements to the backend

- boctopus.bioinfo.se
- prodress.bioinfo.se
- topcons.net 

all share some common backend functionality. The backend should not duplicated as it is right now.


# TODO

- Nanjiang moves prodres to cloud
- Erik Sj installs Centos7 on pcons3 (or SciLife IT)
- Erik Sj tries to install common backend (e.g. topcons)
- Change to cloud for pcons
- Change queueing system.  (Nanjiang suggested RabbitMQ)

