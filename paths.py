import os

# define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_SIZE = "small"  # options: "tiny", "base", "small", "medium", "large"

# ensure data directory exists
# for local file storage
os.makedirs(DATA_DIR, exist_ok=True)