# Generic backend for protein prediction web servers

## Description:
    This is a generic web-server framework for protein structure prediction,
    supposed to run on the computational node as a backend.
    called by WSDL

## Author
Nanjiang Shu

System developer at NBIS

Email: nanjiang.shu@scilifelab.se

## Reference

## Installation

1. Install dependencies for the web server
    * Apache
    * mod\_wsgi

2. Install the virtual environments by 

    $ bash setup_virtualenv.sh

3. Create the django database db.sqlite3

4. Run 

    $ bash init.sh

    to initialize the working folder

5. In the folder `proj`, create a softlink of the setting script.

    For development version

        $ ln -s dev_settings.py settings.py

    For release version

        $ ln -s pro_settings.py settings.py

    Note: for the release version, you need to create a file with secret key
    and stored at `/etc/django_pro_secret_key.txt`

6.  On the computational node. run 

    $ virtualenv env --system-site-packages

    to make sure that python can use all other system-wide installed packages


## Supported methods

* TOPCONS2
* SCAMPI2-single
* SCAMPI2-MSA
* SubCons (using Docker)
* ProQ3/ProQ3D (using Docker)
* PRODRES

## Variables 

* variable for the software to be used: name\_software

