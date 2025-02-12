import modules.manager as manager
import json, re, requests


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters, Updater, CallbackContext, ChatJoinRequestHandler
from telegram.error import BadRequest, Conflict

from modules.utils import process_command, is_admin, cancel, error_callback,check_link

UPSELL_ESCOLHA, UPSELL_RECEBER, UPSELL_LINK = range(3)
# comando /upsell
async def upsell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_check = await process_command(update, context)
    if not command_check:
        return ConversationHandler.END
    if not await is_admin(context, update.message.from_user.id):
        
        return ConversationHandler.END
    context.user_data['conv_state'] = "upsell"

    keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR", callback_data="adicionar"), InlineKeyboardButton("➖ REMOVER", callback_data="remover")],
            [InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)



    await update.message.reply_text("💵 Qual ação deseja fazer com o upsell:", reply_markup=reply_markup)
    return UPSELL_ESCOLHA

async def upsell_escolha(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancelar':
        await cancel(update, context)
        return ConversationHandler.END

    elif query.data == 'adicionar':
        keyboard = [[InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("💵 Envie como deseja a mensagem do upsell\:\n> Pode conter midia", reply_markup=reply_markup, parse_mode='MarkdownV2')
        return UPSELL_RECEBER
    elif query.data == 'remover':
        manager.update_bot_upsell(context.bot_data['id'], {}) 
        await query.message.edit_text("✅ Upsell deletado com sucesso")
        context.user_data['conv_state'] = False
        return ConversationHandler.END

async def upsell_receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print(update.message)
        save = {
            'media':False,
            'text':False,
            'link':False
            }
        if update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            save['media'] = {
                'file':photo_file.file_id,
                'type':'photo'
            }

        elif update.message.video:
            video_file = await update.message.video.get_file()
            save['media'] = {
                'file':video_file.file_id,
                'type':'video'
            }
        elif update.message.text:
            save['text'] = update.message.text
        else: 
            await update.message.reply_text("⛔ Somente texto ou midia:")
            return UPSELL_RECEBER
                

        if update.message.caption:
            save['text'] = update.message.caption

        context.user_data['upsell_context'] = save
        keyboard = [[InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("💵 Envie um link para a mensagem de upsell\:\n> Deve conter http:// ou https:// no inicio", reply_markup=reply_markup, parse_mode='MarkdownV2')
        return UPSELL_LINK
    except Exception as e:
        await update.message.reply_text(text=f"⛔ Erro ao salvar upsell {str(e)}", parse_mode='MarkdownV2')
        context.user_data['conv_state'] = False
        return ConversationHandler.END
async def upsell_recebe_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    keyboard = [[InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    id_grupo = ''
    if not update.message.text:
        await update.message.reply_text("❌ Somente textos são permitidos:", reply_markup=reply_markup)
        return UPSELL_LINK
    link_recebido = update.message.text.strip()
    if not check_link(link_recebido):
        await update.message.reply_text("❌ Insira um link valido:", reply_markup=reply_markup)
        return UPSELL_LINK
    upsell_salvo = context.user_data['upsell_context'] 
    upsell_salvo['link'] = link_recebido
    manager.update_bot_upsell(context.bot_data['id'], upsell_salvo) 
    await update.message.reply_text("✅ Upsell adicionado com sucesso")
    context.user_data['conv_state'] = False
    return ConversationHandler.END

conv_handler_upsell = ConversationHandler(
    entry_points=[CommandHandler("upsell", upsell)],
    states={
        UPSELL_ESCOLHA: [CallbackQueryHandler(upsell_escolha)],
        UPSELL_RECEBER:[MessageHandler(~filters.COMMAND, upsell_receber_mensagem), CallbackQueryHandler(cancel)],
        UPSELL_LINK:[MessageHandler(~filters.COMMAND, upsell_recebe_link), CallbackQueryHandler(cancel)]
    },
    fallbacks=[CallbackQueryHandler(error_callback)]
    )

#UPSELL 
#{
#"text":"",
#"media"{"type", "file"},
#"link"
#}