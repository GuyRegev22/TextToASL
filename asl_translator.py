import ollama

class ASLTranslator:
    def __init__(self, model_name = "mistral"):
        self.model = model_name
        
    def translate(self, sentence=""):

        """
        use the Ollama API to translate a sentence into ASL
        """
        system_prompt = ("""
            You are an expert in American Sign Language (ASL) translation. 
            You **must strictly follow** these instructions without deviation:
            - Use **only** ASL words from the ASL vocabulary.
            - If a word is not in ASL, **replace** it with the closest ASL phrase or **omit it**.
            - Your response **must only contain ASL words**, written in **lowercase** and **separated by spaces**.
            - Do **not** add explanations, extra words, or symbols.
            - If you cannot translate anything, return an **empty string**.

            ⚠️ Failure to follow these rules will be considered an incorrect response.
        """

        )
        
        prompt = f"{system_prompt}\n\nTranslate: '{sentence}'"
        
        response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}], options={"temperature": 0})
        
        return response['message']['content']