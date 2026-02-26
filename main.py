import asyncio
import os
from dotenv import load_dotenv
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# =========================
# 🔐 TOKEN
# =========================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "vizitka.db"

# =========================
# 📦 DATABASE
# =========================
async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            name TEXT,
            surname TEXT,
            location TEXT,
            phone TEXT,
            instagram TEXT,
            profession TEXT
        )
        """)
        await db.commit()

# =========================
# 🔐 FSM
# =========================
class Vizitka(StatesGroup):
    name = State()
    surname = State()
    location = State()
    phone = State()
    instagram = State()
    profession = State()

class EditVizitka(StatesGroup):
    value = State()

# =========================
# 🎛 KEYBOARDS
# =========================
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Vizitka yaratish", callback_data="create")
    builder.button(text="📇 Vizitkani ko'rish", callback_data="my_card")
    builder.adjust(1)
    return builder.as_markup()

def card_actions_menu(instagram: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="📸 Instagram", url=f"https://instagram.com/{instagram}")
    builder.button(text="✏️ Tahrirlash", callback_data="edit_card")
    builder.button(text="📤 Ulashish", callback_data="share_card")
    builder.button(text="🏠 Bosh menyu", callback_data="back_menu")
    builder.adjust(1, 2, 1)
    return builder.as_markup()

def edit_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Ism",        callback_data="edit_name")
    builder.button(text="👤 Familya",    callback_data="edit_surname")
    builder.button(text="📍 Manzil",     callback_data="edit_location")
    builder.button(text="📱 Telefon",    callback_data="edit_phone")
    builder.button(text="📸 Instagram",  callback_data="edit_instagram")
    builder.button(text="💼 Kasb",       callback_data="edit_profession")
    builder.button(text="🔙 Orqaga",     callback_data="my_card")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

# =========================
# 🛠 HELPERS
# =========================
async def get_user_card(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT name, surname, location, phone, instagram, profession "
            "FROM users WHERE tg_id = ? ORDER BY id DESC LIMIT 1",
            (tg_id,)
        )
        return await cursor.fetchone()

def format_card(name, surname, location, phone, instagram, profession) -> str:
    return (
        "╔══════════════════════╗\n"
        "║   💎 SMART VIZITKA   ║\n"
        "╚══════════════════════╝\n\n"
        f"👤 <b>{name} {surname}</b>\n"
        f"💼 <i>{profession}</i>\n\n"
        "─────────────────────────\n"
        f"📍 <b>Manzil:</b> {location}\n"
        f"📞 <b>Tel:</b> {phone}\n"
        f"📸 <b>Instagram:</b> @{instagram}\n"
        "─────────────────────────"
    )

MAIN_TEXT = (
    "✨ <b>SMART VIZITKA BOT</b>\n\n"
    "🚀 Professional raqamli vizitka yarating!\n"
    "📇 Ma'lumotlaringizni bir marta kiriting va istalgan vaqt ulashing."
)

# =========================
# 🚀 START
# =========================
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(MAIN_TEXT, parse_mode="HTML", reply_markup=main_menu())

@dp.callback_query(F.data == "back_menu")
async def back_menu(call: CallbackQuery):
    await call.message.edit_text(MAIN_TEXT, parse_mode="HTML", reply_markup=main_menu())
    await call.answer()

# =========================
# 📝 CREATE
# =========================
@dp.callback_query(F.data == "create")
async def create(call: CallbackQuery, state: FSMContext):
    user = await get_user_card(call.from_user.id)
    if user:
        builder = InlineKeyboardBuilder()
        builder.button(text="✏️ Tahrirlash", callback_data="edit_card")
        builder.button(text="🔙 Orqaga",     callback_data="back_menu")
        builder.adjust(1)
        await call.message.edit_text(
            "⚠️ Sizda allaqachon vizitka mavjud!\nTahrirlashni xohlaysizmi?",
            reply_markup=builder.as_markup()
        )
        await call.answer()
        return

    await call.message.edit_text(
        "📝 <b>Yangi vizitka yaratamiz!</b>\n\n1️⃣ / 6️⃣ — 👤 Ismingizni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(Vizitka.name)
    await call.answer()

@dp.message(Vizitka.name)
async def get_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("❗ Ism kamida 2 ta harf bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("2️⃣ / 6️⃣ — 👤 Familyangizni kiriting:")
    await state.set_state(Vizitka.surname)

@dp.message(Vizitka.surname)
async def get_surname(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("❗ Familya kamida 2 ta harf bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(surname=message.text.strip())
    await message.answer("3️⃣ / 6️⃣ — 📍 Manzilingizni kiriting (shahar, mamlakat):")
    await state.set_state(Vizitka.location)

@dp.message(Vizitka.location)
async def get_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text.strip())
    await message.answer("4️⃣ / 6️⃣ — 📱 Telefon raqamingizni kiriting (+998xxxxxxxxx):")
    await state.set_state(Vizitka.phone)

@dp.message(Vizitka.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = phone.replace("+", "").replace(" ", "").replace("-", "")
    if not digits.isdigit() or len(digits) < 7:
        await message.answer("❗ Noto'g'ri telefon raqami. Qayta kiriting (masalan: +998901234567):")
        return
    await state.update_data(phone=phone)
    await message.answer("5️⃣ / 6️⃣ — 📸 Instagram username kiriting (@siz):")
    await state.set_state(Vizitka.instagram)

@dp.message(Vizitka.instagram)
async def get_instagram(message: Message, state: FSMContext):
    await state.update_data(instagram=message.text.strip().lstrip("@"))
    await message.answer("6️⃣ / 6️⃣ — 💼 Kasbingizni kiriting:")
    await state.set_state(Vizitka.profession)

@dp.message(Vizitka.profession)
async def finish(message: Message, state: FSMContext):
    await state.update_data(profession=message.text.strip())
    data = await state.get_data()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO users (tg_id, name, surname, location, phone, instagram, profession) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (message.from_user.id, data["name"], data["surname"], data["location"],
             data["phone"], data["instagram"], data["profession"])
        )
        await db.commit()

    await state.clear()
    await message.answer("🎉 <b>Vizitka muvaffaqiyatli saqlandi!</b>",
                         parse_mode="HTML", reply_markup=main_menu())

# =========================
# 📇 VIEW CARD
# =========================
@dp.callback_query(F.data == "my_card")
async def my_card(call: CallbackQuery):
    user = await get_user_card(call.from_user.id)

    if not user:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Vizitka yaratish", callback_data="create")
        builder.button(text="🔙 Orqaga",           callback_data="back_menu")
        builder.adjust(1)
        await call.message.edit_text(
            "❗ Sizda hali vizitka yo'q.\nYangi vizitka yarating!",
            reply_markup=builder.as_markup()
        )
        await call.answer()
        return

    name, surname, location, phone, instagram, profession = user
    text = format_card(name, surname, location, phone, instagram, profession)
    await call.message.edit_text(text, parse_mode="HTML",
                                  reply_markup=card_actions_menu(instagram))
    await call.answer()

# =========================
# 📤 SHARE CARD
# =========================
@dp.callback_query(F.data == "share_card")
async def share_card(call: CallbackQuery):
    user = await get_user_card(call.from_user.id)
    if not user:
        await call.answer("❗ Avval vizitka yarating!", show_alert=True)
        return

    name, surname, location, phone, instagram, profession = user
    share_text = (
        f"💎 SMART VIZITKA\n\n"
        f"👤 {name} {surname}\n"
        f"💼 {profession}\n"
        f"📍 {location}\n"
        f"📞 {phone}\n"
        f"📸 instagram.com/{instagram}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="my_card")

    await call.message.edit_text(
        "📤 <b>Vizitkangizni ulashing:</b>\n\n"
        "Quyidagi matnni nusxalab do'stlaringizga yuboring 👇\n\n"
        f"<code>{share_text}</code>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await call.answer()

# =========================
# ✏️ EDIT CARD
# =========================
@dp.callback_query(F.data == "edit_card")
async def edit_card(call: CallbackQuery):
    user = await get_user_card(call.from_user.id)
    if not user:
        await call.answer("❗ Avval vizitka yarating!", show_alert=True)
        return

    await call.message.edit_text(
        "✏️ <b>Qaysi ma'lumotni tahrirlaysiz?</b>",
        parse_mode="HTML",
        reply_markup=edit_menu()
    )
    await call.answer()

EDIT_FIELDS = {
    "edit_name":       ("name",       "👤 Yangi ismingizni kiriting:"),
    "edit_surname":    ("surname",    "👤 Yangi familyangizni kiriting:"),
    "edit_location":   ("location",   "📍 Yangi manzilingizni kiriting:"),
    "edit_phone":      ("phone",      "📱 Yangi telefon raqamingizni kiriting:"),
    "edit_instagram":  ("instagram",  "📸 Yangi Instagram username kiriting:"),
    "edit_profession": ("profession", "💼 Yangi kasbingizni kiriting:"),
}

@dp.callback_query(F.data.in_(EDIT_FIELDS.keys()))
async def edit_field_start(call: CallbackQuery, state: FSMContext):
    field, prompt = EDIT_FIELDS[call.data]
    await state.update_data(edit_field=field)
    await state.set_state(EditVizitka.value)
    await call.message.edit_text(f"✏️ {prompt}", parse_mode="HTML")
    await call.answer()

@dp.message(EditVizitka.value)
async def edit_field_save(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["edit_field"]
    value = message.text.strip()

    if field == "instagram":
        value = value.lstrip("@")

    if field == "phone":
        digits = value.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 7:
            await message.answer("❗ Noto'g'ri telefon raqami. Qayta kiriting:")
            return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f"UPDATE users SET {field} = ? WHERE tg_id = ? AND id = (SELECT MAX(id) FROM users WHERE tg_id = ?)",
            (value, message.from_user.id, message.from_user.id)
        )
        await db.commit()

    await state.clear()
    await message.answer(
        "✅ <b>Ma'lumot muvaffaqiyatli yangilandi!</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# =========================
# ▶️ RUN
# =========================
async def main():
    await create_table()
    print("🚀 Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())