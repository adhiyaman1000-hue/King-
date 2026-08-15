import re
import time
import sqlite3
import telebot

# உன்னுடைய பாட் டோக்கன் இணைக்கப்பட்டுள்ளது
BOT_TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
bot = telebot.TeleBot(BOT_TOKEN)

warnings_tracker = {}
user_infraction_memory = {}

# ஃபில்டர் டேட்டாபேஸ் பெயர்
DATABASE_NAME = "advanced_filters_bot2.db"

EXTENSIVE_BLACKLIST_WORDS = [
    'sex', 'xxx', 'porn', 'nude', 'sexual', 'fuck', 'bitch', 'asshole', 
    'bastard', 'slut', 'whore', 'dick', 'pussy', 'cock', 'boobs',
    'cunt', 'jerk', 'bastards', 'fucker', 'fucking', 'suck', 'strip',
    'chudutha', 'oththu', 'punda', 'olen', 'da', 'loosu'
]

DM_PROMOTION_KEYWORDS = [
    'dm me', 'inbox me', 'pm me', 'message me', 'text me', 
    'inbox', 'dm', 'private chat', 'msg me', 'ping me', 'contact in dm',
    'contact me', 'whatsapp me', 'telegram dm', 'personal chat'
]

def deep_security_inspection_scanner(message):
    text = message.text or message.caption or ""
    
    if message.sticker:
        return True, "Stickers", "Sent unauthorized stickers, animated graphics, or GIFs."
    if message.document:
        return True, "Documents", "Shared unauthorized documents, raw files, or application packages."
    if message.contact:
        return True, "Contacts", "Shared unauthorized personal contact details or phone numbers."
    if message.location:
        return True, "Location", "Shared private geographic location or GPS tracking coordinates."
    if message.forward_from or message.forward_from_chat:
        return True, "Forwards", "Forwarded unauthorized messages or media from external chats."
    if text.startswith('/'):
        return True, "Commands", "Attempted to execute restricted bot commands inside the group chat."
    if re.search(r'#\w+', text):
        return True, "Hashtags", "Used unauthorized hashtags or promotional tags."

    if text:
        text_lower = text.lower()
        
        url_pattern = r'https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|bit\.ly/\S+|goo\.gl/\S+'
        matched_urls = re.findall(url_pattern, text)
        if matched_urls:
            target_link = matched_urls[0]
            return True, "Links", f"Shared prohibited external web link or invitation link: ({target_link})"
        
        for keyword in DM_PROMOTION_KEYWORDS:
            if keyword in text_lower:
                return True, "DM", f"Attempted private chat promotion using restricted phrase: ('{keyword}')"
        
        for bad_word in EXTENSIVE_BLACKLIST_WORDS:
            if bad_word in text_lower:
                return True, "Profanity", f"Used restricted, offensive, or blacklisted vocabulary word: ('{bad_word}')"
            
    return False, "", ""

def text_cleaner(input_text):
    if not input_text:
        return ""
    input_text = input_text.lower().strip()
    input_text = re.sub(r'[^\w\s]', " ", input_text)
    return " ".join(input_text.split())

@bot.message_handler(content_types=['text', 'sticker', 'document', 'video', 'audio', 'photo', 'contact', 'location'])
def supreme_security_and_advanced_filter_gateway(message):
    try:
        sender_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
        if sender_status not in ['administrator', 'creator']:
            is_violation, violation_category, detailed_reason = deep_security_inspection_scanner(message)
            
            if is_violation:
                user_id = message.from_user.id
                user_name = message.from_user.first_name
                
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception as deletion_error:
                    print(f"Deletion Error: {deletion_error}")
                
                user_infraction_memory[user_id] = detailed_reason
                
                action_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                encoded_reason_string = detailed_reason.replace(" ", "_")
                
                btn_warn = telebot.types.InlineKeyboardButton("⚠️ Send Warning", callback_data=f"warn_{user_id}_{violation_category}_{encoded_reason_string}")
                btn_mute = telebot.types.InlineKeyboardButton("🔇 Mute 1 Day", callback_data=f"mute_{user_id}")
                btn_ban = telebot.types.InlineKeyboardButton("🚫 Permanent Ban", callback_data=f"ban_{user_id}")
                btn_ignore = telebot.types.InlineKeyboardButton("✅ No Action", callback_data="ign")
                
                action_markup.add(btn_warn, btn_mute, btn_ban, btn_ignore)
                
                bot.send_message(
                    message.chat.id, 
                    f"🚨 **SECURITY ALERT: RULE VIOLATION DETECTED!**\n\n"
                    f"👤 **Offender:** {user_name} (`{user_id}`)\n"
                    f"❌ **Reason:** {detailed_reason}\n\n"
                    f"⚡ *Message removed. Administrator, select action below:*",
                    reply_markup=action_markup, 
                    parse_mode="Markdown"
                )
                return  
    except Exception as security_error:
        print(f"Security Error: {security_error}")

    # ==========================================
    # உன்னுடைய அட்வான்ஸ் ஃபில்டர் பகுதி (Filter Logic)
    # ==========================================
    incoming_query = message.text or message.caption or ""
    if incoming_query and not incoming_query.startswith('/'):
        user_cleaned_text = text_cleaner(incoming_query)
        try:
            connection = sqlite3.connect(DATABASE_NAME)
            cursor = connection.cursor()
            cursor.execute("SELECT keyword, response FROM filters")
            all_saved_filters = cursor.fetchall()
            connection.close()

            for keyword, response_text in all_saved_filters:
                if keyword in user_cleaned_text:
                    bot.reply_to(message, response_text)
                    break
        except Exception as filter_error:
            print(f"Filter Execution Error: {filter_error}")

@bot.callback_query_handler(func=lambda call: True)
def comprehensive_admin_callback_handler(call):
    try:
        admin_check = bot.get_chat_member(call.message.chat.id, call.from_user.id)
        if admin_check.status not in ['administrator', 'creator']:
            bot.answer_callback_query(call.id, "❌ Access Denied: Admins only!", show_alert=True)
            return

        callback_data_parts = call.data.split('_')
        action_command = callback_data_parts[0]

        if action_command == "warn":
            target_user_id = int(callback_data_parts[1])
            violation_category_type = callback_data_parts[2]
            
            if len(callback_data_parts) > 3:
                full_violation_desc = " ".join(callback_data_parts[3:]).replace("_", " ")
            elif target_user_id in user_infraction_memory:
                full_violation_desc = user_infraction_memory[target_user_id]
            else:
                full_violation_desc = "Committed a violation of rules."
            
            if target_user_id not in warnings_tracker:
                warnings_tracker[target_user_id] = 0
            warnings_tracker[target_user_id] += 1
            current_warning_tally = warnings_tracker[target_user_id]
            
            bot.edit_message_text(
                f"⚠️ **OFFICIAL COMMUNITY WARNING**\n\n"
                f"👤 **User ID:** `{target_user_id}`\n"
                f"🔍 **Infraction:** {full_violation_desc}\n\n"
                f"📜 **Notice:** Warning issued. Next time you will be banned. (Total Warnings: {current_warning_tally})",
                call.message.chat.id, 
                call.message.message_id, 
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "Warning sent successfully.")

        elif action_command == "mute":
            target_user_id = int(callback_data_parts[1])
            muted_until_timestamp = int(time.time()) + 86400
            
            bot.restrict_chat_member(call.message.chat.id, target_user_id, until_date=muted_until_timestamp, can_send_messages=False)
            bot.edit_message_text(
                f"🔇 **USER MUTED**\n\n👤 **User ID:** `{target_user_id}`\n⏳ **Status:** Muted for 24 hours.", 
                call.message.chat.id, 
                call.message.message_id, 
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "User muted successfully.")

        elif action_command == "ban":
            target_user_id = int(callback_data_parts[1])
            
            bot.ban_chat_member(call.message.chat.id, target_user_id)
            bot.edit_message_text(
                f"🚫 **USER BANNED**\n\n👤 **User ID:** `{target_user_id}`\n⚡ **Status:** Banned from group.", 
                call.message.chat.id, 
                call.message.message_id, 
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "User banned successfully.")

        elif action_command == "ign":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Action dismissed.")
            
    except Exception as callback_exec_error:
        print(f"Callback Error: {callback_exec_error}")

if __name__ == "__main__":
    print("Bot is running securely with filters...")
    bot.infinity_polling(skip_pending=True)
