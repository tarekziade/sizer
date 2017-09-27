import sys
import boto3
import time
import contextlib


_DEL = "----------ERROR-------"


class TimeoutError(Exception):
    pass


def log(msg):
    print(msg)


class SSMClient(object):
    def __init__(self, iid, region_name='eu-west-1', timeout=600):
        self._c = boto3.client('ssm', region_name=region_name)
        self._b = boto3.client('s3', region_name=region_name)
        self.timeout = timeout
        self.iid = iid

    def run_command(self, command):
        res = self._c.send_command(InstanceIds=[self.iid],
                                   DocumentName='AWS-RunShellScript',
                                   Comment='Sizer',
                                   OutputS3BucketName='tarek-sizer',
                                   Parameters={"commands": [command]})
        cid = res['Command']['CommandId']
        return self._wait(cid)

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
            time.sleep(1)
        raise TimeoutError()



@contextlib.contextmanager
def run_service(iid='i-0612c54dab69778f7'):
    log("Starting SSM client on %s" % iid)
    c = SSMClient(iid)

    # get the AWS public IP
    c.ip = c.run_command("curl http://169.254.169.254/latest"
                         "/meta-data/public-ipv4")[1]
    log("Instance IP is %s" % c.ip)

    c.run_command("rm -rf /tmp/sizerdata")
    c.run_command("mkdir /tmp/sizerdata")
    images = []

    # running the service image
    log("Starting kinto/kinto-server...")
    cmd = 'docker run --name tested -it -d -p 8888:8888/tcp --rm kinto/kinto-server'
    image_id = c.run_command(cmd)[1]
    log("%s started" % image_id)
    images.append(image_id)

    c.container_name = 'tested'

    # running the glances image
    log("Updating tarekziade/sizer-glances...")
    cmd = ("docker pull tarekziade/sizer-glances")
    c.run_command(cmd)

    log("Starting tarekziade/sizer-glances...")
    cmd = ("docker run -it -d --rm -v /var/run/docker.sock:/var/run/docker.sock:ro"
           " --name glances -v /tmp/sizerdata:/app/data:rw --pid=host "
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
    with open('/tmp/sizerdata/glances.csv', 'w') as f:
        f.write(output)
    log("All done.")
