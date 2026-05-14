"""
Telegram Bot — AI Агенти спілкуються в реальному часі
"""

import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

# ══════════════════════════════════════════
# КОНФІГ
# ══════════════════════════════════════════
API_TOKEN = "8671899772:AAHSxvZ5Lv6WmHdH401W5nd8ecrsci3EoFQ"
GEMINI_API_KEY = "AIzaSyDaGBmEAzbQUD9Q0NjR7Jxj0JWTJwpc54s"

# ══════════════════════════════════════════
# АГЕНТИ
# ══════════════════════════════════════════
AGENTS = [
    {
        "name": "🔬 Дослідник",
        "system": (
            "Ти — професійний дослідник. Твоя задача: проаналізувати тему, "
            "знайти ключові факти, цифри, і передати їх Копірайтеру. "
            "Відповідай чітко і структуровано. Максимум 5 пунктів. "
            "В кінці завжди пиши: 'Передаю Копірайтеру.'"
        ),
    },
    {
        "name": "🧠 Критик",
        "system": (
            "Ти — суворий критик і fact-checker. "
            "Тобі дали аналіз Дослідника. Знайди слабкі місця, "
            "задай уточнюючі питання або вкажи на що треба звернути увагу. "
            "Максимум 3 зауваження. "
            "В кінці пиши: 'Передаю Копірайтеру з поправками.'"
        ),
    },
    {
        "name": "✍️ Копірайтер",
        "system": (
            "Ти — майстер Telegram-контенту. "
            "Тобі дали дослідження і критику. "
            "Напиши фінальний пост для Telegram: "
            "короткий, влучний, з емодзі, максимум 200 слів. "
            "Починай одразу з тексту посту, без вступу."
        ),
    },
]

# ══════════════════════════════════════════
# LLM
# ══════════════════════════════════════════
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
    )

async def ask_agent(agent: dict, conversation: list[dict]) -> str:
    """Запитує агента з урахуванням всього діалогу."""
    llm = get_llm()
    messages = [SystemMessage(content=agent["system"])]

    # Додаємо контекст попередніх повідомлень
    if conversation:
        context = "\n\n".join(
            f"{msg['agent']}: {msg['text']}" for msg in conversation
        )
        messages.append(HumanMessage(
            content=f"Ось що вже сказали інші агенти:\n\n{context}"
        ))

    response = await asyncio.to_thread(llm.invoke, messages)
    return response.content.strip()

# ══════════════════════════════════════════
# HANDLERS
# ══════════════════════════════════════════
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привіт!\n\n"
        "Напиши мені будь-яку тему — і мої агенти почнуть обговорення прямо тут:\n\n"
        "🔬 <b>Дослідник</b> — збере факти\n"
        "🧠 <b>Критик</b> — перевірить і доповнить\n"
        "✍️ <b>Копірайтер</b> — напише фінальний пост\n\n"
        "Просто напиши тему 👇",
        parse_mode="HTML"
    )

async def handle_topic(message: types.Message):
    topic = message.text.strip()

    # Стартове повідомлення
    await message.answer(
        f"🚀 <b>Тема:</b> {topic}\n\n"
        f"Агенти починають роботу...",
        parse_mode="HTML"
    )

    conversation = []

    for i, agent in enumerate(AGENTS):
        # Повідомлення "друкує..."
        typing_msg = await message.answer(f"{agent['name']} думає... ✍️")

        try:
            response = await ask_agent(agent, conversation)
        except Exception as e:
            await typing_msg.delete()
            await message.answer(f"❌ Помилка у агента {agent['name']}: {e}")
            return

        # Видаляємо "думає..." і показуємо відповідь
        await typing_msg.delete()
        await message.answer(
            f"{agent['name']}\n\n{response}",
            parse_mode="HTML"
        )

        conversation.append({
            "agent": agent["name"],
            "text": response
        })

        # Пауза між агентами для ефекту діалогу
        if i < len(AGENTS) - 1:
            await asyncio.sleep(1)

    await message.answer("✅ <b>Обговорення завершено!</b>", parse_mode="HTML")

# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(cmd_start, CommandStart())
    dp.message.register(handle_topic, F.text)

    print("✅ Бот з агентами запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
