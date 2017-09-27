import sys
import boto3
import time
import contextlib


_DEL = "----------ERROR-------"


class TimeoutError(Exception):
    pass


class SSMClient(object):
    def __init__(self, iid, region_name='eu-west-1', timeout=600):
        self._c = boto3.client('ssm', region_name=region_name)
        self.timeout = timeout
        self.iid = iid

    def run_command(self, command):
        res = self._c.send_command(InstanceIds=[self.iid],
                                   DocumentName='AWS-RunShellScript',
                                   Comment='Sizer',
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
    c = SSMClient(iid)

    # get the AWS public IP
    c.ip = c.run_command("curl http://169.254.169.254/latest"
                         "/meta-data/public-ipv4")[1]

    images = []
    # running the glances image
    cmd = ("docker run -d --rm -v /var/run/docker.sock:/var/run/docker.sock:ro"
           " -v /tmp/sizerdata:/app/data:rw tarekziade/sizer-glances")

    ex = "glances -C /app/glances.ini --export-csv /app/data/glances.csv"
    cmd = cmd + ' ' + ex
    images.append(c.run_command(cmd)[1])

    # running the service image
    cmd = 'docker run -t -d -p 8888:8888/tcp --rm kinto/kinto-server'
    images.append(c.run_command(cmd)[1])

    # we're ready
    try:
        yield c
    finally:
        # shutdown everything
        for image in images:
            c.run_command("docker terminate " + image)
            c.run_command("docker rm " + image)


if __name__ == '__main__':
    import requests

    with run_service() as ssm:
        print(requests.get('http://%s:8888/v1/' % ssm.ip).json())
