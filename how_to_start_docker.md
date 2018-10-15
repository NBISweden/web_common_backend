# subcons

## for regular user

    docker run  -e USER_ID=$(id -u $USER) -v /big/data:/data -v /scratch:/scratch --rm --name t_subcons  -it -d nanjiang/subcons

## run apache user

    docker run -v /big/data:/data -v /scratch:/scratch -v /var/www/html/common_backend/proj/pred/static/:/static -u $(id -u apache):$(id -g apache) --restart=always -it --name subcons  -d nanjiang/subcons

# proq3

## for regular user

    docker run  -e USER_ID=$(id -u $USER) --rm -v /big/data/blastdb:/app/proq3/database/blastdb -v /big/software/rosetta/rosetta_bin_linux_2016.15.58628_bundle:/app/proq3/apps/rosetta -v /scratch:/scratch  -it --name t_proq3  -d nanjiang/proq3

## for apache server

    docker run  -e USER_ID=$(id -u apache)  -v /big/data/blastdb:/app/proq3/database/blastdb -v /big/software/rosetta/rosetta_bin_linux_2016.15.58628_bundle:/app/proq3/apps/rosetta -v /scratch:/scratch  -v /var/www/html/common_backend/proj/pred/static/:/static --restart=always -it --name proq3  -d nanjiang/proq3 
