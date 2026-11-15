APP_NAME = "PrimeToolv3"
CLI_NAME = "prime-tool-v3"

GITHUB_OWNER = "arjunss057"
GITHUB_REPOSITORY = "prime-tool-v3"

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPOSITORY}"
GITHUB_RELEASES_URL = f"{GITHUB_API_URL}/releases"
GITHUB_LATEST_RELEASE_URL = f"{GITHUB_RELEASES_URL}/latest"

REQUEST_TIMEOUT = 30
CHUNK_SIZE = 1024*64
MAX_DOWNLOAD_SIZE = 100*1024*1024

REQUIRED_ASSETS = {
    "tool.py",
    "requirements.txt",
    "checksums.txt"
}