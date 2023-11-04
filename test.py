import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import filters, MessageHandler, ContextTypes, ApplicationBuilder, CallbackContext, CommandHandler, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# States for the conversation
WAIT_TEXT = 1

WAIT_SEARCH, WAIT_SELECTION = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username

    first_name = user.first_name
    last_name = user.last_name
    
    if first_name and last_name:
        # User has both first name and last name
        full_name = f"{first_name} {last_name}"
    elif first_name:
        # User has only first name
        full_name = first_name
    else:
        # User does not have first name (unlikely to happen)
        full_name = "User"
    
    response_text = f"Hello, {full_name}! \nWelcome to the Past Questions bot!"
    
    # Send the response to the user
    reply_keyboard=[["/search"],["/request"]]
    await update.message.reply_photo("./images/start.png")
    await update.message.reply_text(response_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
    ))

async def helps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
           /start -> Welcome to the past question bot
           \n/help -> This particular messsage 
        """
        )

# Your mock database
mock_database = [
    {"filename": "UHAS.pdf", "description": "Description 1"},
    {"filename": "UHAS.pdf", "description": "Description 2"},
    {"filename": "UHAS.pdf", "description": "Description 3"},
    {"filename": "UHAS.pdf", "description": "Description 4"},
]

async def search(update: Update, context: CallbackContext):
    await update.message.reply_text("Input the course's past question you want")
    # Set the conversation state to WAIT_SEARCH
    context.user_data['state'] = WAIT_SEARCH
    return WAIT_SEARCH

async def query_selection(update: Update, context: CallbackContext):
    # Process the search query
    query = update.message.text.lower()
    results = [file for file in mock_database if query in file["filename"].lower()]

    if results:
        # Store the results in context.user_data for later use
        context.user_data['results'] = results
        file_list = "\n".join([f'{i+1}. {file["filename"]} - {file["description"]}' for i, file in enumerate(results)])
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
            await update.message.reply_text("your file is downloading")
            reply_keyboard=[["/search"],["/request"],['/help'],['/exit']]
            await update.message.reply_document(document=open(selected_file, 'rb'), parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
            ))
        else:
            await update.message.reply_text("Invalid selection. Please enter a valid number.")
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a valid number.")

    # End the conversation after handling the selection
    return ConversationHandler.END

async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your text:")
    # Set the conversation state to WAIT_TEXT
    context.user_data['state'] = WAIT_TEXT



def handle_input(update: Update, context: CallbackContext):
    user_input = update.message.text

    # Process the user input here
    update.message.reply_text(f"You sent: {user_input}")
    # Process the user input and save it to a file
    save_to_file(user_input, context)
    update.message.reply_text("Your input has been saved.")
    return ConversationHandler.END  # End the conversation after processing the input
   
    

def save_to_file(user_input, context: CallbackContext):
    with open('requests.txt', 'a') as file:
        file.write(user_input + '\n')


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    logging.error(f"Error occurred: {context.error}")
    await update.message.reply_text("An error occurred while processing your request. Please try again later.")



if __name__ == '__main__':
    application = ApplicationBuilder().token('6828345237:AAFjNS-P9Iv62OovrIRnCWk5vFljiG0YRuo').build()

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
        fallbacks=[]
    )
    application.add_handler(search_handler)

    search_handler = CommandHandler("search", search)
    if search_handler:
        application.add_handler(search_handler)

        query_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), query_selection)
        application.add_handler(query_handler)

        selection_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_selection)
        application.add_handler(selection_handler)




    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("request", request)],
        states={
            WAIT_TEXT: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_input)],
        },
        fallbacks=[],
    )

    application.add_handler(conversation_handler)


    application.add_error_handler(error_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()