import time
import os
import json
import sys
import requests

from sizer.testdrive import run_molotov
from sizer.chart import DockerGraph
from sizer.ssm import run_service
from sizer.ec2 import launch_instance
from sizer.util import log

SB = 'https://servicebook-api.stage.mozaws.net/api/project'


def main(project_name, region='eu-west-1', instance_type='t2.micro'):
    log("Reading the servicebook")
    projects = requests.get(SB).json()['data']
    molotov_url = docker = None
    for project in projects:
        if project['name'].lower() == project_name.lower():
            for test in project['tests']:
                if test['name'].lower() == 'sizer':
                    molotov_url, docker = test['url'].split('#')
            if molotov_url is None:
                log("The project was found but it misses a sizer test")
                sys.exit(1)
                return

    if molotov_url is None:
        log("The project was not found in the Service Book")
        sys.exit(1)
        return

    configfile = os.path.join(os.path.expanduser('~'), '.sizer')
    if not os.path.exists(configfile):
        config = {}
    else:
        with open(configfile) as f:
            config = json.loads(f.read())

    iid = config.get(region, {}).get(instance_type)
    if not iid:
        iid = launch_instance(region, instance_type)
        if region not in config:
            config[region] = {}
        config[region][instance_type] = iid
    else:
        log("Reusing Instance %r" % iid)

    try:
        with run_service(docker, iid) as ssm:
            time.sleep(5)
            server = 'http://%s:8888/v1/' % ssm.ip
            os.environ['SERVER_URL'] = server
            run_molotov(molotov_url, server, "sizer")

        graph = DockerGraph("tested",
                            "/tmp/sizerdata/glances.csv")

        title = "Resources usage for %s on a %s"
        graph.create(title % ("kinto", "t2.micro"))
    finally:
        with open(configfile, 'w') as f:
            f.write(json.dumps(config))


if __name__ == '__main__':
    main(sys.argv[1])
