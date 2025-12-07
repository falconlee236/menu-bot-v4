from groq import Groq
import json
from config import DefaultConfig

class NutritionAI:
    def __init__(self):
        self.config = DefaultConfig()
        if not self.config.GROQ_API_KEY or "gsk_" not in self.config.GROQ_API_KEY:
            self.client = None
        else:
            self.client = Groq(api_key=self.config.GROQ_API_KEY)

    def analyze_menu_list(self, items):
        """
        메뉴 리스트를 받아 '숫자 데이터'가 담긴 JSON을 반환
        """
        if not self.client or not items:
            return {}

        items_str = ", ".join(items)
        
        # 프롬프트: 텍스트가 아닌 숫자(Int) 데이터를 요구
        prompt = f"""
        You are a nutritionist. Analyze the nutrition for each item in the list below.
        Menu List: [{items_str}]

        [Rules]
        1. Return ONLY valid JSON.
        2. Key = "Menu Name" (exact match from input), Value = Object with keys: "kcal", "carbs", "protein", "fat".
        3. Values must be Integers (numbers only, no units like 'g' or 'kcal').
        4. Do NOT miss any item. Every item in the list must be in the JSON.
        5. If uncertain, estimate based on general Korean food data.

        [Output Example]
        {{
            "Rice": {{"kcal": 300, "carbs": 65, "protein": 6, "fat": 1}},
            "Kimchi": {{"kcal": 15, "carbs": 3, "protein": 1, "fat": 0}}
        }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Output only JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content
            return json.loads(response_text)
            
        except Exception as e:
            print(f"AI Error: {e}")
            return {}