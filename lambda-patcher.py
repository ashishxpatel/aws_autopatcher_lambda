# Python 3.7 Lambda that will patch EC2 instances that are specified. Note: This lambda must have the
# appropriate role permissions to interact with SSM and also run command

import time
import json
import boto3
import requests

# Place your incoming Slack webhook here

SLACK_URL = ''

# Initialize the clients for SSM and EC2

ssm_client = boto3.client('ssm')
ec2_client = boto3.resource('ec2')

command_to_run = 'yum update -y'

# List of EC2 instances that we want to patch

servers_to_patch = ['i-9999999']


def send_message(message):
    payload = {'text': message}
    try:
        return requests.post(url=SLACK_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    except requests.exceptions.RequestException as e:
        print (e.message)
        return False

# Function to get the name of the instance

def get_name_tag(instanceid):
    instance_name = ''
    instance = ec2_client.Instance(instanceid)
    for tags in instance.tags:
        if tags['Key'] == 'Name':
            instance_name = tags['Value']
        else:
            instance_name = 'N/A'
    return instance_name

# Create the function that that will communicate to an instance and patch it

def patch_server(instanceid):
    instance_name = get_name_tag(instanceid)
    slack_message = '*Now patching server with AWS Lambda (Demo)* '+instance_name+'-'+instanceid+"\nServer Response:"
    response = ssm_client.send_command(
        InstanceIds=[instanceid],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': [command_to_run]},)
    # Include some time for the command to run so we can get a response
    time.sleep(5)
    commandId = response['Command']['CommandId']
    server_output = ssm_client.get_command_invocation(
        CommandId=commandId,
        InstanceId=instanceid,
    )
    slack_message += "\n"+str(server_output['StandardOutputContent'])
    return slack_message

def lambda_handler():
    for servers in servers_to_patch:
        send_message(patch_server(servers))
