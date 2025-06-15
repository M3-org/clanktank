import csv
import os
import re
import json
from pathlib import Path

def sanitize_filename(name):
    # Remove or replace characters that are problematic in filenames
    if not name:
        return "unnamed_character"
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def create_character_folders(csv_path):
    # Create base characters directory
    base_dir = Path("characters")
    base_dir.mkdir(exist_ok=True)
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Extract character name for folder creation
            character_name = row.get("Character Name (Pitcher)", "").strip()
            if not character_name:
                character_name = "Unnamed Character"
                
            # Create sanitized folder name
            folder_name = sanitize_filename(character_name)
            char_dir = base_dir / folder_name
            char_dir.mkdir(exist_ok=True)
            
            # Create README content with all information
            readme_content = f"""# {character_name}

## Project Details
- **Project Title**: {row.get("Project Title", "")}
- **Submission ID**: {row.get("Submission ID", "")}
- **Respondent ID**: {row.get("Respondent ID", "")}
- **Submitted at**: {row.get("Submitted at", "")}

## Creator Information
- **Name**: {row.get("Name", "")}
- **Contact Info**: {row.get("Contact Info", "")}
- **Discord/Telegram**: {row.get("Discord and/or Telegram username", "")}

## 3D Model Status
- **Has Existing Model**: {row.get("Do you have a 3D model of your character?", "No")}
- **Wants to Commission**: {row.get("Do you want to commission one? Prices start at 4 sol", "No")}
- **Voice Details**: {row.get("Custom Voice? You'll need to send sample audio if yes", "")}

## Character Information
{row.get("Character Info", "")}

## Pitch Information
{row.get("Pitch Info", "")}
"""
            
            # Write README file
            readme_path = char_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as readme:
                readme.write(readme_content)
            
            # Also save complete raw data as JSON for reference
            json_path = char_dir / "raw_data.json"
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(dict(row), json_file, indent=2, ensure_ascii=False)
            
            print(f"Created folder and files for {character_name}")

if __name__ == "__main__":
    csv_path = "blocktank.csv"
    create_character_folders(csv_path)
    print("Character folders creation complete!")
