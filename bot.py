import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ContextTypes, ApplicationBuilder, CallbackContext, CommandHandler, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# States for the conversation
WAIT_REQUEST= 1
WAIT_SEARCH, WAIT_SELECTION = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    global username
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    
    if first_name and last_name:
        full_name = f"{first_name} {last_name}"
    elif first_name:
        full_name = first_name
    else:
        full_name = "User"
    
    await update.message.reply_photo("./images/start.png")
    
    welcome_message = f"👋 <b>Hello, {full_name}!\n\nWelcome to the Past Questions Bot! </b> 📚\n\n"
    welcome_message += "<b>I'm here to assist you with past question files. Here's what I can do:</b>\n\n"
    welcome_message += "<b>1. /search </b> - Type the name of the past question you want, and I'll find any matching files for you.\n"
    welcome_message += "<b>2. /request </b>- Send your queries and suggestions, and I'll forward them to the bot manager for necessary actions.\n"
    welcome_message += "<b>3. /help </b>- Display available commands and get assistance with how to use this bot.\n\n"
    welcome_message += "Use the <b> /cancel</b> command to halt any process if you no longer need to continue or complete it.\n\n"
    welcome_message += "<i>🎯 Feel free to ask if you have any questions or need assistance! 😊</i>"

    reply_keyboard = [["/search","/request"], ["/help","/cancel"]]
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        )
    )

async def helps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
           /start -> Welcome to the past question bot
           /help -> This particular message 
        """
    )

# mock database
mock_database = [
    {"filename": "UHAS.pdf", "description": "Description 1"},
    {"filename": "UHAS.pdf", "description": "Description 2"},
    {"filename": "UHAS.pdf", "description": "Description 3"},
    {"filename": "UHAS.pdf", "description": "Description 4"},
]

async def search(update: Update, context: CallbackContext):
    initial_message = "Input the course's past question you want"

    reply_keyboard = [["/help","/cancel"]]

    await update.message.reply_text(
        initial_message,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        )
    )

    # Set the conversation state to WAIT_SEARCH
    context.user_data['state'] = WAIT_SEARCH
    return WAIT_SEARCH

async def query_selection(update: Update, context: CallbackContext):
    query = update.message.text.lower()
    results = [file for file in mock_database if query in file["filename"].lower()]

    if results:
        # Store the results in context.user_data for later use
        context.user_data['results'] = results
        file_list = "\n".join([f'{i+1}. {file["filename"]} - {file["description"]} 📁' for i, file in enumerate(results)])
        await update.message.reply_text(f"Matching files:\n{file_list}\n\nType the number to select the file.")
        # Set the conversation state to WAIT_SELECTION
        context.user_data['state'] = WAIT_SELECTION
    else:
        await update.message.reply_text("No matching files found.")
        # End the conversation if no matching files are found
        return ConversationHandler.END

    return WAIT_SELECTION

async def handle_selection(update: Update, context: CallbackContext):
    try:
        selected_index = int(update.message.text) - 1
        results = context.user_data.get('results')

        if 0 <= selected_index < len(results):
            selected_file = results[selected_index]["filename"]
            # Send the selected file to the user
            await update.message.reply_text("Your file is downloading")
            reply_keyboard = [["/search"], ["/request"], ["/help"], ["/exit"]]
            await update.message.reply_document(
                document=open(selected_file, 'rb'), parse_mode='HTML',
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
        else:
            await update.message.reply_text("Invalid selection. Please enter a valid number.")
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a valid number.")

    # End the conversation after handling the selection
    return ConversationHandler.END

async def save_to_file( user_input):
    
    with open('requests.txt', 'a') as file:
        file.write(username + ' sent: ' + user_input + '\n')

async def request(update: Update, context: CallbackContext):
    initial_message = "Please enter your text:"

    reply_keyboard = [["/help","/cancel"]]

    await update.message.reply_text(
        initial_message,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        )
    )
    context.user_data['state'] = WAIT_REQUEST
    return WAIT_REQUEST

async def handle_input(update: Update, context: CallbackContext):
    user_input = update.message.text

    # Process the user input here
    await update.message.reply_text(f"You sent: {user_input}")
    # Process the user input and save it to a file
    await save_to_file(user_input)
    await update.message.reply_text("Your input has been saved ✅")

    # Clear the conversation state after processing the input
    context.user_data.pop('state', None)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ends the conversation when the user sends /cancel.

    :param update: An object that contains all the incoming update data.
    :param context: A context object containing information for the callback function.
    :return: The next state for the conversation, which is ConversationHandler.END in this case.
    """
    user = update.message.from_user

    response_text = f"Bye! I hope we can talk again some day."
    reply_keyboard = [["/search", "/request"], ["/help", "/cancel"]]
    
    await update.message.reply_text(
        response_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        )
    )

    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Error occurred: {context.error}")
    await update.message.reply_text("An error occurred while processing your request. Please try again later.")

if __name__ == '__main__':
    application = ApplicationBuilder().token('BOT_TOKEN').build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', helps)
    application.add_handler(help_handler)

    search_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            WAIT_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, query_selection)],
            WAIT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(search_handler)

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("request", request)],
        states={
            WAIT_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conversation_handler)

    application.add_error_handler(error_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
