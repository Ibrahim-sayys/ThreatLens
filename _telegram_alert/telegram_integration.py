from telegram import Bot
import asyncio

async def send_message_to_channel(token, channel_name, message):
    """
    Sends a message to a specific Telegram channel.

    Args:
        token (str): The API token for the Telegram bot.
        channel_name (str): The name of the Telegram channel (e.g., @ChannelName).
        message (str): The message to send to the channel.
    """
    try:
        async with Bot(token=token) as bot:
            print(f"Sending message to {channel_name}...")
            await bot.send_message(chat_id=channel_name, text=message)
            print(f"✓ Message sent successfully to {channel_name}")
            return True
    except Exception as e:
        print(f"✗ An error occurred: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Verify bot token is correct")
        print(f"2. Ensure bot is admin of the channel")
        print(f"3. Check internet connectivity")
        return False

# Example usage
async def main():
    TOKEN = "8534807443:AAF529s1Q0OcDfBDVb37WTvXEH1SodaTPNI"
    CHANNEL_NAME = "@ThreatLens"
    MESSAGE = "🔒 ThreatLens Alert: This is a test message from ThreatLens security monitoring system."

    print("=" * 60)
    print("ThreatLens - Telegram Integration Test")
    print("=" * 60)

    print("\nSending message...")
    success = await send_message_to_channel(TOKEN, CHANNEL_NAME, MESSAGE)

    print("\n" + "=" * 60)
    if success:
        print("✓ Test completed successfully!")
    else:
        print("✗ Test failed. Please check the troubleshooting steps above.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())


