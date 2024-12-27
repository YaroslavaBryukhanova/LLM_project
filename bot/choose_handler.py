from .globals import authenticated_users, active_files
from .database import cursor, conn

class ChooseHandler:
    
    def __init__(self, bot):
        self.bot = bot

    def handle_choose_command(self, message):
        chat_id = message.chat.id
        # Check if user is authenticated
        if chat_id not in authenticated_users or not authenticated_users[chat_id].get("authenticated"):
            self.bot.send_message(chat_id, "Please log in first by typing /start.")
            return
        
        # Query the database to get a list of files the user has uploaded
        cursor.execute("SELECT filename FROM user_files WHERE chat_id = ?", (chat_id,))
        files = cursor.fetchall()

        if files:
            # Send the list of files to the user
            file_list = "\n".join(f"{index + 1}. {file[0]}" for index, file in enumerate(files))
            self.bot.send_message(
                chat_id,
                f"You have the following uploaded files:\n{file_list}\n\n"
                "Please reply with the number of the file you want to choose or type 'new' to upload a new file."
            )

            # Save the list of files in user data for later selection
            authenticated_users[chat_id]["file_options"] = files
        else:
            self.bot.send_message(chat_id, "You don't have any uploaded files. Please upload a PDF file to get started.")

    def handle_file_selection(self, message):
        chat_id = message.chat.id
        user_data = authenticated_users[chat_id]
        text = message.text.strip()

        if text.lower() == 'new':
            self.bot.send_message(chat_id, "Please upload a new PDF file.")
            return

        try:
            choice_index = int(message.text.strip()) - 1  # Convert to zero-based index
            if 0 <= choice_index < len(user_data["file_options"]):
                selected_file = user_data["file_options"][choice_index][0]
                active_files[chat_id] = selected_file  # Set the selected file as active
                
                self.bot.send_message(chat_id, f"You have selected '{selected_file}' to ask questions about.")
                del user_data["file_options"]  # Clear options once a file is selected
            else:
                self.bot.send_message(chat_id, "Invalid choice. Please reply with the correct file number.")
        except ValueError:
            self.bot.send_message(chat_id, "Please reply with a valid file number.")