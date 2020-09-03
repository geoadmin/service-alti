# service-alti

| Branch | Status |
|--------|-----------|
| develop | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiUzFGKzRsYzJaVzdQVTd5VHR0Sng3VEo5dk9uMDYwNUZWcmtMV0pQaGdEcCtJZStxN0YyU3E2ZERxVThLK0lXczNEVG51c0RGSm9pU0NiNHA2L0lGZDdVPSIsIml2UGFyYW1ldGVyU3BlYyI6IjJ6cnVFeVo3V3RPMnJXZlMiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=develop) |
| master | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiUzFGKzRsYzJaVzdQVTd5VHR0Sng3VEo5dk9uMDYwNUZWcmtMV0pQaGdEcCtJZStxN0YyU3E2ZERxVThLK0lXczNEVG51c0RGSm9pU0NiNHA2L0lGZDdVPSIsIml2UGFyYW1ldGVyU3BlYyI6IjJ6cnVFeVo3V3RPMnJXZlMiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master) |

## Summary of the project

Height and profile services for http://api3.geo.admin.ch

## How to run locally

### Dependencies

The **Make** targets assume you have **bash**, **curl**, **tar**, **docker** and **docker-compose** installed.

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

    make lint-format

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