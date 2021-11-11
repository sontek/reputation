####################################################
# Start of the Build step. This is the base used
# for both dev and production
####################################################
FROM ubuntu:20.10 as build
ENV POETRY_VIRTUALENVS_CREATE=false
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York


WORKDIR /srv
EXPOSE 8000

RUN apt-get update
RUN apt-get install \
      curl \
      build-essential \
      libffi-dev \
      libssl-dev \
      libyaml-dev \
      patchelf \
      python3.9 \
      python3.9-dev \
      python3-distutils \
      docker.io \
      unzip \
      -y

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.9 get-pip.py

RUN python3.9 -m pip install --upgrade \
      pip \
      setuptools \
      poetry \
      auditwheel


# Copy dependency file up first, we only want
# to de-cache to install layer if dependencies
# change.
COPY pyproject.toml poetry.lock ./

# Don't install dev tools in this step.  We'll install
# them in the dev step.  This allows us to avoid
# bringing them to production
RUN poetry install --no-dev

# Currently poetry isn't great at doing wheels, so we
# are going to use pip for that
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes
RUN python3.9 -m pip wheel -w wheelhouse -r requirements.txt
COPY wheely.sh .
RUN ./wheely.sh

COPY . .

# Build the package here just to verify that it is
# packaged properly.  Only production will use it.
RUN poetry build


####################################################
# Start of the Developer step. This is what is used
# on a daily run in docker-compose.
####################################################

FROM build as dev
WORKDIR /srv

# Re-run install but with dev dependencies this time
RUN poetry install

CMD [ "uvicorn", "baddies.server:app", "--host", "0.0.0.0", "--reload", "--debug" ]



####################################################
# Start of the production step.
####################################################
FROM ubuntu as prod
WORKDIR /srv
RUN apt-get update
RUN apt-get install \
      python3.9 \
      python3-pip \
      -y

COPY --from=build /srv/wheelhouse/ ./wheelhouse
COPY --from=build /srv/dist/ ./dist/

RUN python3.9 -m pip install --no-index --find-links ./wheelhouse/ wheelhouse/*.whl
RUN python3.9 -m pip install --no-index --find-links ./wheelhouse/ dist/*.whl

CMD [ "gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "baddies.server:app", "--bind", "0.0.0.0" ]
