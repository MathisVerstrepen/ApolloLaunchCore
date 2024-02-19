FROM python:3.9-slim

# Install Docker CLI, git and update certificates
RUN apt-get update \
    && apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
    && echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get install -y git \
    && update-ca-certificates

WORKDIR /app

COPY docker/requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt \
    && mkdir /tmp/repo_clone \
    && mkdir /app/docker-compose \
    && mkdir /app/logs

# Copy the git ssh key and add github.com to known hosts
COPY git/git_ssh_key /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa \
    && ssh-keyscan -t rsa github.com >> /root/.ssh/known_hosts

# Compile proto files and fix known import issue
COPY ./protos /app/protos
RUN mkdir /app/py_protos \
    && python3 -m grpc_tools.protoc -I /app/protos --python_out=/app/py_protos --grpc_python_out=/app/py_protos /app/protos/deployAgent.proto \
    && sed -i 's/import deployAgent_pb2 as deployAgent__pb2/from . import deployAgent_pb2 as deployAgent__pb2/g' /app/py_protos/deployAgent_pb2_grpc.py \
    && touch /app/py_protos/__init__.py

COPY src/ env/ /app/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1\
    PYTHONIOENCODING=utf-8\
    FLASK_APP=main.py

EXPOSE 8080

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080", "--reload"]
# CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]