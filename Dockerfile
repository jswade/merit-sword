#*******************************************************************************
#Dockerfile
#*******************************************************************************

#Purpose:
#This file describes the operating system prerequisites for MERIT-SWORD, and is
#used by the Docker software.
#Author:
#Cedric H. David, Jeffrey Wade, 2024


#*******************************************************************************
#Usage
#*******************************************************************************
#docker build -t merit-sword:myimage -f Dockerfile .             #Create image
#docker run --rm --name merit-sword_mycontainer     \
#           -it merit-sword:myimage                      #Run image in container
#docker run --rm --name merit-sword_mycontainer     \
#           -v $PWD/input:/home/merit-sword/input   \
#           -v $PWD/output:/home/merit-sword/output \
#           -it merit-sword:myimage                         #Run and map volumes
#docker save -o merit-sword_myimage.tar merit-sword:myimage #Save copy of image
#docker load -i merit-sword_myimage.tar                     #Load saved image


#*******************************************************************************
#Operating System
#*******************************************************************************
FROM debian:11.7-slim


#*******************************************************************************
#Copy files into Docker image (this ignores the files listed in .dockerignore)
#*******************************************************************************
WORKDIR /home/merit-sword/
COPY . .


#*******************************************************************************
#Operating System Requirements
#*******************************************************************************
RUN  apt-get update && \
     apt-get install -y --no-install-recommends $(grep -v -E '(^#|^$)' requirements.apt) && \
     rm -rf /var/lib/apt/lists/*


#*******************************************************************************
#Python requirements
#*******************************************************************************
ADD https://bootstrap.pypa.io/pip/get-pip.py .
RUN python3 get-pip.py --no-cache-dir \
    `grep 'pip==' requirements.pip` \
    `grep 'setuptools==' requirements.pip` \
    `grep 'wheel==' requirements.pip` && \
    rm get-pip.py

RUN pip3 install --no-cache-dir -r requirements.pip


#*******************************************************************************
#Intended (default) command at execution of image (not used during build)
#*******************************************************************************
CMD  /bin/bash


#*******************************************************************************
#End
#*******************************************************************************
