import os
import json
import re

def clean_description(desc):
    # Remove patterns like ". +20 HP, +15 Hunger", "+10 HP", "Restores 5 Hunger", etc.
    # Pattern 1: ". +X HP, +Y Hunger" at the end
    desc = re.sub(r'[\.,]?\s*\+\d+\s*HP,?\s*\+\d+\s*Hunger$', '.', desc)
    # Pattern 2: "+X HP" or "+X Hunger" preceded by space or comma
    desc = re.sub(r'[,.]?\s*\+\d+\s*(HP|Hunger)', '', desc)
    # Pattern 3: "Restores X Health/Hunger"
    desc = re.sub(r'Restores\s*\d+\s*(Health|Hunger|HP|vitality)', '', desc, flags=re.IGNORECASE)
    # Pattern 4: "gives you" at the end of a sentence
    desc = re.sub(r',\s*gives\s+you\s*[\.,]?$', '.', desc, flags=re.IGNORECASE)
    desc = re.sub(r'gives\s+you\s*[\.,]?$', '.', desc, flags=re.IGNORECASE)
    
    # Strip trailing punctuation/whitespace and ensure it ends with a single period if it made sense
    desc = desc.strip()
    if desc.endswith(','):
        desc = desc[:-1]
    
    if desc and not desc.endswith('.'):
        # Only add a period if the original was a sentence
        if any(char.isalpha() for char in desc):
            desc += '.'
            
    # Cleanup double spaces or weird punctuation left behind
    desc = re.sub(r'\s+', ' ', desc)
    desc = re.sub(r'\.\.+', '.', desc)
    desc = re.sub(r',\.', '.', desc)
    return desc.strip()

items_dir = "assets/definitions/items"
if not os.path.exists(items_dir):
    print(f"Directory {items_dir} not found.")
else:
    for filename in os.listdir(items_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(items_dir, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                
                old_desc = data.get("description", "")
                if old_desc:
                    new_desc = clean_description(old_desc)
                    if old_desc != new_desc:
                        data["description"] = new_desc
                        with open(filepath, "w") as f:
                            json.dump(data, f, indent=4)
                        print(f"Updated {filename}: {old_desc} -> {new_desc}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
