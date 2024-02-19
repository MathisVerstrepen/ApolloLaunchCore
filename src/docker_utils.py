import subprocess
import time
import json
import os


class DockerService:
    """Service to handle docker operations"""

    def __init__(self) -> None:
        self.registry_url = os.environ["DOCKER_REGISTRY_URL"]

        os.system(
            f'echo "{os.environ["DOCKER_REGISTRY_TOKEN"]}" | docker login --username {os.environ["DOCKER_REGISTRY_USERNAME"]} --password-stdin {self.registry_url}'
        )

    def build_docker_image(
        self, image_name: str, dockerfile: str, image_tag: str, timings: dict
    ) -> None:
        """Build the docker image and tag it with the provided tag

        Args:
            image_name (str): name of the image
            dockerfile (str): path to the dockerfile
            image_tag (str): tag to be used for the image
            timings (dict): dictionary to store the time taken for the operation

        Raises:
            subprocess.CalledProcessError: if the command fails
        """
        t0 = time.time()
        subprocess.run(
            [
                "docker",
                "build",
                "-t",
                f"{self.registry_url}/{image_name}:{image_tag}",
                "-f",
                dockerfile,
                ".",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        timings["build_time"] = round(time.time() - t0, 2)

    def push_docker_image(self, image_name: str, image_tag: str, timings: dict) -> None:
        """Push the docker image to the registry

        Args:
            image_name (str): name of the image
            image_tag (str): tag to be used for the image
            timings (dict): dictionary to store the time taken for the operation

        Raises:
            subprocess.CalledProcessError: if the command fails
        """
        t0 = time.time()
        subprocess.run(
            ["docker", "push", f"{self.registry_url}/{image_name}:{image_tag}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        timings["push_time"] = round(time.time() - t0, 2)

    def get_image_details(self, image_name: str) -> dict:
        """Get the details of the image

        Args:
            image_name (str): name of the image

        Returns:
            dict: details of the image in json format
        """

        result = subprocess.run(
            ["docker", "images", image_name, "--format", "{{ json . }}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return json.loads(result.stdout)
