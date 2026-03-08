import os
from database.db_manager import DatabaseManager


def test_create_session_creates_session_and_player_state(tmp_path, monkeypatch):
    project_root = os.path.dirname(os.path.dirname(__file__))
    monkeypatch.chdir(project_root)

    db_path = tmp_path / "test_game_data.db"
    db = DatabaseManager(db_file=str(db_path))

    try:
        session_id = db.create_session(slot_id=1, char_type="warrior")

        session = db.get_session(1)
        assert session is not None
        assert session["id"] == session_id
        assert session["slot_number"] == 1
        assert session["character_type"] == "warrior"

        player = db.get_player_state(session_id)
        assert player is not None
        assert player["session_id"] == session_id
        assert player["current_q"] == 0
        assert player["current_r"] == 0
        assert player["health"] == 100
        assert player["max_health"] == 100
        assert "texture_file" in player

    finally:
        db.close()


def test_create_session_same_slot_resets_existing_session(tmp_path, monkeypatch):
    project_root = os.path.dirname(os.path.dirname(__file__))
    monkeypatch.chdir(project_root)

    db_path = tmp_path / "test_game_data.db"
    db = DatabaseManager(db_file=str(db_path))

    try:
        sid1 = db.create_session(slot_id=2, char_type="warrior")

        class DummyPlayer:
            q = 5
            r = -3
            hp = 42
            hunger = 10
            xp = 99

        db.save_player(sid1, DummyPlayer())

        sid2 = db.create_session(slot_id=2, char_type="mage")

        assert sid1 == sid2

        session = db.get_session(2)
        assert session["id"] == sid1
        assert session["character_type"] == "mage"

        player = db.get_player_state(sid1)
        assert player["current_q"] == 0
        assert player["current_r"] == 0
        assert player["health"] == 100
        assert player["max_health"] == 100

        db.cursor.execute(
            "SELECT COUNT(*) AS c FROM player_state WHERE session_id=?",
            (sid1,),
        )
        row = db.cursor.fetchone()
        assert row["c"] == 1

    finally:
        db.close()
