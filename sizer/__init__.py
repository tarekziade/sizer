import time
import os

from sizer.testdrive import run_molotov
from sizer.chart import DockerGraph
from sizer.ssm import run_service


if __name__ == '__main__':
    with run_service() as ssm:
        time.sleep(5)
        server = 'http://%s:8888/v1/' % ssm.ip
        os.environ['SERVER_URL'] = server

        run_molotov("https://github.com/tarekziade/sizer",
                    server, "normal")

    graph = DockerGraph("Kinto", "/tmp/sizerdata/glances.csv")
    graph.create()
