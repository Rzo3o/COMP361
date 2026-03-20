from ui.game_window import GameWindow
from ui.menu import SaveSelectMenu
import os
import shutil

if __name__ == "__main__":
    menu = SaveSelectMenu()
    res = menu.run()
    
    if res and res[0]:
        slot, selected_skin = res
        target_db = f"game_data_{slot}.db"
        
        # If the save file doesn't exist, create it from default.db (template)
        if not os.path.exists(target_db):
            if os.path.exists("default.db"):
                print(f"Creating new save slot {slot} from default.db...")
                shutil.copy("default.db", target_db)
            else:
                print("No default.db found! Starting with empty database.")
        
        game = GameWindow(slot, selected_skin)
        game.run()
