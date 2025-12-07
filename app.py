import sys
import traceback
from aiohttp import web
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity

from config import DefaultConfig
from bot import MenuBot

# 1. 설정 불러오기
CONFIG = DefaultConfig()

# 2. Config를 딕셔너리 형태로 변환 (CloudAdapter가 딕셔너리를 요구함)
MSG_CONFIG = {
    "MicrosoftAppId": CONFIG.MicrosoftAppId,
    "MicrosoftAppPassword": CONFIG.MicrosoftAppPassword,
    "MicrosoftAppTenantId": CONFIG.MicrosoftAppTenantId,
    "MicrosoftAppType": CONFIG.MicrosoftAppType,
}

print(MSG_CONFIG)

# 3. 인증 및 어댑터 생성 (최신 방식)
AUTH = ConfigurationBotFrameworkAuthentication(MSG_CONFIG)
ADAPTER = CloudAdapter(AUTH)

# 에러 핸들러
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("봇에 오류가 발생했습니다.")

ADAPTER.on_turn_error = on_error

# 봇 인스턴스 생성
BOT = MenuBot()

# 4. 메인 라우트 핸들러
async def messages(req: web.Request) -> web.Response:
    return await ADAPTER.process(req, BOT)

# 웹 서버 생성
app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        print(f"🚀 Server running on http://0.0.0.0:{CONFIG.PORT}")
        web.run_app(app, host="0.0.0.0", port=CONFIG.PORT)
    except Exception as error:
        raise error