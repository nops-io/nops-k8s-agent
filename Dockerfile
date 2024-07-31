FROM python:3.11-slim

WORKDIR /tmp/build

# Install live dependencies.
RUN pip install --upgrade pip


COPY requirements.txt requirements.txt
RUN \
    mkdir /workspace && \
    pip3 install -r requirements.txt

# If this argument is present then we're installing developer dependencies.
ARG debug
COPY requirements.dev.txt requirements.dev.txt
RUN if [ ! -z "$debug" ]; then pip3 install -r requirements.dev.txt; fi

# Cleanup
RUN rm -rf /tmp/build

WORKDIR /workspace
COPY nops_k8s_agent .
