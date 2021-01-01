# Python 3.6+
# usage:
#   ec2_instance = ec2.create_instance()
#   answer = ec2_instance.send_commands(["echo 'Who I am?'"])
#   ec2_instance.terminate()
import os
import json
import time
from datetime import datetime
import pathlib

dockerfolder = pathlib.Path(__file__).parent.parent.absolute()

def log(txt):
  print(f'{datetime.now()}- {txt}')

def create_instance(name):
  """Creates, starts and waits for the ec2 instance to be ready for receiving commands"""

  log(f'debug::ec2.create_instance: started')

  cmd = f'aws ec2 run-instances --image-id ami-05394aef61908afaa --tag-specifications \'ResourceType=instance,Tags=[{{Key=Name,Value={name}}}]\' --instance-type t4g.micro --key-name aws-key-pair-us-east-2 --security-group-ids sg-3735f55e --subnet-id subnet-3bf8c471 --iam-instance-profile Name=ec2-ssm --user-data file://{dockerfolder}/ec2_setup.sh --query "Instances[].InstanceId" --output text'
  instance_id = _run_cmd_txt(cmd)

  log(f'debug::ec2.create_instance: run-instances sent: {instance_id}')
   
  cmd = f'aws ssm describe-instance-information --filters "Key=InstanceIds,Values={instance_id}" --output text --query "InstanceInformationList[].PingStatus"'
  START = 5
  TIMEOUT = 30
  time.sleep(START)
  for i in range(START, TIMEOUT):
    ping_status = _run_cmd_txt(cmd)
    log(f'debug::create_instance::describe-instance-information sent [{i}]: {ping_status}')

    if ping_status == "Online":
      break
    elif i == TIMEOUT - 1:
      raise Exception(f'Instance {instance_id} never got ready for receiving commands (SSM).')
    else:
      time.sleep(1)
    
  return EC2(instance_id)

#def get_instance_by_id(instance_id):
#  return EC2(instance_id)

def get_instance_by_name(name):
  cmd = f"aws ec2 describe-instances --filters \"Name=tag:Name,Values={name}\" --output text --query \"Reservations[].Instances[].InstanceId\""
  instance_id = _run_cmd_txt(cmd)
  log(f'debug::get_instance_by_name::describe-instances sent: {instance_id}')

  if instance_id != '':
    return EC2(instance_id)
  else:
    return None
 
def _run_cmd_txt(cmd):
  return os.popen(cmd).read().strip()
  
def _run_cmd_json(cmd):
  txt = _run_cmd_txt(cmd)
  return json.loads(txt)

class EC2():
  def __init__(self, instance_id):
    self.instance_id = instance_id

  def terminate(self):
    cmd = f'aws ec2 terminate-instances --instance-ids {self.instance_id} --output text --query "TerminatingInstances[].CurrentState.Name"'
    answer = _run_cmd_txt(cmd)
    log(f'debug::ec2.EC2.terminate::terminate-instances sent: {answer}')

    if answer not in ["shutting-down", "terminated"]:
      raise Exception(f'Terminating instance {self.instance_id} not succeeded well.')

  def rename(self, new_name):
    cmd = f'aws ec2 create-tags --resources {self.instance_id} --tags Key=Name,Value={new_name}'
    ret = os.system(cmd)
    log(f'debug::ec2.EC2.rename::create-tags sent: exit_code {ret}')
  
  def change_elastic_ip(self, name):
    cmd = f'aws ec2 describe-addresses --filters "Name=tag:Name,Values={name}" --query "Addresses[].PublicIp" --output text'
    public_ip = _run_cmd_txt(cmd)
    log(f'debug::ec2.EC2.change_elastic_ip::describe-addresses sent: {public_ip}')

    cmd = f'aws ec2 associate-address --instance-id {self.instance_id} --public-ip {public_ip}'
    ret = os.system(cmd)
    log(f'debug::ec2.EC2.change_elastic_ip::associate-address sent: exit_code {ret}')

  def get_public_ip(self):
    cmd = f"aws ec2 describe-instances --instance-ids {self.instance_id} --output text --query \"Reservations[].Instances[].PublicIpAddress\""
    public_ip = _run_cmd_txt(cmd)
    log(f'debug::ec2.EC2.get_public_ip::describe-instances sent: {public_ip}')
    if '.' not in public_ip:
      raise Exception(f'Could not get public ip from instance {self.instance_id}.')
    return public_ip
  
#  def run_commands(self, commands):
#    log(f'debug::ec2.EC2.run_commands: started')
#
#    skipped_commands = map(lambda command: command.replace('"', '\\"'), commands)
#    joined_skipped_commands = '\\", \\"'.join(skipped_commands)
#
#    cmd = f'aws ssm send-command --instance-ids "{self.instance_id}" --document-name "AWS-RunShellScript" --parameters commands=["\\"{joined_skipped_commands}\\""] --output text --query "Command.CommandId"'
#    command_id = _run_cmd_txt(cmd)
#    log(f'debug::ec2.EC2.run_commands::send-command sent::cmd: {command_id}\n{cmd}')
#
#    cmd = f'aws ssm list-command-invocations --command-id "{command_id}" --details --query "CommandInvocations[].CommandPlugins[].{{Status:Status,Output:Output}}"'
#    TIMEOUT = 300
#    STEP = 5
#    for i in range(0, TIMEOUT, STEP):
#      answer = _run_cmd_json(cmd)
#      status = answer[0]["Status"]
#      log(f'debug::ec2.EC2.run_commands::list-command-invocations sent [{i}]::status "{status}"')
#      if status == "Success":
#        break
#      elif i == TIMEOUT - STEP:
#        raise Exception(f'Command {command_id} timed out.')
#      elif status in ["Pending", "InProgress"]:
#        time.sleep(STEP)
#      else:
#        raise Exception(f'Command {command_id} got in an invalid state: {status}')
#
#    return answer[0]["Output"].strip()