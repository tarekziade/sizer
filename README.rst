=====
Sizer
=====


Sizer deploys a Docker on AWS and load tests it until it breaks,
then reports on the CPU, Memory, Network and I/O usage.

This tool can be useful to get a sense of how an application
behaves under stress.

Before you can use sizer, you need the following:

- A Docker image of the service to test.
- A Molotov test that runs against the service.
- A new url in the service book in the tests, called "sizer".
  The url is the URL of the Molotov repo, followed by "#" and the name of the docker
  image.

For testing a Kinto server, the values can be:

- Docker: kinto/kinto-server
- Molotov Repo: https://github.com/tarekziade/sizer
- "sizer" entry in the service book: https://github.com/tarekziade/sizer#kinto/kinto-server

Next, make sure you have an Amazon user with the AmazonSSMFullAccess permission
and a valid ~/.boto configuration file.

Once this is in place, sizer can be executed from the command-line with::

    $ sizer kinto
    Reading the servicebook
    Reusing Instance 'i-06a6057664002caab'
    Starting SSM client on i-06a6057664002caab
    Getting the instance public IP...
    Instance IP is 54.154.224.238
    Starting kinto/kinto-server...
    ...


The first run will take ages because the tool needs to deploy an
SSM-enabled EC2 instance and that takes a while. But once it's done
it should be fairly fast on the next runs.

When instances are created, they are left on AWS to be reused or
can be wiped out after the test is over with an option.

If you don't wipe them, the REAPER will automatically do it after some
time.

