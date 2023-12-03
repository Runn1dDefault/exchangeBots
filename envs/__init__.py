from environs import Env

env = Env()

try:
    env.read_env(".env")
    WAIT_MINUTES = env.int('WAIT_MINUTES')
    DISCORD_JOIN_URL = env.str('DISCORD_JOIN_URL')
    RPC_URL = env.str('RPC_URL')
    API_ETHERSCAN_KEY = env.str("API_ETHERSCAN_KEY")
    DISCORD_DISPLAY_BOT_TOKEN = env.str("DISCORD_DISPLAY_BOT_TOKEN")
    DISCORD_BOT_TOKEN = env.str("DISCORD_BOT_TOKEN")
    DISCORD_BOT_GUILD_ID = env.int("DISCORD_BOT_GUILD_ID")
    DISCORD_BOT_ROLE_USER = env.int("DISCORD_BOT_ROLE_USER")
    DISCORD_SERVER = env.str("DISCORD_SERVER")
    DISCORD_REDIRECT_URI = env.str("DISCORD_REDIRECT_URI")
    DISCORD_CLIENT_ID = env.str("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = env.str("DISCORD_CLIENT_SECRET")
    MYSQL_DATABASE = env.str("MYSQL_DATABASE")
    MYSQL_ROOT_PASSWORD = env.str("MYSQL_ROOT_PASSWORD")
    MYSQL_HOST = env.str("MYSQL_HOST")
    MYSQL_INTERNAL_PORT = env.int("MYSQL_INTERNAL_PORT")
    MYSQL_EXTERNAL_PORT = env.int("MYSQL_EXTERNAL_PORT")
except Exception as e:
    print(e)
    exit()
