import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.openf1_service import OpenF1Service

radio = OpenF1Service.get_team_radio(session_key=9157)
race_control = OpenF1Service.get_race_control(session_key=9157)
print(f"[DEBUG] session_key=9157 - Team Radio messages count: {len(radio)}")
print(f"[DEBUG] session_key=9157 - Race Control messages count: {len(race_control)}")
if radio:
    print(f"Sample radio: {radio[0]}")
if race_control:
    print(f"Sample race control: {race_control[0]}")
