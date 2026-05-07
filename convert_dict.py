import pandas as pd
import json
import os

# Paths
INPUT_CSV = "khmer_dictionary.csv"
OUTPUT_JSON = "backend/models/unigrams.json"

def convert_csv_to_json():
    print(f"📖 Reading {INPUT_CSV}...")
    
    # Load the CSV
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"❌ Error: Cannot find {INPUT_CSV}. Make sure it is in the same folder.")
        return

    # Create the Hash Map (Dictionary)
    # We assign a default "frequency" of 1 to every word just to keep the data structure 
    # compatible with our FastAPI backend logic.
    print("⚙️ Converting to Hash Map...")
    khmer_dict = {}
    for word in df['word'].dropna():  # .dropna() ignores any empty rows
        clean_word = str(word).strip()
        if clean_word:
            khmer_dict[clean_word] = 1 

    # Ensure the models folder exists
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

    # Save to JSON
    print(f"💾 Saving {len(khmer_dict)} words to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(khmer_dict, f, ensure_ascii=False)

    print("✅ Conversion complete! Your backend is ready to go.")

if __name__ == "__main__":
    convert_csv_to_json()