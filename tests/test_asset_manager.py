import unittest
import pygame
from visuals.asset_manager import AssetManager
from core.config import Config

class TestAssetManagerSmoke(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.am = AssetManager()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_asset_manager_initialized(self):
        """AssetManager should initialize without crashing."""
        self.assertIsNotNone(self.am.layouts)
        self.assertIsNotNone(self.am.anim_metadata)

    def test_get_layout_returns_tuple(self):
        """get_layout should always return a (scale, x_shift, y_shift) tuple."""
        layout = self.am.get_layout("non_existing.png")
        self.assertIsInstance(layout, tuple)
        self.assertEqual(len(layout), 3)

    def test_get_image_returns_surface_or_none(self):
        """get_image should return a Pygame Surface or None if missing."""
        surf = self.am.get_image("non_existing.png")
        self.assertTrue(surf is None or isinstance(surf, pygame.Surface))

    def test_get_anim_frame_returns_surface_or_none(self):
        """get_anim_frame should return a Surface for valid animation or fallback."""
        surf = self.am.get_anim_frame("non_existing.png", 0)
        self.assertTrue(surf is None or isinstance(surf, pygame.Surface))

    def test_caching_works(self):
        """Repeated calls should return the same cached object."""
        surf1 = self.am.get_image("non_existing.png")
        surf2 = self.am.get_image("non_existing.png")
        self.assertEqual(surf1, surf2)

if __name__ == "__main__":
    unittest.main()