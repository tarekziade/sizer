from sizer.testdrive import run_molotov
from sizer.chart import DockerGraph
from sizer.container import container



if __name__ == '__main__':


    with container("kinto/kinto-server", ports={'8888/tcp': 8888}) as c:
        run_molotov("https://github.com/tarekziade/sizer", 
                    "http://localhost:8888/v1/",
                    "normal")

        graph = DockerGraph(c.name, "/tmp/sizerdata/glances.csv")
        graph.create()
