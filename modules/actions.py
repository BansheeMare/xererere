
import modules.manager as manager
import modules.payment as payment
import modules.utils as utils
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters, Updater, CallbackContext, ChatJoinRequestHandler
from telegram.error import BadRequest, Conflict
import asyncio, json

from modules.utils import escape_markdown_v2
# Enviar disparo       -
# Enviar recuperação   -
# Enviar upsell        - FEITO - NÃO TESTADO
# Enviar expiração     - FEITO - NÃO TESTADO
# Enviar pagamento pix - 
# Enviar grupo         - FEITO - NÃO TESTADO



async def send_disparo(context, user_id, config):
    
    try:
        print(user_id)
        keyboard = []
        if config['tipo'] == "plano":
            payment_id = manager.create_payment(user_id, config['plano'], config['plano'], context.bot_data['id'])
            valor = config['plano']['value']
            keyboard = [
                [InlineKeyboardButton('Confirmar Oferta', callback_data=f'exibir_{payment_id}')]
            ]
        elif config['tipo'] == "livre":
            keyboard = [[InlineKeyboardButton('ACEITAR OFERTA', url=config['link'])]]
            
        reply_markup=InlineKeyboardMarkup(keyboard)
        
        if config['mensagem'].get('media', False):
            if config['mensagem'].get('text', False):
                print(config['mensagem'].get('media', False))
                if config['mensagem']['media'].get('type', False) == 'photo':
                    await context.bot.send_photo(chat_id=user_id, photo=config['mensagem']['media']['file'], caption=config['mensagem'].get('text', False), reply_markup=reply_markup)
                else:
                    await context.bot.send_video(chat_id=user_id, video=config['mensagem']['media']['file'], caption=config['mensagem'].get('text', False), reply_markup=reply_markup)
            else:
                print('sem texto')
                if config['mensagem']['media'].get('type') == 'photo':
                    await context.bot.send_photo(chat_id=user_id, photo=config['mensagem']['media']['file'], reply_markup=reply_markup)
                else:
                    await context.bot.send_video(chat_id=user_id, video=config['mensagem']['media']['file'], reply_markup=reply_markup)
        else:
            print('texto')
            await context.bot.send_message(chat_id=user_id, text=config['mensagem']['text'], reply_markup=reply_markup)
    except Exception as e:
        print(e)

        return False
    return True

def send_payment():
    pass
#{"media": {"file": "AgACAgEAAxkBAAIDbWehTomUmGO9g5rzT8InVQwfQnQAA2mvMRtsPghFk70HYXbW_0wBAAMCAAN5AAM2BA", "type": "photo"}, "text": "Xibiu", "link": false, "value": 9.99}
async def recovery_thread(context, user_id, config, id):
    await asyncio.sleep(config['tempo']*60)
    print(config)
    payment_data = manager.get_payment_by_id(id)
    state = payment_data[5]
    plano = json.loads(payment_data[3])
    plano['recovery'] = False
    valor = config.get('value', plano['value'])
    plano['value'] = valor
    payment_id = manager.create_payment(user_id, plano, plano['name'], context.bot_data['id'])
    
    keyboard = [
        [InlineKeyboardButton('Confirmar Oferta', callback_data=f'exibir_{payment_id}')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if state != 'awaiting':
        if config.get('media', False):
            if config.get('text', False):
                if config['media'].get('type') == 'photo':
                    await context.bot.send_photo(chat_id=user_id, photo=config['media']['file'], caption=config['text'], reply_markup=markup)
                else:
                    await context.bot.send_video(chat_id=user_id, video=config['media']['file'], caption=config['text'], reply_markup=markup)
            else:
                if config['media'].get('type') == 'photo':
                    await context.bot.send_photo(chat_id=user_id, photo=config['media']['file'], reply_markup=markup)
                else:
                    await context.bot.send_video(chat_id=user_id, video=config['media']['file'], reply_markup=markup)
        else:
            await context.bot.send_message(chat_id=user_id, text=config['text'], reply_markup=markup)


async def send_upsell(context, user_id):
    config = manager.get_bot_upsell(context.bot_data['id'])
    if not config.get('text', False) or not config.get('media', False):
        return
    

    keyboard = [[InlineKeyboardButton('Ver Oferta', url=config['link'])]]
    reply = InlineKeyboardMarkup(keyboard)
    if config.get('media', False):
        if config.get('text', False):
            if config['media'].get('type') == 'photo':
                await context.bot.send_photo(chat_id=user_id, photo=config['media']['file'], caption=config['text'], reply_markup=reply)
            else:
                await context.bot.send_video(chat_id=user_id, video=config['media']['file'], caption=config['text'], reply_markup=reply)
        else:
            if config['media'].get('type') == 'photo':
                await context.bot.send_photo(chat_id=user_id, photo=config['media']['file'], reply_markup=reply)
            else:
                await context.bot.send_video(chat_id=user_id, video=config['media']['file'], reply_markup=reply)
    else:
        await context.bot.send_message(chat_id=user_id, text=config['text'], reply_markup=reply)

async def send_expiration(context, user_id):
    config = manager.get_bot_expiration(context.bot_data['id'])
    if not config.get('text', False) or not config.get('media', False):
        return
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='RENOVAR ASSINATURA', callback_data='acessar_ofertas')]])
    if config.get('media', False):
        if config.get('text', False):
            if config['media'].get('type') == 'photo':
                await context.bot.send_photo(chat_id=user_id, photo=config['media']['file'], caption=config['text'], reply_markup=reply_markup)
            else:
                await context.bot.send_video(chat_id=user_id, video=config['media']['file'], caption=config['text'], reply_markup=reply_markup)
        else:
            if config['media'].get('type') == 'photo':
                await context.bot.send_photo(chat_id=user_id, photo=config['media']['file'], reply_markup=reply_markup)
            else:
                await context.bot.send_video(chat_id=user_id, video=config['media']['file'], reply_markup=reply_markup)
    else:

        
        await context.bot.send_message(chat_id=user_id, text=config['text'], reply_markup=reply_markup)


async def send_invite(context, user_id):
    try:
        # Carrega as informações do grupo
        grupo_info = manager.get_bot_group(bot_id=context.bot_data['id'])
        user = await context.bot.get_chat(user_id)
        # Cria o link de convite com solicitação de entrada ativada
        
        
        group_invite_link = await context.bot.create_chat_invite_link(
            chat_id=grupo_info, 
            creates_join_request=True
        )
        nickname = user.username
        keyboard = [
            [InlineKeyboardButton("ENTRAR NO GRUPO", url=group_invite_link.invite_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Pagamento aprovado! Clique no botão abaixo para entrar no grupo.",
            reply_markup=reply_markup
        )
        print(f"[INFO] Link de convite criado com sucesso: {group_invite_link.invite_link}")
    except ValueError as ve:
        print(f"[ERRO] Erro no ID do grupo: {ve}")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Não foi possível identificar o grupo. Por favor, entre em contato com o suporte."
        )
    except Exception as e:
        print(f"[ERRO] Erro ao criar link de grupo: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Ocorreu um erro ao gerar o link de convite. Por favor, tente novamente mais tarde."
        )

async def acessar_planos(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    planos = manager.get_bot_plans(context.bot_data['id'])
    keyboard_plans = []
    for plan_index in range(len(planos)):
        keyboard_plans.append([InlineKeyboardButton(f'{planos[plan_index]['name']} - R$ {planos[plan_index]['value']}', callback_data=f"plano_{plan_index}")])
    reply_markup = InlineKeyboardMarkup(keyboard_plans)
    await query.message.edit_text('Escolha um plano:', reply_markup=reply_markup)


async def confirmar_plano(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    plano_index = query.data.split('_')[-1]
    planos = manager.get_bot_plans(context.bot_data['id'])
    
    if len(planos) > int(plano_index):
        plano = planos[int(plano_index)]

        payment_id = manager.create_payment(str(query.from_user.id), plano, plano['name'], context.bot_data['id'])
        keyboard = [
            [InlineKeyboardButton('Confirmar Oferta', callback_data=f'pagar_{payment_id}')]
        ]
        names = {
            'dia':'dias',
            'semana':'semanas',
            'mes':'meses',
            'ano':'anos',
            'eterno':''
        }
    
        reply_markup = InlineKeyboardMarkup(keyboard)
        valor = plano['value']
    
        if plano['time'] == 1:
            names = {
            'dia':'dia',
            'semana':'semana',
            'mes':'mes',
            'ano':'ano',
            'eterno':''
        }
    
        if plano['time_type'] != 'eterno':
            await query.message.reply_text(f"💎 Confirme o plano\:\n\nNome\: {escape_markdown_v2(plano['name'])}\nTempo\: {plano['time']} {names[plano['time_type']]}\nValor\: R\$ {escape_markdown_v2(str(valor))}", reply_markup=reply_markup, parse_mode='MarkdownV2')
        else:
            await query.message.reply_text(f"💎 Confirme o plano\:\n\nNome\: {escape_markdown_v2(plano['name'])}\nTempo\: Vitalicio\nValor\: R\$ {escape_markdown_v2(str(valor))}", reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        await query.message.reply_text(f'⛔ Erro ao encontrar oferta')

async def exibir_plano(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    payment_index = query.data.split('_')[-1]
    plano = json.loads(manager.get_payment_plan_by_id(payment_index))

    keyboard = [
        [InlineKeyboardButton('Confirmar Oferta', callback_data=f'pagar_{payment_index}')]
    ]
    names = {
        'dia':'dias',
        'semana':'semanas',
        'mes':'meses',
        'ano':'anos',
        'eterno':''
    }
    reply_markup = InlineKeyboardMarkup(keyboard)
    valor = plano['value']
    if plano['time'] == 1:
            names = {
            'dia':'dia',
            'semana':'semana',
            'mes':'mes',
            'ano':'ano',
            'eterno':''
        }
    if plano['time_type'] != 'eterno':
        await query.message.reply_text(f"💎 Confirme o plano\:\n\nNome\: {escape_markdown_v2(plano['name'])}\nTempo\: {plano['time']} {names[plano['time_type']]}\nValor\: R\$ {escape_markdown_v2(str(valor))}", reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        await query.message.reply_text(f"💎 Confirme o plano\:\n\nNome\: {escape_markdown_v2(plano['name'])}\nTempo\: Vitalicio\nValor\: R\$ {escape_markdown_v2(str(valor))}", reply_markup=reply_markup, parse_mode='MarkdownV2')


async def notificar_admin(chat_id, plano_escolhido, bot_application, admin):
    bot_instance = bot_application.bot
    try:
        user = await bot_instance.get_chat(int(chat_id))
        username = user.username or "Não definido"
        first_name = user.first_name or "Não definido"
        #{"name": "XERERECA OTARIA", "value": 12.0, "time_type": "mes", "time": 12}
        mensagem_venda = (
            f"✅ Venda realizada!\n\n"
            f"🆔 Clientid: {chat_id}\n"
            f"👤 User: @{username}\n"
            f"📝 Nome: {first_name}\n"
            f"💵 Valor: R$ {str(plano_escolhido['value']).replace('.', ',')}\n"
            f"🔗 Plano: {plano_escolhido['name']}"
        )
        await bot_instance.send_message(chat_id=int(admin), text=mensagem_venda)
    except Exception as e:
        print(f'[ERROR] Erro ao notificar admin? {e}')


#{"name": "Alexo", "value": 18.9, "time_type": "eterno", "time": "eterno"}



