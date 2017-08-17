=====
Sizer
=====

Sizer uses Glances, Molotov, Docker and AWS to try to perform a sizing for a 
web service.

Given a Molotov test and a Docker image for the service, Sizer
does the following steps:

- Run a CoreOS instance of a given VM size
- Deploy the Docker image of the service on the instance
- Run the Molotov test on it, with the autosize feature
- Shutdown everything
- Display a report of CPU, Memory and I/O usage for the instance using Glances


Example::

    $ sizer --vm-instance=m4.large --docker=kintowe --molotov https://github.com/testrepo 
    Starting a m4.large with CoreOS... OK
    Setting up probes... OK
    Deploying kintowe... OK
    Running Molotov...
    ...
    Shutting down everything... OK
     
    
