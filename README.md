# service-alti

| Branch | Status |
|--------|-----------|
| develop | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiK2FITjNBUmhiQ2J2cjdwM3hsT1ByeStsZkFSaVFHcTBzSDBrNSs3RDAwZm1penhYVzJiWVhmRHJaYmZDRm1Ed1MwdGIxVVYxc294dFA2aWhnTUtXRUFNPSIsIml2UGFyYW1ldGVyU3BlYyI6IkNXTmIrTlptaHBnVE5kQkMiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=develop) |
| master | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiK2FITjNBUmhiQ2J2cjdwM3hsT1ByeStsZkFSaVFHcTBzSDBrNSs3RDAwZm1penhYVzJiWVhmRHJaYmZDRm1Ed1MwdGIxVVYxc294dFA2aWhnTUtXRUFNPSIsIml2UGFyYW1ldGVyU3BlYyI6IkNXTmIrTlptaHBnVE5kQkMiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master) |

- [Summary of the project](#summary-of-the-project)
- [How to run locally](#how-to-run-locally)
  - [Dependencies](#dependencies)
  - [Setting up to work](#setting-up-to-work)
  - [Linting and formatting your work](#linting-and-formatting-your-work)
  - [Test your work](#test-your-work)
- [Versioning](#versioning)
- [Endpoints](#endpoints)
  - [/checker GET](#checker-get)
  - [`/rest/services/height` GET](#restservicesheight-get)
  - [`/rest/services/profile.json` and `/rest/services/profile.csv` GET/POST](#restservicesprofilejson-and-restservicesprofilecsv-getpost)
- [Deploying the project and continuous integration](#deploying-the-project-and-continuous-integration)
  - [Deployment configuration](#deployment-configuration)

## Summary of the project

Height and profile services for http://api3.geo.admin.ch

## How to run locally

### Dependencies

The **Make** targets assume you have **bash**, **curl**, **python3.9**, **pipenv**, **docker** and **docker-compose** installed.

### Setting up to work

First, you'll need to clone the repo

    git clone git@github.com:geoadmin/service-alti.git

Then, you can run the setup target to ensure you have everything needed to develop, test and serve locally

    make setup

That's it, you're ready to work.

### Linting and formatting your work

In order to have a consistent code style the code should be formatted using `yapf`. Also to avoid syntax errors and non
pythonic idioms code, the project uses the `pylint` linter. Both formatting and linter can be manually run using the
following command:

    make format-lint

**Formatting and linting should be at best integrated inside the IDE, for this look at
[Integrate yapf and pylint into IDE](https://github.com/geoadmin/doc-guidelines/blob/master/PYTHON.md#yapf-and-pylint-ide-integration)**

### Test your work

Testing if what you developed work is made simple. You have four targets at your disposal. **test, serve, gunicornserve, dockerrun**

    make test

This command run the integration and unit tests.

    make serve

This will serve the application through Flask without any wsgi in front.

    make gunicornserve

This will serve the application with the Gunicorn layer in front of the application

    make dockerrun

This will serve the application with the wsgi server, inside a container.
To stop serving through containers,

    make shutdown

Is the command you're looking for.

## Versioning

This service uses [SemVer](https://semver.org/) as versioning scheme. The versioning is automatically handled by `.github/workflows/main.yml` file.

See also [Git Flow - Versioning](https://github.com/geoadmin/doc-guidelines/blob/master/GIT_FLOW.md#versioning) for more information on the versioning guidelines.

## Endpoints

### /checker GET

this is a simple route meant to test if the server is up.

### `/rest/services/height` GET

http://api3.geo.admin.ch/services/sdiservices.html#height

### `/rest/services/profile.json` and `/rest/services/profile.csv` GET/POST

http://api3.geo.admin.ch/services/sdiservices.html#profile

## Deploying the project and continuous integration

When creating a PR, it should run a codebuild job to test, build and push automatically your PR as a tagged container.

This service is to be deployed to the Kubernetes cluster once it is merged.

TO DO: give instructions to deploy to kubernetes.

### Deployment configuration

The service is configured by Environment Variable:

| Env                  | Default                   | Description                            |
|----------------------|---------------------------|----------------------------------------|
| HTTP_PORT            | `'5000'`                  | HTTP port of the service               |
| LOGGING_CFG          | `'logging-cfg-local.yml'` | Logging configuration file             |
| LOGS_DIR             | `'./logs'`                | Directory for logging output files     |
| DTM_BASE_PATH        | `'/var/local/profile/'`   | Raster and COMB files location         |
| PRELOAD_RASTER_FILES | `False`                   | Preload raster files at startup. If not set they will be loaded during first request |
| ALTI_WORKERS         | `0`                       | Number of workers. `0` or negative value means that the number of worker are computed from the number of cpu |
| DFT_CACHE_HEADER     | `public, max-age=86400`   | Default cache settings for successful GET, HEAD and OPTIONS requests |
| GUNICORN_WORKER_TMP_DIR | `None` | This should be set to an tmpfs file system for better performance. See https://docs.gunicorn.org/en/stable/settings.html#worker-tmp-dir. |
