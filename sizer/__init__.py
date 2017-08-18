import contextlib
import docker
from testdrive import run_molotov


class Docker(object):
    def __init__(self):
        self._client = docker.from_env()
        self._containers = []

    def deploy(self, name, **kw):
        try:
            self._client.images.get(name)
        except docker.errors.ImageNotFound:
            print("Pulling %r" % name)
            self._client.images.pull(name)

        if 'tty' not in kw:
            kw['tty'] = True
        if 'stdin_open' not in kw:
            kw['stdin_open'] = True
        print("Deploying %r" % name)
        cont = self._client.containers.run(name, detach=True, **kw)
        print("%r deployed (%r)" % (cont.name, cont.short_id))
        self._containers.append(cont)

    @contextlib.contextmanager
    def run(self, name, **kw):
        volumes = {'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'ro'}}
        self.deploy("sizer/glances", pid_mode="host", 
                    volumes=volumes)
        self.deploy(name, **kw)
        yield
        self.terminate()

    def terminate(self):
        for cont in self._containers:
            print("Killing %r (%r)" % (cont.name, cont.short_id))
            try:
                cont.kill()
            finally:
                cont.remove()



if __name__ == '__main__':

    d = Docker()

    with d.run("kinto/kinto-server", ports={'8888/tcp': 8888}):
        run_molotov("https://github.com/tarekziade/sizer", 
                    "http://localhost:8888/v1/",
                    "normal")
