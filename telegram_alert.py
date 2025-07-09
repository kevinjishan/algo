import telegram
import asyncio

TOKEN = '7775843154:AAEe3gqc5Frey-3Y1Tl7n7F8tm6IK80eUG4'
CHAT_ID = 66580946 #여러분의 챗ID값으로 변경!!!

bot = telegram.Bot(token=TOKEN)

async def send_telegram_alert(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg)


def SendMessage(msg):
    try:
        loop = asyncio.get_event_loop()  # 기존 이벤트 루프 가져오기
        if loop.is_running():  # 이미 이벤트 루프가 실행 중인 경우
            loop.create_task(send_telegram_alert(msg))  # 비동기 작업을 추가
        else:
            loop.run_until_complete(send_telegram_alert(msg))  # 새로운 이벤트 루프 실행
    except Exception as ex:
        print(ex)