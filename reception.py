import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

TOKEN = "8353468552:AAFJzYntcGkSNsuk7XdJPRyi1zNPIgMRdBI"
ALLOWED_CHAT_ID = -1002572579294

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


async def safe_delete(chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass


async def is_admin(user_id: int, chat_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False


async def handle_admin_command(message: types.Message, text: str):
    if message.chat.id != ALLOWED_CHAT_ID:
        return

    if not await is_admin(message.from_user.id, message.chat.id):
        try:
            warn = await message.reply("❌")
        except:
            return

        asyncio.create_task(safe_delete(message.chat.id, message.message_id))

        async def del_warn():
            await asyncio.sleep(10)
            await safe_delete(warn.chat.id, warn.message_id)

        asyncio.create_task(del_warn())
        return

    if not message.reply_to_message:
        try:
            notice = await message.reply("Команда должна использоваться в ответ на сообщение.")
        except:
            return

        async def delayed_cleanup():
            await asyncio.sleep(10)
            await safe_delete(message.chat.id, message.message_id)
            await safe_delete(notice.chat.id, notice.message_id)

        asyncio.create_task(delayed_cleanup())
        return

    user = message.reply_to_message.from_user

    if user.username:
        user_link = f"<a href='https://t.me/{user.username}'>{user.full_name}</a>"
    else:
        user_link = user.full_name

    msg_text = text.format(user_link=user_link)

    await safe_delete(message.chat.id, message.reply_to_message.message_id)

    try:
        sent = await bot.send_message(
            chat_id=message.chat.id,
            text=msg_text,
            disable_web_page_preview=True
        )
    except:
        return

    await safe_delete(message.chat.id, message.message_id)

    async def delayed_remove_warning():
        await asyncio.sleep(300)
        await safe_delete(sent.chat.id, sent.message_id)

    asyncio.create_task(delayed_remove_warning())


@dp.message(Command("esc"))
async def esc_handler(message: types.Message):
    text = (
        "<b>{user_link}</b>\n"
        "<b>Внимание! В Вашем посте не обнаружилось упоминания Нашего</b> "
        "<b><a href='http://t.me/MikeTysonGarant'>гарант-сервиса!</a></b> "
        "<b>Добавьте в Ваш пост упоминание Нашего гаранта! – </b> <code>@MikeTysonGarant</code>"
    )
    await handle_admin_command(message, text)


@dp.message(Command("ad"))
async def ad_handler(message: types.Message):
    text = (
        "<b>{user_link}</b>\n"
        "<b>Внимание! Ваша реклама не согласована.</b>\n"
        "<b>Напишите нашему <a href='https://t.me/MikeTysonSupport'>саппорту</a>, "
        "для согласования рекламы – t.me/MikeTysonSupport</b>"
    )
    await handle_admin_command(message, text)


@dp.message(Command("escen"))
async def escen_handler(message: types.Message):
    text = (
        "<b>{user_link}</b>\n"
        "<b>Attention! Your post does not contain a mention of our</b> "
        "<b><a href='http://t.me/MikeTysonGarant'>guarantor service!</a></b>\n"
        "<b>Please add a mention of our guarantor – </b> <code>@MikeTysonGarant</code>"
    )
    await handle_admin_command(message, text)


@dp.message(Command("aden"))
async def aden_handler(message: types.Message):
    text = (
        "<b>{user_link}</b>\n"
        "<b>Attention! Your advertisement is not approved.</b>\n"
        "<b>Please contact our <a href='https://t.me/MikeTysonSupport'>support</a> "
        "to approve the advertisement – t.me/MikeTysonSupport</b>"
    )
    await handle_admin_command(message, text)


@dp.message()
async def filter_messages(message: types.Message):
    try:
        if message.entities:
            for ent in message.entities:
                if ent.type == "bot_command":
                    cmd = message.text[ent.offset: ent.offset + ent.length]
                    if cmd.startswith(("/esc", "/ad", "/escen", "/aden")):
                        return
    except:
        pass

    if message.chat.id != ALLOWED_CHAT_ID:
        if message.chat.type == "private":
            return

        if message.new_chat_members:
            try:
                me = await bot.me()
            except:
                return

            for member in message.new_chat_members:
                if member.id == me.id:
                    try:
                        warn = await message.answer("❌")
                    except:
                        return

                    asyncio.create_task(safe_delete(warn.chat.id, warn.message_id))
                    try:
                        await bot.leave_chat(message.chat.id)
                    except:
                        pass
                    return
        return


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
