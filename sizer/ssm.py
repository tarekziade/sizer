import os
import boto3
import time
import contextlib
from sizer.util import log


_DEL = "----------ERROR-------"


class TimeoutError(Exception):
    pass


class SSMClient(object):
    def __init__(self, iid, region_name='eu-west-1', timeout=30,
                 ssm_client=None):
        if ssm_client:
            self._c = ssm_client
        else:
            self._c = boto3.client('ssm', region_name=region_name)
        self._b = boto3.client('s3', region_name=region_name)
        self.timeout = timeout
        self.iid = iid
        describe = self._c.describe_instance_information

        iids = [i['InstanceId'] for i in
                describe()['InstanceInformationList']]

        if self.iid not in iids:
            raise ValueError('%r is not listed as SSM compatible' % iid)

    def run_command(self, command):
        res = self._c.send_command(InstanceIds=[self.iid],
                                   DocumentName='AWS-RunShellScript',
                                   Comment='Sizer',
                                   TimeoutSeconds=30,
                                   OutputS3BucketName='tarek-sizer',
                                   Parameters={"commands": [command]})
        cid = res['Command']['CommandId']
        attempts = 0
        while attempts < 2:
            try:
                return self._wait(cid)
            except TimeoutError:
                attempts += 1
        raise TimeoutError()

    def _wait(self, cid):
        start = time.time()
        while time.time() - start < self.timeout:
            res = self._c.list_commands(CommandId=cid)
            command = res["Commands"][0]
            status = command["Status"]
            if status in ("Success", "Failed"):
                res = self._c.list_command_invocations(CommandId=cid,
                                                       Details=True)
                res = res["CommandInvocations"][0]
                res = res['CommandPlugins'][0]

                exit_code = res['ResponseCode']
                bucket = res.get('OutputS3BucketName')

                if bucket:
                    prefix = res['OutputS3KeyPrefix']
                    res = self._b.list_objects_v2(Bucket='tarek-sizer',
                                                  Prefix=prefix)
                    keys = [entry['Key'] for entry in res.get('Contents', [])]

                    stdout = [key for key in keys if key.endswith('stdout')]
                    stderr = [key for key in keys if key.endswith('stderr')]

                    if stdout:
                        stdout = self._b.get_object(Bucket="tarek-sizer",
                                                    Key=stdout[0])
                        stdout = stdout['Body'].read().strip()
                    else:
                        stdout = b''

                    if stderr:
                        stderr = self._b.get_object(Bucket="tarek-sizer",
                                                    Key=stderr[0])
                        stderr = stderr['Body'].read().strip()
                    else:
                        stderr = b''

                    stdout = stdout.decode('utf8')
                    stderr = stderr.decode('utf8')
                else:
                    output = res['Output'].split(_DEL)
                    if len(output) == 2:
                        stdout, stderr = output[0].strip(), output[1].strip()
                    else:
                        stdout = output[0].strip()
                        stderr = ''
                return exit_code, stdout, stderr
            elif status in ("Pending", "InProgress"):
                time.sleep(3)
            else:
                raise ValueError(str(res))
        raise TimeoutError()


@contextlib.contextmanager
def run_service(docker, iid='i-0612c54dab69778f7', ssm_client=None,
                port=8888):
    log("Starting SSM client on %s" % iid)
    c = SSMClient(iid, ssm_client=ssm_client)

    # get the AWS public IP
    log("Getting the instance public IP...")
    c.ip = c.run_command("curl http://169.254.169.254/latest"
                         "/meta-data/public-ipv4")[1]
    log("Instance IP is %s" % c.ip)

    c.run_command("rm -rf /tmp/sizerdata")
    c.run_command("mkdir /tmp/sizerdata")
    images = []

    # running the service image
    log("Starting %s..." % docker)
    port = '%d:%d/tcp' % (port, port)
    cmd = 'docker run --name tested -it -d -p %s --rm %s'
    cmd = cmd % (port, docker)
    image_id = c.run_command(cmd)[1]
    log("%s started" % image_id)
    images.append(image_id)

    c.container_name = 'tested'

    # running the glances image
    log("Updating tarekziade/sizer-glances...")
    cmd = ("docker pull tarekziade/sizer-glances")
    c.run_command(cmd)

    log("Starting tarekziade/sizer-glances...")
    cmd = ("docker run -it -d --rm "
           "-v /var/run/docker.sock:/var/run/docker.sock:ro "
           "--name glances -v /tmp/sizerdata:/app/data:rw --pid=host "
           "tarekziade/sizer-glances")

    ex = "glances -C /app/glances.ini --export-csv /app/data/glances.csv"
    cmd = cmd + ' ' + ex
    image_id = c.run_command(cmd)[1]
    log("%s started" % image_id)
    images.append(image_id)

    # we're ready
    try:
        yield c
    finally:
        # shutdown everything
        for image in images:
            log("Terminating %s" % image)
            c.run_command("docker kill " + image)
            c.run_command("docker rm " + image)

    log("Grabing metrics...")

    output = c.run_command("cat /tmp/sizerdata/glances.csv")[1]
    if not os.path.exists('/tmp/sizerdata'):
        os.makedirs('/tmp/sizerdata')
    with open('/tmp/sizerdata/glances.csv', 'w') as f:
        f.write(output)
    log("All done.")
