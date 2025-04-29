import ollama
import threading as Threading

class ASLTranslator:
    def __init__(self, model_name = "mistral"):
        self.model = model_name
        self.vocabulary = self.load_asl_vocabulary("asl_dict.txt")

#         self.system_prompt =  (f"""
# You are an American Sign Language (ASL) translator bot.

# You MUST follow these rules exactly and strictly:


# 1. You are FORBIDDEN from inventing, guessing, or generating explanations.

# 2. You must NEVER say anything like "no translation found", "I don't know", or similar responses.

# 3. If the input contains nonsense, gibberish, or anything not matching ASL words:
#    - OMIT it completely and silently.
#    - Do not comment, explain, or acknowledge it.

# 4. DO NOT use any special characters (", (, ), -, ?, !, etc.) and DO NOT use any numbers (0–9).

# 5. Correct minor typos silently.

# 6. Your output must be:
#    - ONLY the translation result: a list of ASL words and/or spelled letters.
#    - All words must be in lowercase, separated by spaces.
#    - Simple, clear, and strictly dictionary words or spelled names/places.
#    - NO commentary, NO extra text, NO apologies, NO explanations.

# ⚠️ Important: You MUST obey these rules perfectly. Output ONLY the translation. Anything else is forbidden.

# """)

# 5. If you detect a person's name or place name that does not exist in ASL:
#    - Spell it out, letter-by-letter, with a space between each letter (e.g., "Guy" → "g u y").
#    - Do not put spaces between other words in the sentence (e.g., "hello my name" should remain as is).

#    - Only names or places should be spelled out with spaces between the letters. Words in the sentence should remain intact.

        self.system_prompt = (f"""
You are an American Sign Language (ASL) translator bot.

You MUST follow these rules exactly and strictly:

1. ONLY use words used in ASL and with ASL syntax.

2. You are FORBIDDEN from inventing, guessing, or generating explanations.

3. You must NEVER say anything like "no translation found", "I don't know", or similar responses.

4. If the input contains nonsense, gibberish, or anything not matching ASL words:
   - OMIT it completely and silently.
   - Do not comment, explain, or acknowledge it.

5. DO NOT use any special characters (/,\,", (, ), -, ?, !, etc.) and DO NOT use any numbers (0–9).

6. Correct minor typos silently.

7. Your output must be:
   - ONLY the translation result: a list of ASL words and/or spelled letters.
   - Simple, clear, and strictly dictionary words or spelled names/places.

8. NO commentary, NO extra text, NO apologies, NO explanations. only the translation result.

9. You need to maintain the original sentence meaning as much as possible.
                              
10. If you are unfamiliar with an existing word just keep it in the sentence while maintaining the meaning of it
                              

⚠️ Important: You MUST obey these rules perfectly. Output ONLY the translation. Anything else is forbidden.
""")

    def translate(self, sentence=""):
        
        """
        use the Ollama API to translate a sentence into ASL
        """
        
        prompt = f"please translate the following sentence into ASL: {sentence}. Follow the rules! "
                
        response = ollama.chat(model=self.model, messages=[{"role": "system", "content": self.system_prompt},{"role": "user", "content": prompt }],
                        options={"temperature": 0.0,          # Low temperature for strictness
                        "top_p":0.1,               # Low top_p to reduce creativity
                        "max_tokens":80,          # Limit the number of tokens (words) to avoid too long responses
                        "frequency_penalty":0.2,   # Penalize repeated words to avoid repetition
                        "presence_penalty":0.4,    # No penalty for new words, since we control it by the dictionary
                        "stop":["\n", "END", "-", "?", "!", "|"],      #define stop tokens needed to prevent over-generation
                        "n":1})
        
        translated = response['message']['content'].lower()
        print(f"Translated: {translated}")
        invalid_words = self.validate_translation(translated)
        print(f"invalid words: {invalid_words}")
        if invalid_words != []:
            print(f"Invalid translation: {translated}. Missing words: {invalid_words}")
            for word in invalid_words:
                translated.replace(word, " ".join(word.split())) # replace the word with its letters separated by spaces

        

        return translated
    

    def validate_translation(self, translation):
        """
        Check if the translation uses only words from the ASL dictionary
        or spelled names (letters separated by spaces).
        """
        words = translation.lower().split()
        missing_words = []
        for word in words:
            if len(word) == 1 and word.isalpha():
                continue  # single letters are OK (for spelling names)
            if word not in self.vocabulary:
                missing_words += word # found a word not in ASL dictionary
        return missing_words

    def load_asl_vocabulary(self, file_path="asl_dict.txt"):
        """
        Load the ASL vocabulary from a file.
        """
        try:
            with open(file_path, 'r') as file:
                asl_words = file.read()
                #print(asl_words)
                asl_words = asl_words.replace("\n", " ")
            return asl_words
        except FileNotFoundError:
            print(f"File {file_path} not found.")
            return []
        except Exception as e:
            print(f"An error occurred while loading the ASL vocabulary: {e}")
            return []
        
