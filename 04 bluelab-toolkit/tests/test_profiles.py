import json
from pathlib import Path

PROFILE = Path(__file__).parents[1] / "profiles" / "approved_gatt.json"


def test_profile_file_is_valid_json_and_has_no_approved_default_writes():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    approved = [value for key, value in data.items() if not key.startswith("_") and isinstance(value, dict) and value.get("documented") is True]
    assert approved == []


def test_example_format_has_conservative_payload_limit():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    example = data["_example_format"]["0000xxxx-0000-1000-8000-00805f9b34fb"]
    assert example["max_payload_bytes"] <= 20
