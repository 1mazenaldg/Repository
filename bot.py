import telebot
from telebot import types
import requests

API_TOKEN = '7486498259:AAEg-Bzt359YA88fw88lxbi34xlsloHULFU'
SMM_API_KEY = '6a23bbadc69605a381e17e04678239dc'
CHANNEL_USERNAME = 'SMMTechnoTel'

bot = telebot.TeleBot(API_TOKEN)

free_services = {
    1308: {'name': 'اعجابات انستغرام ❤️🔥', 'min': 10, 'max': 50},
    1309: {'name': 'مشاهدات انستغرام جميع الروابط ❤️🔥', 'min': 100, 'max': 100},
    1561: {'name': 'مشاهدات فيديو فيسبوك | ريلز/فيديو', 'min': 500, 'max': 500},
    999:  {'name': 'مزيج من ردود الفعل الإيجابية ❤️', 'min': 10, 'max': 10},
    1560: {'name': 'مزيج من ردود الفعل السلبية 💩', 'min': 10, 'max': 10},
}

user_states = {}
user_selected_service = {}
user_links = {}


def check_subscription(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status != 'left'
    except Exception as e:
        print("Subscription check error:", e)
        return False


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    if not check_subscription(user_id):
        bot.send_message(message.chat.id,
                         f"مرحباً @{username}!\nيرجى الاشتراك في القناة أولاً:\nhttps://t.me/{CHANNEL_USERNAME}")
        return

    user_states[user_id] = 'waiting_for_service'

    markup = types.InlineKeyboardMarkup(row_width=2)
    service_emojis = {
        1308: "❤️👍",
        1309: "👀🔥",
        1561: "🎥📈",
        999:  "💬😊",
        1560: "💬😞"
    }

    for svc_id, svc_info in free_services.items():
        emoji = service_emojis.get(svc_id, "")
        btn_text = f"{emoji} {svc_info['name']}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"service_{svc_id}"))

    markup.add(
        types.InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/TechnoStor1"),
        types.InlineKeyboardButton("📘 تابعنا على فيسبوك", url="https://www.facebook.com/share/1DNBgn1eDS/")
    )
    markup.add(
        types.InlineKeyboardButton("🟢 تابعنا على واتساب", url="https://whatsapp.com/channel/0029Vayn6dpJENxtFfFoBO29")
    )

    welcome_text = (
        f"مرحباً @{username}!\n\n"
        "اختر الخدمة المجانية من القائمة أدناه:\n"
        "- اضغط على اسم الخدمة لاختيارها.\n"
        "- بعد ذلك سترسل الرابط المطلوب.\n"
        "- ثم أدخل الكمية المطلوبة.\n\n"
        "جميع الخدمات مجانية.\n\n"
        "للاستفسار أو وجود مشكلة، تواصل معنا عبر الدعم الفني."
    )

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def service_chosen(call):
    user_id = call.from_user.id
    svc_id = int(call.data.split('_')[1])

    if svc_id not in free_services:
        bot.answer_callback_query(call.id, "الخدمة غير متوفرة حالياً.")
        return

    user_selected_service[user_id] = svc_id
    user_states[user_id] = 'waiting_for_link'

    svc_info = free_services[svc_id]
    bot.send_message(call.message.chat.id,
                     f"لقد اخترت: {svc_info['name']}\n"
                     f"الحد الأدنى: {svc_info['min']}\n"
                     f"الحد الأقصى: {svc_info['max']}\n"
                     "الرجاء إرسال الرابط:")
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state == 'waiting_for_link':
        link = message.text.strip()
        if not (link.startswith("http://") or link.startswith("https://")):
            bot.send_message(message.chat.id, "الرابط غير صحيح، يجب أن يبدأ بـ http:// أو https://")
            return

        user_links[user_id] = link
        user_states[user_id] = 'waiting_for_quantity'

        svc_id = user_selected_service.get(user_id)
        svc_info = free_services.get(svc_id)

        bot.send_message(message.chat.id,
                         f"أرسل الكمية المطلوبة بين {svc_info['min']} و {svc_info['max']}")

    elif state == 'waiting_for_quantity':
        try:
            qty = int(message.text)
        except:
            bot.send_message(message.chat.id, "يرجى إدخال رقم صحيح.")
            return

        svc_id = user_selected_service.get(user_id)
        svc_info = free_services.get(svc_id)

        if qty < svc_info['min'] or qty > svc_info['max']:
            bot.send_message(message.chat.id,
                             f"الكمية غير صحيحة، يجب أن تكون بين {svc_info['min']} و {svc_info['max']}")
            return

        link = user_links.pop(user_id)

        order_url = "https://smmtechno.ly/api/v2"
        params = {
            'key': SMM_API_KEY,
            'action': 'add',
            'service': svc_id,
            'link': link,
            'quantity': qty
        }

        try:
            resp = requests.post(order_url, data=params)
            data = resp.json()
            if 'error' in data:
                bot.send_message(message.chat.id, f"حدث خطأ في الطلب: {data['error']}")
            else:
                bot.send_message(message.chat.id,
                                 f"تم الطلب بنجاح!\nرقم الطلب: {data.get('order')}\nالخدمة: {svc_info['name']}\nالكمية: {qty}")
        except Exception as e:
            bot.send_message(message.chat.id, f"فشل الاتصال بالسيرفر: {e}")

        user_states[user_id] = 'waiting_for_service'
        start(message)


bot.infinity_polling()
