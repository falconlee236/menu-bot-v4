import requests
import datetime
import json
from config import DefaultConfig

class MenuCrawler:
    def __init__(self):
        self.config = DefaultConfig()
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://front.cjfreshmeal.co.kr/",
            "Origin": "https://front.cjfreshmeal.co.kr",
            "Accept": "application/json"
        }

    def _fetch_week_data(self):
        url = f"{self.config.API_BASE_URL}/week-meal"
        params = {"storeIdx": self.config.STORE_IDX, "weekType": "1"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            response.raise_for_status()
            raw_data = response.json().get("data")
            
            # 데이터 평탄화 (Flatten)
            all_meals = []
            if isinstance(raw_data, dict):
                for day_schedule in raw_data.values():
                    if isinstance(day_schedule, dict):
                        for meal_list in day_schedule.values():
                            if isinstance(meal_list, list):
                                all_meals.extend(meal_list)
            return all_meals
        except Exception as e:
            print(f"API Error: {e}")
            return []

    # [변경] 텍스트가 아니라 '리스트'를 반환하도록 수정
    def get_menu_data(self, target_date=None):
        try:
            data = self._fetch_week_data()
            if not data: return []

            # 날짜별로 그룹화
            daily_menu = {} # Key: 날짜, Value: [메뉴리스트]

            for meal in data:
                if not isinstance(meal, dict): continue
                
                # 날짜 포맷 (YYYYMMDD -> MM.DD)
                raw_date = str(meal.get("mealDt", ""))
                if len(raw_date) == 8:
                    fmt_date = f"{raw_date[4:6]}.{raw_date[6:8]}"
                else:
                    fmt_date = raw_date
                
                # 특정 날짜만 원할 경우 필터링 (오늘 메뉴용)
                if target_date and raw_date != target_date:
                    continue

                if fmt_date not in daily_menu:
                    daily_menu[fmt_date] = []

                # 필요한 정보만 정제해서 저장
                menu_info = {
                    "corner": meal.get("corner", "") or meal.get("name", ""), # 코너명
                    "main": meal.get("name", ""),      # 메인 메뉴
                    "side": meal.get("side", ""),      # 반찬
                    "img": meal.get("thumbnailUrl", ""), # 이미지 URL
                    "kcal": meal.get("kcal", 0)        # 칼로리 (있으면 좋음)
                }
                
                # 중복 제거 및 추가
                daily_menu[fmt_date].append(menu_info)

            return daily_menu

        except Exception as e:
            print(f"Parsing Error: {e}")
            return {}