import shutil
from jsonschema import validate

SCHEMA = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["owner", "name"],
                },
                "docker": {
                    "type": "object",
                    "properties": {
                        "imageName": {"type": "string"},
                        "imageTag": {"type": "string"},
                        "dockerfileLocation": {"type": "string"},
                        "buildArgs": {"type": "array", "items": {"type": "string"}},
                        "composeFile": {"type": "string"},
                    },
                    "required": ["imageName", "imageTag"],
                },
                "deploy": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "enum": ["all-at-once", "rolling", "blue-green"],
                        },
                        "maxRetries": {"type": "number"},
                        "timeout": {"type": "number"},
                    },
                    "required": ["strategy"],
                },
                "environment": {"type": "string", "enum": ["dev", "prod"]},
                "notifications": {
                    "type": "object",
                    "properties": {
                        "onSucess": {"type": "string"},
                        "onFailure": {"type": "string"},
                    },
                },
                "hooks": {
                    "type": "object",
                    "properties": {
                        "preDeploy": {"type": "string"},
                        "postDeploy": {"type": "string"},
                    },
                },
                "secrets": {
                    "type": "object",
                    "properties": {
                        "useSecretManager": {"type": "boolean"},
                        "secretKeys": {"type": "string"},
                    },
                },
                "performance": {
                    "type": "object",
                    "properties": {
                        "maxBuildCpu": {"type": "number"},
                        "maxDeployCpu": {"type": "number"},
                    },
                },
                "healthChecks": {
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string"},
                        "interval": {"type": "number"},
                        "timeout": {"type": "number"},
                    },
                },
                "rollback": {
                    "type": "object",
                    "properties": {
                        "enable": {"type": "boolean"},
                        "previousImageTag": {"type": "string"},
                    },
                },
            },
            "required": ["repository", "docker", "deploy", "environment"],
        }
    },
    "required": ["config"],
}

def validate_deploy_config(deploy_config: dict):
    """Validate the required deploy configuration against the schema

    Args:
        deploy_config (dict): _description_
    """
    validate(deploy_config, SCHEMA)

def copy_env_to_git_repo(env_file: str, clone_dir: str) -> None:
    """Copy the stored environment file to the git repository

    Args:
        env_file (str): the environment file to copy
    """
    shutil.copyfile(f"/app/env/{env_file}", f"{clone_dir}/.env")
