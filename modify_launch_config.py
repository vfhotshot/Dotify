"""A python library for automatically rehydrating EC2 instances in AutoScaling Groups"""

import base64
import boto3
import json
import time
import os

# global vars
ASG_CLIENT = boto3.client('autoscaling')
S3_CLIENT = boto3.client('s3')
LAMBDA_CLIENT = boto3.client('lambda')

def get_ami_for_asg(asg_id):
    """Called by set_bounce_amis to find the AMI ID for an ASG.
       Optionally checks the AMI_VALIDATED tag on the ASG to see if it
       matches the AMI ID."""

    response = ASG_CLIENT.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_id]
    )
    if 'AutoScalingGroups' not in response or len(response['AutoScalingGroups']) == 0:
        return {'error': 'ASG not found'}
    asg_detail = response['AutoScalingGroups'][0]
    asg_name = asg_detail['AutoScalingGroupName']
    instances = asg_detail['Instances']
    lc_name = asg_detail['LaunchConfigurationName']
    desired_capacity = asg_detail.get('DesiredCapacity', 0)

    lc_response = ASG_CLIENT.describe_launch_configurations(
        LaunchConfigurationNames=[lc_name]
    )

    launch_config = lc_response['LaunchConfigurations'][0]
    image_id = launch_config['ImageId']

    return {
        'ami': image_id,
        'name': asg_name,
        'instances': instances,
        'lc': launch_config,
        'lc_name': lc_name,
        'desired_capacity': desired_capacity
    }

def update_lc(results, asg_name, latest_ami):
    """Create a new Launch Configuration, associate it with the AutoScaling Group,
    and Delete the old one"""

    # create a new launch configuration with the latest ami
    launch_config = results['lc']
    curr_lc_name = results['lc_name']
    curr_asg_ami = results['ami']
    
    ticks = time.time()
    
    new_lc_name = 'launch-config-' + asg_name + '-' + str(ticks)

    # Check if ASG update is needed
    if curr_lc_name == new_lc_name and curr_asg_ami == latest_ami:
        print "LC and AMI are unchanged"
        return False

    # First check if launch config with new ami already exists
    response = ASG_CLIENT.describe_launch_configurations(LaunchConfigurationNames=[new_lc_name])
    if not response['LaunchConfigurations']:
        # LC doesn't exist. Create it first.
        print "Creating new LC: " + new_lc_name
        kwargs = {
            'LaunchConfigurationName': new_lc_name,
            'ImageId': latest_ami,
        }

        for k in ['KeyName', 'SecurityGroups', 'UserData', 'InstanceType',
                  'BlockDeviceMappings', 'InstanceMonitoring', 'IamInstanceProfile',
                  'EbsOptimized', 'AssociatePublicIpAddress']:
            print str(k)

            if k in launch_config and launch_config[k] != '':
                kwargs[k] = launch_config[k]
                print str(kwargs[k])

        # print "Old snapshot: " + str(kwargs['BlockDeviceMappings'][0].get('Ebs').get('SnapshotId'))
        # kwargs['BlockDeviceMappings'][0]['Ebs']['SnapshotId'] = 'snap-53beeae1'
        # print "New snapshot: " + str(kwargs['BlockDeviceMappings'][0].get('Ebs').get('SnapshotId'))


        # need to base64 decode the user data, so it isn't encoded twice.
        if 'UserData' in kwargs:
            kwargs['UserData'] = base64.standard_b64decode(kwargs['UserData'])

        clc_response = ASG_CLIENT.create_launch_configuration(**kwargs)
        print(clc_response)
    else:
        print new_lc_name + " already exists"

    # detatch the old launch configuration and attach the new one
    uasg_response = ASG_CLIENT.update_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchConfigurationName=new_lc_name
    )
    print(uasg_response)
    return True


# Get S3 Object JSON
def get_s3_obj_data(bucket, key):
    s3_response = S3_CLIENT.get_object(
        Bucket=bucket,
        Key=key
    )
    obj_json = json.loads(response['Body'].read())

    print str(json.dumps(obj_json))
    return obj_json


# Get data in json obj if it exists, return empty string otherwise
def get_data(key, obj_json):
    if key in obj_json:
        return obj_json[key]
    return ''

def call_refresh(asg_name):
    
    event_payload = {'asg': asg_name, 'call_action': 'scale_up'}
    invokeResponse = LAMBDA_CLIENT.invoke(
        FunctionName='refresh_instances',
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps(event_payload)
    )
    return invokeResponse

# This is the entry point for the Lambda
def modify_lc(event, context):
    """Main entrypoint for library.
    event and context parameters currently ignored, but exist to meet lambda interface."""

    auto_scale_group = ''

    curr_min = 0

    # Should be ASG name
    auto_scale_group = event['stack']
    print auto_scale_group
    
    #Send text approval request
    os.system("curl -X POST -H 'Content-Type: application/json' -d '{\"value1\":\""+ auto_scale_group + "\"}' https://maker.ifttt.com/trigger/approval-request/with/key/cTQ8Wc2oHssQsfV_0hN5Fj")
    
    # Send Starting Slack Notification
    os.system("curl -X POST --data-urlencode 'payload={\"channel\": \"#dotify\", \"username\": \"Tim-Bot\", \"text\": \"Refreshing DotifyA stack...\", \"icon_emoji\": \":thumbsup:\"}' https://hooks.slack.com/services/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")
    
    latest_ami = 'ami-c58c1dd3'
    if not latest_ami:
        print "Could not find ami_id input"
        return None
    if not auto_scale_group:
        print "Could not find asg input"
        return None
    results = get_ami_for_asg(auto_scale_group)

    if update_lc(results, auto_scale_group, latest_ami):
        print "ASG updated with new LC"
        # Call Refresh
        call_refresh(auto_scale_group)
    else:
        print "ASG not updated"
    
    
    return None
