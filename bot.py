import asyncio
import datetime
from botbuilder.core import ActivityHandler, TurnContext, CardFactory, MessageFactory
from botbuilder.schema import ChannelAccount, Attachment
from config import DefaultConfig
from crawler import MenuCrawler
from ai_service import NutritionAI

class MenuBot(ActivityHandler):
    def __init__(self):
        self.crawler = MenuCrawler()
        self.ai = NutritionAI()
        self.config = DefaultConfig()

    # --------------------------------------------------------
    # [도우미] 괄호 제거 및 반찬 분리
    # --------------------------------------------------------
    def safe_split_menu(self, text):
        items = []
        buffer = ""
        paren_depth = 0
        for char in text:
            if char == '(': paren_depth += 1
            elif char == ')': paren_depth -= 1
            
            if char == ',' and paren_depth == 0:
                if buffer.strip(): items.append(buffer.strip())
                buffer = ""
            else:
                buffer += char
        if buffer.strip(): items.append(buffer.strip())
        return items

    # --------------------------------------------------------
    # [도우미] 영양성분 숫자 -> 문자열 포맷팅
    # --------------------------------------------------------
    def format_nutrition(self, data):
        """ {'kcal': 300, 'carbs': 65...} -> '🔥 300kcal...' """
        if not data:
            return ""
        k = data.get('kcal', 0)
        c = data.get('carbs', 0)
        p = data.get('protein', 0)
        f = data.get('fat', 0)
        return f"🔥 {k}kcal | 🍚 탄:{c}g | 🥚 단:{p}g | 🧀 지:{f}g"

    # --------------------------------------------------------
    # [디자인] 카드 생성 (Total 계산 로직 포함)
    # --------------------------------------------------------
    def create_daily_menu_card(self, date_str, menu_list, nutrition_map={}) -> Attachment:
        body_elements = [
            {
                "type": "TextBlock",
                "text": f"📅 {date_str} 식단",
                "weight": "Bolder",
                "size": "Large",
                "color": "Accent"
            }
        ]

        for menu in menu_list:
            # 코너명
            body_elements.append({
                "type": "TextBlock",
                "text": menu['corner'],
                "weight": "Bolder",
                "size": "Medium",
                "spacing": "Medium",
                "color": "Dark"
            })

            columns = []
            if menu['img']:
                columns.append({
                    "type": "Column",
                    "width": "auto",
                    "items": [{"type": "Image", "url": menu['img'], "size": "Small", "style": "Person"}]
                })

            text_items = []

            # -------------------------------------------------
            # 1. 모든 메뉴 아이템 수집 및 총합 계산 (Total Sum)
            # -------------------------------------------------
            main_name = menu['main']
            side_names = []
            
            raw_side = menu['side']
            if raw_side:
                parts = self.safe_split_menu(raw_side)
                for p in parts:
                    clean_name = p.split('|')[0].strip() # 파이프 앞부분만
                    side_names.append(clean_name)

            # 총합 변수 초기화
            total_stats = {'kcal': 0, 'carbs': 0, 'protein': 0, 'fat': 0}
            
            # 메인 메뉴 데이터 가져오기
            main_data = nutrition_map.get(main_name, {})
            if main_data:
                for k in total_stats:
                    total_stats[k] += main_data.get(k, 0)

            # 반찬 데이터 가져오기 및 총합 누적
            for s_name in side_names:
                s_data = nutrition_map.get(s_name, {})
                if s_data:
                    for k in total_stats:
                        total_stats[k] += s_data.get(k, 0)

            # -------------------------------------------------
            # 2. 메인 메뉴 출력 (여기에 Total Sum 표시)
            # -------------------------------------------------
            text_items.append({
                "type": "TextBlock",
                "text": main_name, 
                "weight": "Bolder",
                "wrap": True,
                "size": "Default"
            })
            
            # [핵심] 메인 메뉴 밑에는 '식단 전체 총합'을 출력
            if nutrition_map: # 분석 데이터가 있을 때만
                total_str = self.format_nutrition(total_stats)
                text_items.append({
                    "type": "TextBlock",
                    "text": f"Total: {total_str}", # Total 표시
                    "wrap": True,
                    "size": "Small",
                    "color": "Attention", # 주황색 강조
                    "weight": "Bolder",
                    "spacing": "None"
                })

            # -------------------------------------------------
            # 3. 반찬 출력 (개별 성분 표시)
            # -------------------------------------------------
            if raw_side:
                parts = self.safe_split_menu(raw_side)
                for item in parts:
                    title = item
                    desc = ""
                    if '|' in item:
                        splitted = item.split('|')
                        title = splitted[0].strip()
                        desc = splitted[1].strip() if len(splitted) > 1 else ""

                    # 반찬 개별 데이터 찾기
                    s_data = nutrition_map.get(title, {})
                    s_str = self.format_nutrition(s_data)

                    # 반찬 이름
                    text_items.append({
                        "type": "TextBlock",
                        "text": f"• {title}",
                        "isSubtle": True, "wrap": True, "size": "Small", "spacing": "Small"
                    })
                    
                    # 반찬 개별 영양성분
                    if s_str:
                        text_items.append({
                            "type": "TextBlock",
                            "text": f"   {s_str}",
                            "wrap": True,
                            "size": "Small",
                            "color": "Good", # 초록색 계열 (총합과 구분)
                            "spacing": "None"
                        })
                    
                    if desc:
                        text_items.append({"type": "TextBlock", "text": f"   └ {desc}", "isSubtle": True, "wrap": True, "size": "Small", "spacing": "None"})

            columns.append({
                "type": "Column",
                "width": "stretch",
                "items": text_items,
                "verticalContentAlignment": "Center"
            })

            body_elements.append({"type": "ColumnSet", "columns": columns, "spacing": "Small"})
            body_elements.append({"type": "Container", "style": "emphasis", "height": "1px", "bleed": True, "spacing": "Small"})

        if len(body_elements) > 0 and body_elements[-1].get("height") == "1px":
            body_elements.pop()

        return CardFactory.adaptive_card({
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": body_elements
        })

    # ... (create_menu_selection_card 등 나머지 부분은 동일) ...

    def create_menu_selection_card(self) -> Attachment:
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {"type": "TextBlock", "text": "🍱 프레시밀 & AI 영양사", "weight": "Bolder", "size": "Medium"},
                {"type": "TextBlock", "text": "원하시는 메뉴를 선택해주세요.", "wrap": True}
            ],
            "actions": [
                {"type": "Action.Submit", "title": "🍚 오늘 식단 + AI 분석", "data": {"action": "today_menu"}},
                {"type": "Action.Submit", "title": "📅 주간 전체 보기 (빠름)", "data": {"action": "week_menu"}},
                {"type": "Action.Submit", "title": "🤖 주간 식단 + AI 분석 (느림)", "data": {"action": "week_menu_ai"}}
            ]
        }
        return CardFactory.adaptive_card(card_data)

    async def on_members_added_activity(self, members_added: ChannelAccount, turn_context: TurnContext):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(MessageFactory.attachment(self.create_menu_selection_card()))

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.value:
            data = turn_context.activity.value
            if isinstance(data, dict):
                action = data.get("action")
            else:
                return

            loop = asyncio.get_event_loop()
            kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
            
            if action == "today_menu":
                await turn_context.send_activity("🤖 전체 영양 성분을 정밀 계산 중입니다...")
                today_str = kst_now.strftime("%Y%m%d")
                daily_data = await loop.run_in_executor(None, self.crawler.get_menu_data, today_str)
                
                if not daily_data:
                    await turn_context.send_activity(f"오늘({today_str})은 식단이 없습니다.")
                else:
                    date_key = list(daily_data.keys())[0]
                    menu_list = daily_data[date_key]
                    
                    # 수집
                    all_food_items = []
                    for menu in menu_list:
                        all_food_items.append(menu['main'])
                        if menu['side']:
                            sides = self.safe_split_menu(menu['side'])
                            for side in sides:
                                name = side.split('|')[0].strip()
                                all_food_items.append(name)
                    
                    # 분석 (숫자 데이터 받기)
                    nutrition_map = await loop.run_in_executor(None, self.ai.analyze_menu_list, all_food_items)
                    
                    # 카드 생성 (Total 계산 로직 적용)
                    card = self.create_daily_menu_card(date_key, menu_list, nutrition_map)
                    await turn_context.send_activity(MessageFactory.attachment(card))

            elif action == "week_menu":
                await turn_context.send_activity("📅 주간 식단을 불러옵니다...")
                weekly_data = await loop.run_in_executor(None, self.crawler.get_menu_data)
                if not weekly_data:
                    await turn_context.send_activity("데이터가 없습니다.")
                else:
                    cards = []
                    for date in sorted(weekly_data.keys()):
                        card = self.create_daily_menu_card(date, weekly_data[date], {})
                        cards.append(card)
                    await turn_context.send_activity(MessageFactory.carousel(cards))

            elif action == "week_menu_ai":
                await turn_context.send_activity("🤖 주간 식단을 정밀 분석 중입니다... (시간 소요)")
                weekly_data = await loop.run_in_executor(None, self.crawler.get_menu_data)
                if not weekly_data:
                    await turn_context.send_activity("데이터가 없습니다.")
                else:
                    cards = []
                    for date in sorted(weekly_data.keys()):
                        menu_list = weekly_data[date]
                        all_food_items = []
                        for menu in menu_list:
                            all_food_items.append(menu['main'])
                            if menu['side']:
                                sides = self.safe_split_menu(menu['side'])
                                for side in sides:
                                    all_food_items.append(side.split('|')[0].strip())
                        
                        nutrition_map = await loop.run_in_executor(None, self.ai.analyze_menu_list, all_food_items)
                        card = self.create_daily_menu_card(date, menu_list, nutrition_map)
                        cards.append(card)
                    
                    await turn_context.send_activity(MessageFactory.carousel(cards))
            
            await turn_context.send_activity(MessageFactory.attachment(self.create_menu_selection_card()))
        else:
            await turn_context.send_activity(MessageFactory.attachment(self.create_menu_selection_card()))