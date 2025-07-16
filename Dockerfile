FROM python:3.9-slim-bookworm
ENV HTTP_PORT 8080
RUN groupadd -g 1000 geoadmin && useradd -u 1000 -s /bin/false -g geoadmin geoadmin


# HERE : install relevant packages
# NOTE: curl is required for vhost health check, could be removed when moving to k8s
RUN apt-get update \
  && apt-get -y install \
       curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && pip3 install pipenv \
    && pipenv --version

COPY Pipfile* /tmp/
RUN cd /tmp && \
    pipenv install --system --deploy --ignore-pipfile

WORKDIR /app
COPY --chown=geoadmin:geoadmin ./ /app/

ARG GIT_HASH=unknown
ARG GIT_BRANCH=unknown
ARG GIT_DIRTY=""
ARG VERSION=unknown
ARG AUTHOR=unknown
LABEL git.hash=$GIT_HASH
LABEL git.branch=$GIT_BRANCH
LABEL git.dirty="$GIT_DIRTY"
LABEL version=$VERSION
LABEL author=$AUTHOR

# Overwrite the version.py from source with the actual version
RUN echo "APP_VERSION = '$VERSION'" > /app/app/version.py

USER geoadmin

EXPOSE $HTTP_PORT

# Use a real WSGI server
ENTRYPOINT ["python3", "wsgi.py"]
