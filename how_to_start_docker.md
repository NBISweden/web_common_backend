# subcons

## for regular user

    docker run  -e USER_ID=$(id -u $USER) -v /big/data:/data -v /scratch:/scratch --rm --name t_subcons  -it -d nanjiang/subcons

## run apache user

    docker run -e USER_ID=$(id -u apache) -v /big/data:/data -v /scratch:/scratch -v /var/www/html/common_backend/proj/pred/static/:/static  --restart=always -it --name subcons  -d nanjiang/subcons 

# proq3

## for regular user

    docker run  -e USER_ID=$(id -u $USER) --rm -v /big/data/blastdb:/app/proq3/database/blastdb -v /big/software/rosetta/rosetta_bin_linux_2016.15.58628_bundle:/app/proq3/apps/rosetta -v /scratch:/scratch  -it --name t_proq3  -d nanjiang/proq3

## for apache server

    docker run  -e USER_ID=$(id -u apache)  -v /big/data/blastdb:/app/proq3/database/blastdb -v /big/software/rosetta/rosetta_bin_linux_2016.15.58628_bundle:/app/proq3/apps/rosetta -v /scratch:/scratch  -v /var/www/html/common_backend/proj/pred/static/:/static --restart=always -it --name proq3  -d nanjiang/proq3 

# predzinc

## for regular user

    docker run  -e USER_ID=$(id -u $USER) -v /data:/data -v /data/db_predzinc:/app/predzinc/data -v /scratch:/scratch --rm --name t_predzinc  -it -d nanjiang/predzinc 

## for apache server
    docker run -e USER_ID=$(id -u apache) -v /big/data:/data -v /big/data/db_predzinc:/app/predzinc/data -v /scratch:/scratch -v /var/www/html/common_backend/proj/pred/static/:/static  --restart=always -it --name predzinc  -d nanjiang/predzinc

---

# Using docker-compose to start containers for web-server use
It is recommended to use docker-compose to start docker containers

First you need to create the environmental file `.env` by 

    make init

An example of the contnet of the `.env` file is shown below

```
# Please change if you have different settings
DATA_DIR=/data
TOPCONSDB_DIR=/data/topcons2_database
BLASTDB_DIR=/data/blastdb
ROSETTA_DIR=/data/rosetta/rosetta_bin_linux_2016.15.58628_bundle
SCRATCH_DIR=/scratch

# Please don't change from here
WEB_STATIC=/big/data3/server/web_common_backend//proj/pred/static
USER_ID=33
```

Note that `topcons2_database` should be under the folder `${DATA_DIR}`

You may need to modify values of some of the environmental variables
accordingly.

After that, start the containers by 

    make up

If you just want to start only one container, e.g. `topcons2`, use

    docker-compose up -d topcons2
