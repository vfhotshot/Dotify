import time
import boto3

LAMBDA_CLIENT = boto3.client('lambda')
ASG_CLIENT = boto3.client('autoscaling')


def scale_up(asg_name):
    asg_response = ASG_CLIENT.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )
    asg_obj = asg_response['AutoScalingGroups'][0]
    min_size = asg_obj['MinSize']
    max_size = asg_obj['MaxSize']
    desired_size = asg_obj['DesiredCapacity']
    
    # TODO Check if all instances are up first

    double_desired = desired_size * 2
    print "Updating " + asg_name + " desired capacity from " + str(desired_size) + " to " + str(double_desired)
    update_response = ASG_CLIENT.update_auto_scaling_group(AutoScalingGroupName=asg_name,
                                                           DesiredCapacity=double_desired)
    # Wait after updating DesiredCapacity
    sleep_time = 120
    print "Sleeping for " + str(sleep_time) + " seconds for new instances to spin up..."
    time.sleep(sleep_time)  # delays for 120 seconds

    # Recursive:
    event_payload = {'asg': asg_name, 'call_action': 'scale_down', 'size': desired_size}
    invokeResponse = LAMBDA_CLIENT.invoke(
        FunctionName='refresh_instances',
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps(event_payload)
    )
    return None


def scale_down(asg_name, size_down):
    
    # TODO Check if all instances are up first
    
    print "Updating " + asg_name + " desired capacity to " + str(size_down)
    update_response = ASG_CLIENT.update_auto_scaling_group(AutoScalingGroupName=asg_name,
                                                           DesiredCapacity=size_down)
    return None


def lambda_handler(event, context):
    asg_name = event['asg']
    action = event['call_action']

    if action == 'scale_up':
        scale_up(asg_name)
    elif action == 'scale_down':
        size_down = event['size']
        scale_down(asg_name, size_down)

    return {'Completed': action}
