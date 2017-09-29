import time
import os
import json
import sys
import requests
import argparse

from sizer.testdrive import run_molotov
from sizer.chart import DockerGraph
from sizer.ssm import run_service
from sizer.ec2 import launch_instance
from sizer.util import log

SB = 'https://servicebook-api.stage.mozaws.net/api/project'


def _parser():
    parser = argparse.ArgumentParser(description='Autosizer.')

    parser.add_argument('project_name', help="name of the project")

    parser.add_argument('--instance-type', default="t2.micro", type=str,
                        help="AWS Instance Type",
                        choices=['t2.micro', 't2.small', 't2.medium',
                                 't2.large', 't2.xlarge', 'tx.2xlarge',
                                 'm4.large', 'm4.xlarge', 'm4.2xlarge',
                                 'm4.4xlarge', 'm4.10xlarge', 'm4.16xlarge',
                                 'm3.medium', 'm3.large', 'm3.xlarge',
                                 'm3.xlarge', 'm3.2xlarge', 'c4.large',
                                 'c4.xlarge', 'c4.2xlarge', 'c4.4xlarge',
                                 'c4.8xlarge', 'c3.large', 'c3.xlarge',
                                 'c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge'])

    parser.add_argument('--region', default="eu-west-1", type=str,
                        help='AWS Region', choices=['eu-west-1'])

    return parser


def main(args=None):
    if args is None:
        args = _parser().parse_args()

    project_name = args.project_name
    region = args.region
    instance_type = args.instance_type
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
        iid, ssm_client = launch_instance(region, instance_type)
        if region not in config:
            config[region] = {}
        config[region][instance_type] = iid
        with open(configfile, 'w') as f:
            f.write(json.dumps(config))
        log("Please run the same command again.")
        sys.exit(0)
    else:
        ssm_client = None
        log("Reusing Instance %r" % iid)

    try:
        with run_service(docker, iid, ssm_client) as ssm:
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
