import os
import time

from discord_webhook import DiscordWebhook, DiscordEmbed


def format_details(details):
    """Format the details to be sent in the discord message"""
    formatted_details = ""
    for key, value in details.items():
        if isinstance(
            value, dict
        ):  # Si la valeur est un dictionnaire, itérez à l'intérieur
            formatted_details += f"**{key}:**\n"
            for subkey, subvalue in value.items():
                formatted_details += f"\t{subkey}: {subvalue}\n"
        else:
            formatted_details += f"**{key}:** {value}\n"
    return formatted_details


class DiscordService:
    """A class to interact with the Discord bot"""

    def __init__(self):
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.webhook = DiscordWebhook(url=webhook_url)

    def post_message(self, title, description, details=None, error=None):
        """Post a message in the channel with the webhook"""
        self.webhook.rate_limit_retry = True

        if error:
            embed = DiscordEmbed(
                title=title,
                color="ff0000",
                timestamp=int(time.time()),
                fields=[
                    {
                        "name": "Description",
                        "value": description,
                        "inline": False,
                    },
                    {
                        "name": "Error",
                        "value": error[:1024],
                        "inline": False,
                    },
                ],
                author={
                    "name": "Deployment Bot",
                },
            )
        else:
            formatted_details = format_details(details)
            embed = DiscordEmbed(
                title=title,
                color="00ff00",
                timestamp=int(time.time()),
                fields=[
                    {
                        "name": "Description",
                        "value": description,
                        "inline": False,
                    },
                    {
                        "name": "Details",
                        "value": formatted_details,
                        "inline": False,
                    },
                ],
                author={
                    "name": "Deployment Bot",
                },
            )

        self.webhook.add_embed(embed)
        self.webhook.execute(remove_embeds=True)
