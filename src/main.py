import time
import logging
import os
import threading
from flask import Flask, request, jsonify
from jsonschema.exceptions import ValidationError
import grpc

from git_utils import GitService
from docker_utils import DockerService
from utils import validate_deploy_config, copy_env_to_git_repo
from discord_bot import DiscordService

# Import the generated gRPC classes
import py_protos.deployAgent_pb2_grpc as deployAgent_pb2_grpc
import py_protos.deployAgent_pb2 as deployAgent_pb2

app = Flask(__name__)

DOCKER_REGISTRY_URL = os.environ["DOCKER_REGISTRY_URL"]
CLONE_DIR = os.environ["CLONE_DIR"]
HOSTS = {
    "hogwarts-1": "192.168.2.51",
    "hogwarts-2": "192.168.2.64",
    "hogwarts-3": "65.109.65.105",
}


def handle_repository_deploiement(payload: dict) -> dict:
    """Handle the deployment of the repository

    Args:
        payload (dict): the payload received from the webhook

    Returns:
        dict: the response to send back
    """

    timings = {}
    t0 = time.time()
    repo_name = payload["repository"]["name"]

    # Start logger
    logging.basicConfig(filename=f"/app/logs/{repo_name}.log", level=logging.DEBUG)

    try:
        DOCKER_SERVICE = DockerService()
        GIT_SERVICE = GitService()
        DISCORD_SERVICE = DiscordService()

        # Clone the repository and get the deploy configuration
        GIT_SERVICE.clone_repository(payload, timings)
        deploy_config = GIT_SERVICE.get_deploy_config()

        # Validate the deploy configuration provided in the repository
        validate_deploy_config(deploy_config)
        logging.info("Deploy config is valid")

        # Handle the environment file
        env_file = deploy_config["config"]["docker"].get("envFile")
        env_deploy_type = deploy_config["config"]["docker"].get("envDeployType")
        IMAGE_NAME = deploy_config["config"]["docker"]["imageName"]
        IMAGE_TAG = deploy_config["config"]["docker"]["imageTag"]

        # Construct the environment file in bytes format to be sent to the agent
        # The environment file needs to be sent as bytes to the agent with grpc
        env_bytes = f"IMAGE_TAG={IMAGE_TAG}\n".encode("utf-8")
        if env_file is not None and env_deploy_type == "file":
            copy_env_to_git_repo(env_file, CLONE_DIR)
            env_bytes += open(env_file, "rb").read()

        # Change the working directory to the cloned repository
        os.chdir(CLONE_DIR)

        # Build and push the docker image
        DOCKERFILE = deploy_config["config"]["docker"]["dockerfileLocation"]
        COMPOSE_FILE = deploy_config["config"]["docker"]["composeFile"]
        HOST_NAME = deploy_config["config"]["docker"].get("host", "hogwarts-1")

        DOCKER_SERVICE.build_docker_image(IMAGE_NAME, DOCKERFILE, IMAGE_TAG, timings)
        DOCKER_SERVICE.push_docker_image(IMAGE_NAME, IMAGE_TAG, timings)

        # Open the grpc channel and send the deployment request to the agent on the specified host
        channel = grpc.insecure_channel(f"{HOSTS[HOST_NAME]}:50051")
        client = deployAgent_pb2_grpc.DeployDockerComposeStub(channel)

        docker_compose_bytes = open(COMPOSE_FILE, "rb").read()
        agent_req = deployAgent_pb2.DeployDockerComposeRequest(
            dockerComposeYaml=docker_compose_bytes,
            envFile=env_bytes,
            serviceName=IMAGE_NAME,
        )
        agent_res = client.Deploy(agent_req)
        channel.close()
        if agent_res.message != "Success":
            return jsonify({"status": "ERROR", "message": "Deployment failed"}), 500

        t1 = time.time()
        image_name = f"{DOCKER_REGISTRY_URL}/{IMAGE_NAME}:{IMAGE_TAG}"
        image_details = DOCKER_SERVICE.get_image_details(image_name)
        
        os.chdir("/app")

        deployment_details = {
            "status": "OK",
            "message": "Deployment completed successfully",
            "image_name": image_name,
            "image_size": image_details.get("Size"),
            "repository": image_details.get("Repository"),
            "tag": image_details.get("Tag"),
            "timings": timings,
            "total_time": round(t1 - t0, 2),
        }
        DISCORD_SERVICE.post_message(
            title="Deployment completed",
            description=f'Deployment of {repo_name} on branch {payload["ref"].split("/")[-1]} to {HOST_NAME} completed successfully',
            details=deployment_details,
        )

    except ValidationError as e:
        logging.error(e)
        DISCORD_SERVICE.post_message(
            title="Invalid deploy configuration",
            description=f"The deploy configuration for {repo_name} is invalid",
            error=str(e),
        )
    except Exception as e:
        logging.error(e)
        DISCORD_SERVICE.post_message(
            title="Deployment failed",
            description=f'Deployment of {repo_name} on branch {payload["ref"].split("/")[-1]} failed',
            error=str(e),
        )

@app.errorhandler(403)
def forbidden(e):
    """Handle the 403 error formatting"""
    return jsonify({"status": "ERROR", "message": "Forbidden"}), 403


@app.route("/", methods=["POST"])
def handle_webhook():
    """Handle the webhook sent by the git service

    Returns:
        json: A json response with the status of the deployment
    """

    # Verify the signature of the request used for authentication
    GIT_SERVICE = GitService()
    GIT_SERVICE.verify_signature(
        request.data,
        request.headers.get("X-Hub-Signature-256"),
    )

    # Check if the event is a ping event
    if request.headers.get("X-GitHub-Event") == "ping":
        return jsonify({"status": "OK", "message": "Ping event received"}), 200

    payload = request.get_json()

    # Start the deployment process in a new thread to avoid blocking the webhook
    threading.Thread(target=handle_repository_deploiement, args=(payload,)).start()

    return jsonify({"status": "OK", "message": "Deployment started"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
