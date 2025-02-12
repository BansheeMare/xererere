
import modules.manager as manager

import json, re, requests, asyncio

from modules.actions import recovery_thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters, Updater, CallbackContext, ChatJoinRequestHandler
from telegram.error import BadRequest, Conflict



    

# Função de execução do bot
from modules.utils import cancel, escape_markdown_v2
from modules.actions import send_disparo, send_upsell, send_expiration, send_invite, send_payment, acessar_planos, confirmar_plano, notificar_admin
from comandos.grupo import conv_handler_grupo
from comandos.planos import conv_handler_planos
from comandos.upsell import conv_handler_upsell
from comandos.expiracao import conv_handler_adeus
from comandos.recuperacao import conv_handler_recuperacao
from comandos.inicio import conv_handler_inicio
from comandos.admins import conv_handler_admin
from comandos.gateway import conv_handler_gateway
from comandos.disparo import conv_handler_disparo
from comandos.start import start
from datetime import datetime, timedelta
def add_days(date_str, type, amount, date_format="%Y-%m-%d"):
    name = {
            'dia':1,
            'semana':7,
            'mes':30,
            'ano':365
        }
    if type == 'eterno':
        return '2077-01-01'
    if not type in name.keys():
        return False
    days = name[type]*amount
    date_obj = datetime.strptime(date_str, date_format)
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime(date_format)
from datetime import datetime, timedelta

def calcular_datas(dias: int):
    agora = datetime.now()  # Obtém a data e hora atual
    futura = agora + timedelta(days=dias)  # Soma os dias à data atual

    return agora.strftime("%Y-%m-%d %H:%M:%S"), futura.strftime("%Y-%m-%d %H:%M:%S")

async def check_join_request(update: Update, context: CallbackContext):
    join_request = update.chat_join_request  # Detalhes da solicitação de entrada
    user = join_request.from_user
    group = manager.get_bot_group(bot_application.bot_data['id'])
    auth = manager.get_user_expiration(str(user.id), group)
    if auth:
        await join_request.approve()
        print(f'user aprovado {user.username}')
        await send_upsell(context, str(user.id))
        
async def expiration_task():
    print('expiration')
    while True:
        try:
            grupo_id = manager.get_bot_group(bot_application.bot_data['id'])
            expirados = manager.verificar_expirados(grupo_id)
        
            for user_id in expirados:
                try:
                    print(f'expirado {user_id}')
                    manager.remover_usuario(user_id, grupo_id)
                    await send_expiration(bot_application, user_id)
                    await bot_application.bot.ban_chat_member(chat_id=grupo_id, user_id=user_id)
                    await bot_application.bot.unban_chat_member(chat_id=grupo_id, user_id=user_id)
                    
                    
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
            #print(f'erro exp {bot_application.bot_data['id']}')
        await asyncio.sleep(5)

async def payment_task():
    print("PAYMENT TASK > Iniciando")
    name = {
            'dia':1,
            'semana':7,
            'mes':30,
            'ano':365
        }
    while True:
        await asyncio.sleep(2)
        try:
            payments = manager.get_payments_by_status('paid', bot_application.bot_data['id'])
            
            if len(payments) > 0:
                
                for payment in payments:
                    manager.update_payment_status(payment[1], 'finished')
                    
                    
                    if True:
                        group = manager.get_bot_group(bot_application.bot_data['id'])
                        user = payment[2]
                        plan = json.loads(payment[3])
                        days = 3650
                        if not plan['time_type'] == 'eterno':
                            days = name[plan['time_type']]*int(plan['time'])
                        today, expiration = calcular_datas(days)
                        #{"name": "XERERECA OTARIA", "value": 12.0, "time_type": "mes", "time": 12}
                        #expiration = add_days(str(today),plan['time_type'], plan['time'])

                        manager.add_user_to_expiration(user, today, expiration, plan, group)
                        await send_invite(bot_application, user)
                        
                        admin_list = manager.get_bot_admin(bot_application.bot_data['id'])
                        owner = manager.get_bot_owner(bot_application.bot_data['id'])
                        admin_list.append(owner)
                        for admin in admin_list:
                            await notificar_admin(user, plan, bot_application, admin)
                        
                    
        except:
            pass

from modules.utils import process_command, is_admin, cancel, error_callback, error_message, escape_markdown_v2
from modules.actions import exibir_plano

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(context, update.message.from_user.id):
        
        return ConversationHandler.END
    commands_text = """
🛠️ **Comandos de Administração do Bot** 🛠️  

👑 /admins – Gerencia os administradores do bot.  
🚀 /disparo – Envia um plano ou link para todos os usuários.  
⏳ **/expiracao** – Edita a mensagem de expiração do plano.  
💳 **/gateway** – Gerencia as chaves para pagamentos.  
🌟 /vip – Define o grupo VIP com os planos.  
🎬 /inicio – Define as mensagens de boas-vindas.  
📦 **/planos** – Gerencia os planos do bot.  
🔄 **/recuperacao** – Define a mensagem de recuperação de compra.  
📈 /upsell – Gerencia o Upsell.  
▶️ **/start** – Inicia o bot.  
"""
    
    await context.bot.send_message(chat_id=update.message.from_user.id, text=escape_markdown_v2(commands_text), parse_mode='MarkdownV2')

    return ConversationHandler.END



async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton('texto fds', callback_data=f'acessar_ofertas')]
    ]
    reply = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('FDS O TEXTO', reply_markup=reply)
    print(update.message.from_user.id)
    return ConversationHandler.END

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    
    payment_id = manager.create_payment(manager.get_bot_group(context.bot_data['id']), {
        'nome':'planolegal',
        'value':'5.5'
        }, 0,'123')
    keyboard = [
        [InlineKeyboardButton('texto fds', callback_data=f'pagar_{payment_id}')]
    ]
    reply = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('FDS O TEXTO', reply_markup=reply)
    print(update.message.from_user.id)
    return ConversationHandler.END

import modules.payment as payment
async def pagar(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    payment_id = query.data.split('_')[-1]
    
    payment_data = manager.get_payment_by_id(payment_id)
    plan = json.loads(payment_data[3])
    value = plan.get('value', False)
    if not value:
        await query.message.edit_text('Valor não encontrado')
    recovery = plan.get('recovery', False)
    if recovery:
        asyncio.create_task(recovery_thread(context, query.from_user.id, recovery, payment_id))


    keyboard = [
            [InlineKeyboardButton('Pagamento Efetuado', callback_data=f'pinto')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        gate = manager.get_bot_gateway(context.bot_data['id'])
        if not gate.get('type', False):
            await query.message.edit_text('Nenhuma gateway cadastrada')
            return ConversationHandler.END

        if not gate.get('token', False):
            await query.message.edit_text('Nenhuma gateway valida cadastrada')
            return ConversationHandler.END

        qr_data = {}

        if gate.get('type') == 'pp':
            qr_data = payment.criar_pix_pp(gate['token'], plan['value'])
            print(qr_data)
        elif gate.get('type') == 'MP':
            qr_data = payment.criar_pix_mp(gate['token'], plan['value'])
        payment_qr = qr_data.get('pix_code', False)
        trans_id = qr_data.get('payment_id', False)
       
        if not payment_qr or not trans_id:
            
            await query.message.edit_text('Erro ao gerar QRCODE tente novamente')
            return ConversationHandler.END

        manager.update_payment_id(payment_id, trans_id)
        manager.update_payment_status(payment_id, 'waiting')
        #await query.message.edit_text(f'Confirme o plano\:\n>Nome\: {escape_markdown_v2(plano['name'])} {names[plano['time_type']]}\n>Tempo\: {escape_markdown_v2(plano['time'])} {escape_markdown_v2(names[plano['time_type']])}\n>Valor\: {escape_markdown_v2(str(plano['value']))}', parse_mode='MarkdownV2')
        
        await context.bot.send_message(query.from_user.id, f'**Aguarde um momento enquanto preparamos tudo**', parse_mode='MarkdownV2')
        await context.bot.send_message(query.from_user.id, f'{escape_markdown_v2('Para efetuar o pagamento, utiliza a opção "Pagar" > "PIX copia e Cola" no aplicativo do seu banco.')}', parse_mode='MarkdownV2')
        #Copie o qr abaixo
        #>`{escape_markdown_v2(payment_qr)}`
        await context.bot.send_message(query.from_user.id, f'Copie o qr abaixo', parse_mode='MarkdownV2')
        await context.bot.send_message(query.from_user.id, f'`{escape_markdown_v2(payment_qr)}`', parse_mode='MarkdownV2')
        await context.bot.send_message(query.from_user.id, f'**Após efetuar o pagamento clique nesse botão**', parse_mode='MarkdownV2', reply_markup=reply_markup)
    
       
    
    except Exception as e:
        await query.message.edit_text('Ocorreu um erro ao executar tarefa de pagamentos')

    return ConversationHandler.END

async def acessar_planos_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if await is_admin(context, update.message.from_user.id):
            return ConversationHandler.END
    except:
        print('penis')


async def run_bot(token, bot_id):

# [NOTA PARA MODIFICAÇÕES]
# Ao requisitar bot application ou bot instance sempre referenciar a variavel global
# Definir novamente a variavel pode gerar conflitos de hierarquia e escopo

    global bot_application
 
# Caso o bot não carregue o processo atual sera encerrado
    disable_get_updates(token)
    bot_application = Application.builder().token(token).build()
    bot_application.add_handler(conv_handler_grupo)
    bot_application.add_handler(conv_handler_upsell)
    bot_application.add_handler(conv_handler_planos)
    bot_application.add_handler(conv_handler_adeus)
    bot_application.add_handler(conv_handler_recuperacao)
    bot_application.add_handler(conv_handler_inicio)
    bot_application.add_handler(conv_handler_admin)
    bot_application.add_handler(conv_handler_gateway)
    bot_application.add_handler(conv_handler_disparo)
    bot_application.add_handler(ChatJoinRequestHandler(check_join_request))
    bot_application.add_handler(CallbackQueryHandler(pagar, pattern='^pagar_'))
    bot_application.add_handler(CallbackQueryHandler(acessar_planos, pattern='^acessar_ofertas$'))
    bot_application.add_handler(CallbackQueryHandler(confirmar_plano, pattern='^plano_'))
    bot_application.add_handler(CallbackQueryHandler(exibir_plano, pattern='^exibir_'))
    bot_application.add_handler(CommandHandler('debug', debug))
    bot_application.add_handler(CommandHandler('start', start))
    bot_application.add_handler(CommandHandler('comandos', comandos))
    bot_application.add_handler(CallbackQueryHandler(cancel, pattern='cancelar'))
    bot_application.add_handler(MessageHandler(~filters.COMMAND, acessar_planos_force))
    bot_application.bot_data['id'] = bot_id
    await bot_application.initialize()
    await bot_application.start()
    await bot_application.updater.start_polling()
    



# Grupo - Feito e testado e modulado
# Upsell - Feito e testado e modulado
# Expiração - Feito e testado e modulado
# Planos - Feito e testado e modulado
# Inicio - Feito e testado e modulado
# Recuperação - Feito e testado e modulado
# Admin - Feito e testado e modulado
#Gateway - Feito e testasdo e modulado


#Disparo

#Start

# - Processos -
# Pagamentos
# Expiração

# - Funções - 
# Manipular users
# Manipular pagamentos
# Webserver

######################################################################







#async def main():
#    """Executa o bot e a task de loop assíncrono simultaneamente."""
#    await asyncio.gather(
#        run_bot('7552906520:AAE4_OvgmU2ZblsVmtihm7v_Rr7XNGri4So', '123'),
#        #payment_task()
#    )

# Executa as tarefas assíncronas
    # Executa o bot de forma assíncrona sem bloquear
  # Polling assíncrono


async def main_start(token, id):
    """Executa o bot e outras tarefas simultaneamente"""
    await asyncio.gather(
        run_bot(token, id),
        payment_task(),
        expiration_task()
    )

def disable_get_updates(token):
    url = f"https://api.telegram.org/bot{token}/close"
    response = requests.post(url)

    if response.status_code == 200:
        print("✅ getUpdates desativado com sucesso!")
    else:
        print(f"❌ Erro ao desativar getUpdates: {response.text}")

def run_bot_sync(token, bot_id):
    """Executa o bot sincronamente dentro do novo processo."""
    asyncio.run(main_start(token, bot_id))

#def run_bot_sync(token,bot_id):
#    loop = asyncio.new_event_loop()
#    asyncio.set_event_loop(loop)
#    loop.create_task(payment_task())
#    loop.run_until_complete(run_bot(token, bot_id))

# Inicia o bot caso esteja no processo principal e possua argumentos validos
#if __name__ == '__main__':
#    import sys
#    if len(sys.argv) < 2:
#        print("Por favor, forneça o token do bot como argumento.")
#    else:
#        run_bot(sys.argv[1])
#        asyncio.run(main(sys.argv[0], sys.argv[1]))
#    loop = asyncio.get_event_loop()
#    loop.create_task(main())
    
# DEVELOPED BY GLOW