"""A python library for automatically rehydrating EC2 instances in AutoScaling Groups"""

import base64
import boto3
import json

# global vars
ASG_CLIENT = boto3.client('autoscaling')
S3_CLIENT = boto3.client('s3')


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

    new_lc_name = 'launch-config-' + asg_name + '-' + latest_ami

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


# This is the entry point for the Lambda
def modify_lc(event, context):
    """Main entrypoint for library.
    event and context parameters currently ignored, but exist to meet lambda interface."""

    bucket = ''
    key = ''
    auto_scale_group = ''
    latest_ami = ''

    curr_min = 0

    # Get filename from S3
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print bucket + ": " + key

    if bucket and key:
        obj_json = get_s3_obj_data(bucket, key)

        auto_scale_group = get_data('asg', obj_json)
        latest_ami = get_data('ami_id', obj_json)
        curr_min = get_data('min', obj_json)

        print auto_scale_group + ": " + latest_ami

    # auto_scale_group = event['asg']
    # latest_ami = event['ami_id']
    if not latest_ami:
        print "Could not find ami_id input"
        return None
    if not auto_scale_group:
        print "Could not find asg input"
        return None
    results = get_ami_for_asg(auto_scale_group)

    if update_lc(results, auto_scale_group, latest_ami):
        print "ASG updated with new LC"
    else:
        print "ASG not updated"
    return None
