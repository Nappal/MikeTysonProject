import asyncio
import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated

TOKEN = "7808257839:AAENbKC5teVZlQvZBTBcE0wzcKtaA5GR2mg"
CHAT_ID = -1002572579294

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

EMOJI_POOL = [
    "🍀", "💀", "👾", "🌍", "📄", "💻",
    "🎯", "🧠", "🦴", "👑", "🧨", "🧩",
    "🐍", "🐉", "🦊", "🐺", "🦅", "🦂",
    "🕷", "🦇", "🐲", "🐯", "🐸", "🐵"
]

CAPTCHA_BUTTONS = 6
user_captcha = {}
user_invites = {}
user_lang = {}

def language_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]]
    )

def captcha_keyboard(emojis):
    buttons = [
        InlineKeyboardButton(text=e, callback_data=f"captcha:{e}")
        for e in emojis
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons[:3],
            buttons[3:6]
        ]
    )

def rules_keyboard(lang):
    text = "I have read the rules" if lang == "en" else "С правилами ознакомился"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="rules_ok")]]
    )

async def send_captcha(message: types.Message, lang: str):
    emojis = random.sample(EMOJI_POOL, CAPTCHA_BUTTONS)
    correct = random.choice(emojis)
    user_captcha[message.from_user.id] = correct

    text = (
        "🔒 <b>To get the chat invite link, please complete the captcha:</b>\n"
        f"Select {correct} on the keyboard"
        if lang == "en"
        else
        "🔒 <b>Для получения ссылки на чат, пройдите простую капчу:</b>\n"
        f"Выберите на клавиатуре {correct}"
    )

    await message.answer(text, reply_markup=captcha_keyboard(emojis))

@dp.message(Command("start"))
async def start(message: types.Message):
    try:
        member = await bot.get_chat_member(CHAT_ID, message.from_user.id)
        if member.status in ("kicked", "banned"):
            await message.answer("❌ <b>Вы заблокированы в нашем чате</b>")
            return
    except:
        pass

    await message.answer(
        "🌐 <b>Выберите язык / Select language:</b>",
        reply_markup=language_keyboard()
    )
    try:
        await message.delete()
    except:
        pass

@dp.callback_query(lambda c: c.data in ("lang_ru", "lang_en"))
async def choose_language(callback: types.CallbackQuery):
    lang = "en" if callback.data == "lang_en" else "ru"
    user_lang[callback.from_user.id] = lang

    try:
        member = await bot.get_chat_member(CHAT_ID, callback.from_user.id)
        if member.status in ("kicked", "banned"):
            await callback.message.edit_text("❌ <b>Вы заблокированы в нашем чате</b>")
            await callback.answer()
            return

        if member.status in ("member", "administrator", "creator"):
            text = (
                "❌ <b>You are already a member of our chat</b>"
                if lang == "en"
                else "❌ <b>Вы уже присутствуете в нашем чате</b>"
            )
            await callback.message.edit_text(text)
            await callback.answer()
            return
    except:
        pass

    await callback.message.delete()
    await send_captcha(callback.message, lang)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("captcha:"))
async def captcha_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    clicked = callback.data.split(":")[1]
    correct = user_captcha.get(user_id)

    if clicked != correct:
        emojis = random.sample(EMOJI_POOL, CAPTCHA_BUTTONS)
        new_correct = random.choice(emojis)
        user_captcha[user_id] = new_correct

        text = (
            "🔒 <b>To get the chat invite link, please complete the captcha:</b>\n"
            f"Select {new_correct} on the keyboard"
            if lang == "en"
            else
            "🔒 <b>Для получения ссылки на чат, пройдите простую капчу:</b>\n"
            f"Выберите на клавиатуре {new_correct}"
        )

        await callback.message.edit_text(
            text,
            reply_markup=captcha_keyboard(emojis)
        )
        await callback.answer("❌ Wrong!" if lang == "en" else "❌ Неверно!", show_alert=True)
        return

    user_captcha.pop(user_id, None)
    await callback.message.delete()

    text = (
        "📄 <b>Please read the chat rules before joining:</b>"
        if lang == "en"
        else "📄 <b>Перед вступлением в чат, ознакомьтесь с правилами:</b>"
    )

    await callback.message.answer(
        text,
        reply_markup=rules_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "rules_ok")
async def rules_ok(callback: types.CallbackQuery):
    lang = user_lang.get(callback.from_user.id, "ru")

    invite = await bot.create_chat_invite_link(chat_id=CHAT_ID)
    user_invites[callback.from_user.id] = invite.invite_link

    text = (
        "🔓 <b>The chat invite link is active for 5 minutes:</b>\n"
        if lang == "en"
        else "🔓 <b>Ссылка для вступления в наш чат активна 5 минут:</b>\n"
    )

    msg = await callback.message.edit_text(
        text + invite.invite_link,
        disable_web_page_preview=True
    )

    async def delete_after():
        await asyncio.sleep(300)
        try:
            await msg.delete()
        except:
            pass

    asyncio.create_task(delete_after())
    await callback.answer()

@dp.chat_member()
async def on_user_join(event: ChatMemberUpdated):
    if event.chat.id != CHAT_ID:
        return

    if event.new_chat_member.status == "member":
        user_id = event.from_user.id
        invite_link = user_invites.get(user_id)

        if invite_link:
            try:
                await bot.revoke_chat_invite_link(
                    chat_id=CHAT_ID,
                    invite_link=invite_link
                )
            except:
                pass

            user_invites.pop(user_id, None)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
