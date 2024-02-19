import subprocess
import time
import os
import hashlib
import hmac
import shutil
import json

from flask import abort


class GitService:
    """Service to handle git operations"""

    def __init__(self) -> None:
        self.clone_dir = os.environ["CLONE_DIR"]

        # Vérifie si le répertoire existe déjà et le supprime
        if os.path.isdir(self.clone_dir):
            shutil.rmtree(self.clone_dir)
        os.mkdir(self.clone_dir)

    def get_deploy_config(self) -> dict:
        """Get the deploy configuration from the repository.

        Returns:
            dict: deploy configuration
        """
        with open(f"{self.clone_dir}/deployConfig.json", "r", encoding="utf-8") as f:
            deploy_config = json.load(f)
        return deploy_config

    def clone_repository(self, payload: dict, timings: dict):
        """Clone the repository to the specified branch.

        Args:
            payload (dict): payload received from the webhook
            branch (str): branch to clone
            timings (dict): dictionary to store the time taken for the operation
        """
        start_clone_time = time.time()

        repo_branch = payload.get("ref", "").split("/")[-1]
        ssh_url = payload.get("repository", {}).get("ssh_url")

        if not ssh_url:
            raise ValueError("Repository URL is missing!")
        elif not repo_branch:
            raise ValueError("Branch is missing!")

        subprocess.run(
            [
                "git",
                "clone",
                "-b",
                repo_branch,
                ssh_url,
                self.clone_dir,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        timings["clone_time"] = round(time.time() - start_clone_time, 2)

    def verify_signature(self, payload_body: bytes, signature_header: str):
        """Verify that the payload was sent from GitHub by validating SHA256.

        Raise and return 403 if not authorized.

        Args:
            payload_body: original request body to verify (request.body())
            signature_header: header received from GitHub (x-hub-signature-256)

        Source: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries#python-example
        """
        if not signature_header:
            abort(403, "x-hub-signature-256 header is missing!")

        token = os.environ["GITHUB_WEBHOOK_SECRET"].encode("utf-8")
        hash_object = hmac.new(token, msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + hash_object.hexdigest()
        if not hmac.compare_digest(expected_signature, signature_header):
            abort(403, "Request signatures didn't match!")
