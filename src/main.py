import os
import ec2
from datetime import datetime
import pathlib

def run_commands(commands):
  for cmd in commands:
    exit_code = os.system(cmd)
    if exit_code != 0:
      raise Exception(f'Command exit with code {exit_code}: {cmd}')

def log(txt):
  print(f'{datetime.now()}- {txt}')

log('started')

dockerfolder = pathlib.Path(__file__).parent.parent.absolute()
deployment = os.environ['DEPLOYMENT']
project_name = os.environ['PROJECT']

#run_commands([ f'aws s3 sync {dockerfolder}/ec2 s3://{project_name}/deployment_files/deployer' ])

ec2_instance = ec2.create_instance(f'{project_name}-{deployment}-warmup')

#public_ip = ec2_instance.get_public_ip()

#configure_macaeentrega_meiliseach.run(public_ip)

if deployment == 'prod':
  ec2_instance.change_elastic_ip(project_name)

old_ec2_instance = ec2.get_instance_by_name(f'{project_name}-{deployment}')
if old_ec2_instance != None:
  old_ec2_instance.rename(f'{project_name}-{deployment}-old')
  # TODO: check if is it needed to copy previous meilisearch-data docker volue or not (leave it here, or in configure_macaeentrega_meiliseach?)
  old_ec2_instance.terminate()

ec2_instance.rename(f'{project_name}-{deployment}')

log('finished')