# import pygame

# # please install "python -m pip install pytest" to import
# from gameplay.world import *
# import tkinter as tk
# from main import GameWindow
# from GameDB import *
import unittest
from database.db_manager import DatabaseManager
from gameplay.world import World
from gameplay.engine import GameEngine
from visuals.asset_manager import get_asset
import unittest
from ui.game_window import GameWindow


class SmokeTests(unittest.TestCase):

    def setUp(self):
        """Runs before every test."""
        # Use a temporary database for testing
        self.db = DatabaseManager("test_game.db")

        # Create a test session
        self.session_id = self.db.create_session(1)

    def tearDown(self):
        """Cleanup after tests."""
        self.db.close()

    def test_database_initialization(self):
        """Database should initialize correctly."""
        self.assertIsNotNone(self.db)

    def test_create_session(self):
        """Session should be created."""
        session = self.db.get_session(1)
        self.assertIsNotNone(session)

    def test_world_load(self):
        """World should load tiles and player."""
        world = World(self.db, self.session_id)

        self.assertIsNotNone(world)
        self.assertIsNotNone(world.player)

    def test_engine_start(self):
        """GameEngine should initialize."""
        engine = GameEngine(self.db, self.session_id)

        self.assertIsNotNone(engine.world)
        self.assertIsNotNone(engine.world.player)

    def test_player_move(self):
        """Player movement should run without crashing."""
        engine = GameEngine(self.db, self.session_id)

        result = engine.handle_input("MOVE_NORTH")

        self.assertEqual(result, "TURN_TAKEN")

    def test_fog_of_war_runs(self):
        """Fog of war update should not crash."""
        world = World(self.db, self.session_id)
        world.update_fog_of_war()
        self.assertTrue(True)

    def test_get_tile(self):
        """World should be able to return a tile."""
        world = World(self.db, self.session_id)

        tile = world.get_tile(0, 0)

        # Tile may be None depending on map, but call should succeed
        self.assertTrue(True)

    def test_player_damage(self):
        """Player should take damage correctly."""
        world = World(self.db, self.session_id)

        player = world.player
        old_hp = player.hp

        player.take_damage(10)

        self.assertLessEqual(player.hp, old_hp)

    def test_save_player(self):
        """Saving player state should not crash."""
        world = World(self.db, self.session_id)

        self.db.save_player(self.session_id, world.player)

        self.assertTrue(True)

    def test_database_close(self):
        """Database should close without crashing."""
        self.db.close()
        self.assertTrue(True)
    
    def test_game_over_state(self):
        """Engine should return GAME_OVER if player is dead."""
        engine = GameEngine(self.db, self.session_id)

        engine.world.player.dead = True

        result = engine.handle_input("MOVE_NORTH")

        self.assertEqual(result, "GAME_OVER")

    def test_player_death(self):
        """Player death should set dead flag."""
        world = World(self.db, self.session_id)

        player = world.player
        player.take_damage(999)

        self.assertTrue(player.dead)


if __name__ == "__main__":
    unittest.main()
