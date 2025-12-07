# config.py
import os

class DefaultConfig:
    """ Bot Configuration """
    PORT = 7753
    # APP_ID = ""
    # APP_PASSWORD = ""
    
    MicrosoftAppId = os.environ.get("MicrosoftAppId", "YOUR_APP_ID")
    MicrosoftAppPassword = os.environ.get("MicrosoftAppPassword", "YOUR_APP_PASSWORD")
    MicrosoftAppTenantId = os.environ.get("MicrosoftAppTenantId", "YOUR_TENANT_ID")
    MicrosoftAppType = os.environ.get("MicrosoftAppType", "SingleTenant")
    # secret id: 7ce880e0-0fe2-4e86-9c75-ae5b056af9ea
    
    # 식당 정보
    STORE_IDX = "5978" 
    
    # [중요] 찾아낸 진짜 API 주소
    API_BASE_URL = "https://front.cjfreshmeal.co.kr/meal/v1"

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
