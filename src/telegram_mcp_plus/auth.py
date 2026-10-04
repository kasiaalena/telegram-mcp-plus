import sys
import asyncio
import argparse

from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

from telegram_mcp_plus.client import get_client


async def async_main(phone: str, password: str | None = None):
    client = get_client()
    try:
        await client.connect()

        print(f"Sending code to {phone}...")
        await client.send_code_request(phone)

        code = input("Enter the code from Telegram: ")

        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            if password is None:
                password = input("Two-factor authentication enabled. Enter your password: ")
            await client.sign_in(password=password)
        except PhoneCodeInvalidError:
            print("Error: The code you entered is invalid.", file=sys.stderr)
            sys.exit(1)

        me = await client.get_me()
        display = me.first_name or ""
        if me.last_name:
            display += f" {me.last_name}"
        if me.username:
            display += f" (@{me.username})"
        print(f"Authorized successfully as {display} (id={me.id})")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Authorize Telegram MCP Plus")
    parser.add_argument("--phone", required=True, help="Phone number with country code")
    parser.add_argument("--password", help="2FA password (if enabled)")
    args = parser.parse_args()
    asyncio.run(async_main(args.phone, args.password))


if __name__ == "__main__":
    main()
