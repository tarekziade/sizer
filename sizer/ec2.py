import boto3
import time


_USER_DATA = """\
#!/bin/bash
cd /tmp
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
sudo yum install -y docker
sudo service docker start
sudo start amazon-ssm-agent
"""


_AMIS = {'eu-west-1': 'ami-ebd02392'}

def log(msg):
    print(msg)


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
    response = ec2.meta.client.associate_iam_instance_profile(
        IamInstanceProfile = {
            'Name': 'tarek_autosizer'
        },
        InstanceId=iid
    )

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

    return iid
