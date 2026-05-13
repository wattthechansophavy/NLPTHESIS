import pandas as pd
import requests
import time

EXCEL_FILE = "testSet.xlsx"
API_URL = "http://127.0.0.1:8000/check_spelling"

def run_evaluation():
    print("📊 Loading Golden Dataset...")
    try:
        # Note: Using your exact column headers from the screenshot
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {EXCEL_FILE}. Make sure it's in the same folder.")
        return

    TP = 0  # True Positives
    FN = 0  # False Negatives
    FP = 0  # False Positives
    Top3_Hits = 0 

    print(f"🚀 Testing {len(df)} sentences against the NLP Engine...\n")
    start_time = time.time()

    for index, row in df.iterrows():
        # Using the exact headers from your screenshot (including the 'Imput' typo!)
        correct_sentence = str(row['Imput sentence']).strip().replace('\u200b', '')
        typo_sentence = str(row['Imput Typos']).strip().replace('\u200b', '')

        if correct_sentence == 'nan' or typo_sentence == 'nan':
            continue # Skip empty rows

        try:
            response = requests.post(API_URL, json={"text": typo_sentence})
            data = response.json()
            annotated_text = data.get("annotated_text", [])
        except Exception as e:
            print(f"API Error on row {index + 1}: {e}")
            continue

        sentence_has_tp = False

        for item in annotated_text:
            word = item["text"].strip()
            is_typo = item["is_typo"]
            suggestions = item["suggestions"]

            if is_typo:
                # If the flagged word does NOT exist in the correct sentence, it found the malformed typo!
                if word not in correct_sentence:
                    TP += 1
                    sentence_has_tp = True
                    
                    # String Reconstruction Test for Accuracy
                    # Try swapping the typo with the AI's suggestions to see if it fixes the whole sentence
                    for k in range(min(3, len(suggestions))):
                        test_sentence = ""
                        for sub_item in annotated_text:
                            if sub_item == item:
                                test_sentence += suggestions[k]
                            else:
                                test_sentence += sub_item['text']
                        
                        if test_sentence.strip() == correct_sentence:
                            Top3_Hits += 1
                            break # It successfully reconstructed the target!
                else:
                    # It flagged a word that actually belongs in the correct sentence
                    FP += 1

        # If it finished the sentence and never flagged a malformed word
        if not sentence_has_tp:
            
            FN += 1

    # --- CALCULATE THE METRICS ---
    Recall = (TP / (TP + FN)) * 100 if (TP + FN) > 0 else 0
    Precision = (TP / (TP + FP)) * 100 if (TP + FP) > 0 else 0
    F1_Score = (2 * (Precision * Recall) / (Precision + Recall)) if (Precision + Recall) > 0 else 0
    Accuracy = (Top3_Hits / TP) * 100 if TP > 0 else 0

    end_time = time.time()

    # --- THE TERMINAL REPORT ---
    print("========================================")
    print("🏆 KHMER NLP ENGINE EVALUATION REPORT")
    print("========================================")
    print(f"Time Taken:   {round(end_time - start_time, 2)} seconds")
    print(f"Total Tested: {len(df)} sentences\n")
    
    print("--- RAW CONFUSION MATRIX ---")
    print(f"True Positives (TP):  {TP} (Typos successfully caught)")
    print(f"False Negatives (FN): {FN} (Typos missed completely)")
    print(f"False Positives (FP): {FP} (Valid words falsely flagged)\n")
    
    print("--- FINAL PERCENTAGES ---")
    print(f"Detection Rate (Recall): {round(Recall, 2)}%")
    print(f"Precision:               {round(Precision, 2)}%")
    print(f"F1-Score:                {round(F1_Score, 2)}%")
    print(f"Top-3 Suggestion Acc.:   {round(Accuracy, 2)}%")
    print("========================================")

if __name__ == "__main__":
    run_evaluation()