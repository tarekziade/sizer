import os
import boto3
import time
from sizer.util import log


_UD = os.path.join(os.path.dirname(__file__), 'user_data.sh')
with open(_UD) as f:
    _USER_DATA = f.read()

_AMIS = {'eu-west-1': 'ami-ebd02392'}


def launch_instance(region='eu-west-1', instance_type='t2.micro'):
    ec2 = boto3.resource('ec2', region_name=region)

    params = {'ImageId': _AMIS[region],
              'InstanceType': instance_type,
              'MinCount': 1,
              'MaxCount': 1,
              'UserData': _USER_DATA,
              'SecurityGroupIds': ['sg-f4360b8c'],
              'KeyName': 'autosizer'}

    # starts the instance
    log('Starting an instance...')
    res = ec2.create_instances(**params)
    iid = res[0].id
    log('Instance %r created' % iid)
    log('Wait for the instance to run')
    instance = ec2.Instance(iid)
    instance.wait_until_running()
    # Also wait status checks to complete
    log('Wait for all statuses to be green')
    waiter = ec2.meta.client.get_waiter('instance_status_ok')
    waiter.wait(InstanceIds=[iid])

    # IAM roles
    log('Applying IAM roles...')
    profile = {'Name': 'tarek_autosizer'}
    ec2.meta.client.associate_iam_instance_profile(IamInstanceProfile=profile,
                                                   InstanceId=iid)
    log('Wait for IAM role to be effective...')
    ssm = boto3.client('ssm', region_name=region)
    describe = ssm.describe_instance_information

    start = time.time()
    while time.time() - start < 60 * 5:
        iids = [i['InstanceId'] for i in
                describe()['InstanceInformationList']]
        if iid in iids:
            break
        time.sleep(10.)

    return iid, ssm
