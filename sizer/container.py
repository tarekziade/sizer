import contextlib
import docker


class DockerContainer(object):
    def __init__(self, image_name):
        self._client = docker.from_env(timeout=10)
        self._containers = []
        self.image_name = image_name

    def _deploy(self, name, **kw):
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
        return cont

    def run(self, **kw):
        volumes = {'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'ro'},
                   '/tmp/sizerdata': {'bind': '/app/data', 'mode': 'rw'}}
        self._deploy("sizer/glances", pid_mode="host",
                    volumes=volumes)
        cont = self._deploy(self.image_name, **kw)
        self.name = cont.name

    def terminate(self):
        for cont in self._containers:
            print("Killing %r (%r)" % (cont.name, cont.short_id))
            try:
                cont.kill()
            except docker.errors.APIError:
                pass
            finally:
                cont.remove()


@contextlib.contextmanager
def container(image_name, **options):
    c = DockerContainer(image_name)
    c.run(**options)
    try:
    	yield c
    finally:
    	c.terminate()
