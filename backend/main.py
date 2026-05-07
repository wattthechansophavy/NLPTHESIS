import os
import json
import editdistance
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from khmernltk import word_tokenize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("Loading NLP Dictionaries into memory...")

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

# 2.The Context-Aware Suggestion Engine
def get_contextual_suggestions(typo, prev_word=None, max_distance=2):
    candidates = []
    
    for vocab_word, unigram_freq in unigrams.items():
        if abs(len(typo) - len(vocab_word)) > max_distance: continue
        
        dist = editdistance.eval(typo, vocab_word)
        if dist <= max_distance:
            # Base logic: heavily penalize distance, slightly reward overall popularity
            score = (dist * 10000) - unigram_freq
            
            
            # If we know the word right before the typo, check our Bigram model!
            if prev_word:
                bigram_key = f"{prev_word} {vocab_word}"
                if bigram_key in bigrams:
                    bigram_freq = bigrams[bigram_key]
                    # If the words belong together, give it a massive mathematical advantage
                    score -= (bigram_freq * 100000)
            # ---------------------

            candidates.append((vocab_word, score))
            
    # Sort by lowest score first
    candidates.sort(key=lambda x: x[1])
    return [word for word, score in candidates[:3]]

def is_clean_word(word):
    bad_chars = ['«', '»', '”', '“', '"', "'", '(', ')', '[', ']', '{', '}', '!', '?', '.', ',', '។', '៖', 'ៈ', '-', ' ', '\n', '\t']
    if any(c in word for c in bad_chars): return False
    if len(word.strip()) == 0: return False
    if word.isnumeric(): return False
    return True

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
            chunk_words = word_tokenize(chunk, return_tokens=True)
        except Exception as e:
            print(f"Tokenization error on chunk: {chunk} - Error: {e}")
            chunk_words = [chunk]
            
        # 3. Track the "Previous Word" to feed the context engine
        prev_word = None 
            
        for word in chunk_words:
            if not is_clean_word(word) or word in unigrams:
                annotated_text.append({"text": word, "is_typo": False, "suggestions": []})
                prev_word = word # This valid word becomes the context for the next word
            else:
                # Cache key MUST include context now, because suggestions change based on prev_word!
                cache_key = f"{prev_word}_{word}"
                
                if cache_key not in checked_words_cache:
                    checked_words_cache[cache_key] = get_contextual_suggestions(word, prev_word)
                    
                annotated_text.append({"text": word, "is_typo": True, "suggestions": checked_words_cache[cache_key]})
                
                # We break the context chain on a typo so we don't build assumptions on garbage data
                prev_word = None
                
    return {"status": "success", "annotated_text": annotated_text}