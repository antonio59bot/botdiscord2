import discord
import sys

print("Discord version:", discord.__version__)
print("Has app_commands:", hasattr(discord, 'app_commands'))

try:
    import discord.app_commands
    print("Import discord.app_commands: SUCCESS")
except ImportError:
    print("Import discord.app_commands: FAILED")

try:
    from discord import app_commands
    print("Import from discord import app_commands: SUCCESS")
except ImportError:
    print("Import from discord import app_commands: FAILED")

sys.exit(0)
