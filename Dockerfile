FROM amazon/aws-cli:2.1.10

#yum update &&\
# &&\ pip3 install meilisearch
RUN yum install python3 -y

COPY src /dockerfolder

#  When GitHub Actions is running, it mounts
# the whole repository on /github/workspace,
# and changes the workdir to there on run.
ENTRYPOINT ["python3", "/dockerfolder/main.py"]