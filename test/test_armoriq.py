from armoriq_sdk import ArmorIQClient
from pathlib import Path

CONFIG = Path(__file__).with_name("armoriq-test.yaml")

client = ArmorIQClient.from_config(str(CONFIG))

print("ArmorIQ client initialized successfully")
