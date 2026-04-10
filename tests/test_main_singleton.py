import main


class _DummyScreen:
    instances = 0

    def __init__(self, manager):
        self.manager = manager
        type(self).instances += 1

    def handle_event(self, event):
        return None

    def draw(self):
        return None


class _DummySurface:
    def get_size(self):
        return (800, 600)


class _DummyInfo:
    current_w = 1024
    current_h = 768


class _DummyClock:
    def tick(self, fps):
        return None


def test_screen_manager_is_singleton(monkeypatch):
    main.ScreenManager._screenManager_instance = None
    main.ScreenManager._initialized = False
    _DummyScreen.instances = 0

    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.time, "get_ticks", lambda: 123)
    monkeypatch.setattr(main.pygame.time, "Clock", lambda: _DummyClock())
    monkeypatch.setattr(main.pygame.display, "set_caption", lambda title: None)
    monkeypatch.setattr(main.pygame.display, "Info", lambda: _DummyInfo())
    monkeypatch.setattr(
        main.pygame.display,
        "set_mode",
        lambda size, flags=0: _DummySurface(),
    )

    for module_name in (
        "screen1",
        "screen2",
        "screen3",
        "screen4",
        "screen5",
        "screen6",
        "screen7",
        "screen8",
    ):
        module = getattr(main, module_name)
        for class_name in (
            "Welcome",
            "Winner",
            "GameRules",
            "MainMenu",
            "Characters",
            "SaveSelectMenu",
            "GameWindow",
            "GameOver",
        ):
            if hasattr(module, class_name):
                monkeypatch.setattr(module, class_name, _DummyScreen)

    manager1 = main.ScreenManager()
    manager2 = main.ScreenManager()

    assert manager1 is manager2
    assert _DummyScreen.instances == 1
    assert manager1.current_screen is manager2.current_screen
    assert manager1.width == 800
    assert manager1.height == 600
