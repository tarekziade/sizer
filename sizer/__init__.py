import time
import os

from sizer.testdrive import run_molotov
from sizer.chart import DockerGraph
from sizer.ssm import run_service
from sizer.ec2 import launch_instance


def main():
    # XXX todo, reuse existing instance
    iid = launch_instance()

    with run_service(iid) as ssm:
        time.sleep(5)
        server = 'http://%s:8888/v1/' % ssm.ip
        os.environ['SERVER_URL'] = server

        run_molotov("https://github.com/tarekziade/sizer",
                    server, "normal")
    graph = DockerGraph("tested",
                        "/tmp/sizerdata/glances.csv")

    title = "Resources usage for %s on a %s"
    graph.create(title % ("kinto", "t2.micro"))


if __name__ == '__main__':
    main()
