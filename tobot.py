import logging
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define states for conversation flow
SELECTING_CHAIN, TYPING_TOKEN, TYPING_PORTAL, SELECTING_SLOT = range(4)

# Define a few command handlers. These usually take the two arguments update and context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("ETH", callback_data='ETH')],
        [InlineKeyboardButton("BNB", callback_data='BNB')],
        [InlineKeyboardButton("SOL", callback_data='SOL')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text('Select chain:', reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text('Select chain:', reply_markup=reply_markup)
    
    return SELECTING_CHAIN

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Send me your token address.")
    
    # Store the chain selection in the context for future use
    context.user_data['chain'] = query.data
    return TYPING_TOKEN

async def token_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle token address input."""
    user_address = update.message.text
    context.user_data['token_address'] = user_address

    # Ask the user what they want to order
    order_keyboard = [
        [InlineKeyboardButton("Trending Fast-Track", callback_data='Fast-Track')]
    ]
    order_reply_markup = InlineKeyboardMarkup(order_keyboard)
    await update.message.reply_text('What do you want to order?', reply_markup=order_reply_markup)
    return SELECTING_SLOT

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle order selection."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Send me portal/group link.")
    return TYPING_PORTAL

async def portal_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle portal/group link input."""
    portal_link = update.message.text
    # Regex pattern to validate a Telegram link
    telegram_link_pattern = re.compile(r'(https?://)?(www\.)?(t\.me|telegram\.me)/[a-zA-Z0-9_]+')
    
    if telegram_link_pattern.match(portal_link):
        context.user_data['portal_link'] = portal_link
        # Ask the user to select an open slot
        slot_keyboard = [
            [
                InlineKeyboardButton("Top 3 Guarantee", callback_data='Top 3 Guarantee'),
                InlineKeyboardButton("Top 8 Guarantee", callback_data='Top 8 Guarantee')
            ],
            [InlineKeyboardButton("Any position", callback_data='Any position')]
        ]
        slot_reply_markup = InlineKeyboardMarkup(slot_keyboard)
        await update.message.reply_text(
            'Select open slot or click to see the nearest potential availability time:',
            reply_markup=slot_reply_markup
        )
        return SELECTING_SLOT
    else:
        await update.message.reply_text("Incorrect portal or group link. Please send a valid Telegram link.")
        return TYPING_PORTAL

async def slot_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle slot selection."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"You selected {query.data}.")
    # End the conversation
    return ConversationHandler.END

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /delete command."""
    delete_keyboard = [
        [InlineKeyboardButton("Yes, I'm sure", callback_data='confirm_delete')],
        [InlineKeyboardButton("No", callback_data='cancel_delete')]
    ]
    delete_reply_markup = InlineKeyboardMarkup(delete_keyboard)
    await update.message.reply_text(
        'Are you sure to delete all configuration data?\n'
        'Do not do this if you have paid or are about to pay for this configuration, '
        'as a new payment wallet will be generated next time!',
        reply_markup=delete_reply_markup
    )

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of delete."""
    query = update.callback_query
    await query.answer()
    # Here you would add the logic to delete the configuration data.
    await query.edit_message_text(text="All configuration data has been deleted.")
    # Restart the conversation from the beginning
    return await start(query, context)

async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancellation of delete."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Deletion cancelled.")
    # End the conversation
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Insert your API token here
    token = '7357601045:AAEb_YpC7vOwZcFpowBZJDd2v3kuabMhKBo'
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Define conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_CHAIN: [CallbackQueryHandler(button, pattern='^(ETH|BNB|SOL)$')],
            TYPING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, token_address)],
            TYPING_PORTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, portal_group_link)],
            SELECTING_SLOT: [
                CallbackQueryHandler(order, pattern='^(Fast-Track)$'),
                CallbackQueryHandler(slot_selection, pattern='^(Top 3 Guarantee|Top 8 Guarantee|Any position)$')
            ]
        },
        fallbacks=[]
    )

    # Add conversation handler to application
    application.add_handler(conv_handler)

    # Add delete command handler
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CallbackQueryHandler(confirm_delete, pattern='^confirm_delete$'))
    application.add_handler(CallbackQueryHandler(cancel_delete, pattern='^cancel_delete$'))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
