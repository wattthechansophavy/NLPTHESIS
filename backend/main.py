import os
import json
import editdistance
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from khmernltk import word_tokenize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("🧠 Loading NLP Dictionaries into memory...")

with open(os.path.join(BASE_DIR, "models", "unigrams.json"), 'r', encoding='utf-8') as f:
    unigrams = json.load(f)

with open(os.path.join(BASE_DIR, "models", "bigrams.json"), 'r', encoding='utf-8') as f:
    bigrams = json.load(f)

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class TextPayload(BaseModel):
    text: str

khmer_common_typos = {
    ('ណ', 'ន'): True, 
    ('ប', 'ផ'): True, 
    ('ឆ', 'ច'): True,
    ('ស', 'ហ'): True,
    ('វ', 'ា'): True 
}

def is_clean_word(word):
    bad_chars = ['«', '»', '”', '“', '"', "'", '(', ')', '[', ']', '{', '}', '!', '?', '.', ',', '។', '៖', 'ៈ', '-', ' ', '\n', '\t']
    if any(c in word for c in bad_chars): return False
    if len(word.strip()) == 0: return False
    if word.isnumeric(): return False
    return True

# --- PHASE 2: THE DE-GLUER ---
# --- PHASE 2: THE DE-GLUER (Patched with Unicode Shield) ---
def split_glued_typo(word):
    if word in unigrams or not is_clean_word(word):
        return [word]
        
    for i in range(len(word)-1, 0, -1):
        prefix = word[:i]
        suffix = word[i:]
        
        # FIX: Forbid splitting if the suffix starts with a dependent vowel, subscript, or diacritic!
        if re.match(r'^[\u17B4-\u17D3]', suffix):
            continue
            
        if prefix in unigrams:
            if len(suffix) > 1: 
                return [prefix, suffix]
                
    for i in range(1, len(word)):
        prefix = word[:i]
        suffix = word[i:]
        
        # FIX: Forbid splitting if the suffix starts with a dependent vowel, subscript, or diacritic!
        if re.match(r'^[\u17B4-\u17D3]', suffix):
            continue
            
        if suffix in unigrams:
            if len(prefix) > 1:
                return [prefix, suffix]
                
    return [word]

# --- PHASE 3: THE RE-JOINER (Patched Cannibal Bug) ---
def should_merge(w1, w2):
    if not is_clean_word(w1) or not is_clean_word(w2):
        return False
    
    combined = w1 + w2
    if combined in unigrams:
        return True
        
    # FIX: ONLY run heavy fuzzy merge if BOTH pieces are broken.
    # Prevents a valid word from swallowing an adjacent short typo.
    if w1 not in unigrams and w2 not in unigrams:
        for vocab_word in unigrams.keys():
            if abs(len(combined) - len(vocab_word)) <= 2:
                if editdistance.eval(combined, vocab_word) <= 2:
                    return True 
    return False

# --- PHASE 4: THE SUGGESTION ENGINE (Patched Diacritic Blindspot) ---
# --- PHASE 4: THE SUGGESTION ENGINE (Universal Diacritic Patch) ---
def get_contextual_suggestions(typo, prev_word=None, next_word=None, max_distance=2):
    candidates = []
    
    # The complete list of crucial Khmer diacritics and shifters
    khmer_diacritics = ['់', '៌', '័', '៏', '៊', '៉']
    
    for vocab_word, unigram_freq in unigrams.items():
        if abs(len(typo) - len(vocab_word)) > max_distance: continue
        
        dist = editdistance.eval(typo, vocab_word)
        if dist <= max_distance:
            score = (dist * 10000) - unigram_freq
            
            # 1. Standard Character Pair Confusion Matrix
            for i in range(min(len(typo), len(vocab_word))):
                char_pair = (typo[i], vocab_word[i])
                if char_pair in khmer_common_typos or char_pair[::-1] in khmer_common_typos:
                    score -= 5000 
            
            # 2. UNIVERSAL DIACRITIC CHECK (Works anywhere in the word)
            # If the edit distance is exactly 1, let's see if it's just a diacritic issue
            if dist == 1:
                if len(vocab_word) > len(typo):
                    # Typo is missing a diacritic
                    for d in khmer_diacritics:
                        if vocab_word.replace(d, '', 1) == typo:
                            score -= 8000 # Massive reward
                            break
                elif len(typo) > len(vocab_word):
                    # Typo has an accidental extra diacritic
                    for d in khmer_diacritics:
                        if typo.replace(d, '', 1) == vocab_word:
                            score -= 8000 # Massive reward
                            break
            
            # 3. Context Integration
            if prev_word:
                back_key = f"{prev_word} {vocab_word}"
                if back_key in bigrams:
                    score -= (bigrams[back_key] * 50000)
                    
            if next_word:
                forward_key = f"{vocab_word} {next_word}"
                if forward_key in bigrams:
                    score -= (bigrams[forward_key] * 50000)

            candidates.append((vocab_word, score))
            
    candidates.sort(key=lambda x: x[1])
    return [word for word, score in candidates[:3]]

@app.post("/check_spelling")
async def check_spelling(payload: TextPayload):
    clean_text = payload.text.replace('\u200b', '')
    if not clean_text.strip(): return {"status": "success", "annotated_text": []}
    
    chunks = re.split(r'([\s។៖ៈ,.\-!?"\'«»”“]+)', clean_text)
    
    annotated_text = []
    checked_words_cache = {} 
    
    for chunk in chunks:
        if not chunk: continue
        
        if not is_clean_word(chunk):
            annotated_text.append({"text": chunk, "is_typo": False, "suggestions": []})
            continue
            
        try:
            raw_words = word_tokenize(chunk, return_tokens=True)
            
            split_words = []
            for w in raw_words:
                split_words.extend(split_glued_typo(w))
            
            chunk_words = []
            skip_next = False
            for i in range(len(split_words)):
                if skip_next:
                    skip_next = False
                    continue
                    
                current_word = split_words[i]
                if i + 1 < len(split_words):
                    next_word = split_words[i+1]
                    if should_merge(current_word, next_word):
                        chunk_words.append(current_word + next_word)
                        skip_next = True
                        continue
                        
                chunk_words.append(current_word)
                
        except Exception as e:
            print(f"Tokenization error on chunk: {chunk} - Error: {e}")
            chunk_words = [chunk]
            
        prev_word = None 
            
        for i, word in enumerate(chunk_words):
            if not is_clean_word(word) or word in unigrams:
                annotated_text.append({"text": word, "is_typo": False, "suggestions": []})
                prev_word = word 
            else:
                next_word = chunk_words[i+1] if i + 1 < len(chunk_words) and is_clean_word(chunk_words[i+1]) else None
                cache_key = f"{prev_word}_{word}_{next_word}"
                
                if cache_key not in checked_words_cache:
                    checked_words_cache[cache_key] = get_contextual_suggestions(word, prev_word, next_word)
                    
                annotated_text.append({"text": word, "is_typo": True, "suggestions": checked_words_cache[cache_key]})
                prev_word = None
                
    return {"status": "success", "annotated_text": annotated_text}