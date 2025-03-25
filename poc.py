import ollama

def translate_to_asl(sentence):
    system_prompt = (
        "You are an expert in American Sign Language (ASL) translation. "
        "Translate English sentences into ASL, using only words found in ASL vocabulary. "
        "If a word isn't in ASL, replace it with the closest ASL phrase or omit it."
        "I need the response to be consisted only from ASL words without additional text or symbols."
        "Only use the ASL alphabet and numbers seperated by spaces. Do not use any other symbols or characters."
    )
    
    prompt = f"{system_prompt}\n\nTranslate: '{sentence}'"
    
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    
    return response['message']['content']

# Example usage
sentence = "I want to eat a big meal with my family"
asl_translation = translate_to_asl(sentence)
print(asl_translation)
