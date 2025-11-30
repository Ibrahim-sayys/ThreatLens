from telegram import Bot

def send_message_to_channel(token, channel_name, message):
    """
    Sends a customized message to a specific Telegram channel.

    Args:
        token (str): The API token for the Telegram bot.
        channel_name (str): The name of the Telegram channel (e.g., @ChannelName).
        message (str): The message to send to the channel.
    """
    try:
        bot = Bot(token=token)
        bot.send_message(chat_id=channel_name, text=message)
        print(f"Message sent successfully to {channel_name}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    TOKEN = "8534807443:AAF529s1Q0OcDfBDVb37WTvXEH1SodaTPNI"
    CHANNEL_NAME = "@ThreatLens"
    MESSAGE = "This is a customized message sent to the ThreatLens channel."

    send_message_to_channel(TOKEN, CHANNEL_NAME, MESSAGE)
