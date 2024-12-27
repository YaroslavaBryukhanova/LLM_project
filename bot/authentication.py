from .database import cursor, conn
from .globals import authenticated_users
from utilis.chromadb_client import chroma_client, embedder
from io import BytesIO
import PyPDF2
import uuid


class Authentication:

    def __init__(self, bot):
        self.bot = bot

    def handle_registration(self, message):
        chat_id = message.chat.id
        user_data = authenticated_users[chat_id]
        text = message.text.strip()

        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        if user:
            # User already registered
            self.bot.send_message(chat_id, "You have already registered. Please log in instead by typing /start.")
            self.bot.send_message(chat_id, "If you forgot your username and password, please type /remind.")
            authenticated_users[chat_id] = {"registration": False, "username": None, "authenticated": True}
            return

        # Registration process
        if not user_data["username"]:
            cursor.execute("SELECT * FROM users WHERE username = ?", (text,))
            if cursor.fetchone():
                self.bot.send_message(chat_id, "Username already taken. Please enter a different username.")
            else:
                user_data["username"] = text
                self.bot.send_message(chat_id, "Username accepted! Now, please enter a password:")
        else:
            cursor.execute("INSERT INTO users (chat_id, username, password) VALUES (?, ?, ?)", (chat_id, user_data["username"], text))
            conn.commit()
            user_data["authenticated"] = True
            # Upload the basic AI material
            cursor.execute("SELECT * FROM user_files WHERE chat_id = ? AND filename = ?", (chat_id, "Introduction to AI.pdf"))
            existing_file = cursor.fetchone()
            if not existing_file:
            # Initialize collection and save PDF content
                existing_collections = chroma_client.list_collections()
                collection_names = [collection.name for collection in existing_collections]
                if "Introduction_to_AI" in collection_names:
                    collection_name = "Introduction_to_AI"
                    collection = chroma_client.get_collection(collection_name)
                else:
                    collection_name = "Introduction_to_AI"
                    collection = chroma_client.create_collection(collection_name)

                with open("src/AI_material.pdf", "rb") as file:
                    pdf_content = BytesIO(file.read())
                    pdf_reader = PyPDF2.PdfReader(pdf_content)
                    num_pages = len(pdf_reader.pages)

                for i in range(num_pages):
                    page = pdf_reader.pages[i]
                    page_text = page.extract_text()
                    id = str(uuid.uuid4())
                    collection.add(documents=[page_text], ids=[id], embeddings=[embedder.encode(page_text).tolist()])

                cursor.execute("INSERT INTO user_files (chat_id, collection_name, filename) VALUES (?, ?, ?)", (chat_id, collection_name, "Introduction to AI.pdf"))
                conn.commit()
            self.bot.send_message(chat_id, "Registration successful! Please upload a PDF file to get started.")

    def handle_login(self, message):
        chat_id = message.chat.id
        user_data = authenticated_users[chat_id]
        text = message.text.strip()

        if not user_data["username"]:
            cursor.execute("SELECT * FROM users WHERE username = ?", (text,))
            row = cursor.fetchone()
            if row:
                user_data["username"] = text
                self.bot.send_message(chat_id, "Username found. Please enter your password:")
            else:
                self.bot.send_message(chat_id, "Username not found. Please start over or register by typing 'yes'.")
                del authenticated_users[chat_id]
        else:
            cursor.execute("SELECT password FROM users WHERE username = ?", (user_data["username"],))
            row = cursor.fetchone()
            if row and row[0] == text:
                user_data["authenticated"] = True
                
                # cursor.execute("SELECT * FROM user_files WHERE chat_id = ? AND filename = ?", (chat_id, "Introduction to AI.pdf"))
                # existing_file = cursor.fetchone()
                # if not existing_file:
                # # Initialize collection and save PDF content
                #     collection_name = "Introduction_to_AI"
                #     collection = chroma_client.create_collection(collection_name)

                #     with open("src/AI_material.pdf", "rb") as file:
                #         pdf_content = BytesIO(file.read())
                #         pdf_reader = PyPDF2.PdfReader(pdf_content)
                #         num_pages = len(pdf_reader.pages)

                #     for i in range(num_pages):
                #         page = pdf_reader.pages[i]
                #         page_text = page.extract_text()
                #         id = str(uuid.uuid4())
                #         collection.add(documents=[page_text], ids=[id], embeddings=[embedder.encode(page_text).tolist()])

                #     cursor.execute("INSERT INTO user_files (chat_id, collection_name, filename) VALUES (?, ?, ?)", (chat_id, collection_name, "Introduction to AI.pdf"))
                #     conn.commit()
                
                cursor.execute("SELECT filename FROM user_files WHERE chat_id = ?", (chat_id,))
                files = cursor.fetchall()
                
                if files:
                    self.bot.send_message(chat_id, "Login successful! You have the following files uploaded:")
                    for file in files:
                        self.bot.send_message(chat_id, file[0])
                else:
                    self.bot.send_message(chat_id, "Login successful! You don't have any uploaded files yet. Please upload a PDF to get started.")
                    
                self.bot.send_message(chat_id, "Please upload a PDF file to continue or type /choose to select a file about which you want to ask questions.")
            else:
                self.bot.send_message(chat_id, "Incorrect password! Please try again.")

    def handle_initial_response(self, message):
        chat_id = message.chat.id
        text = message.text.lower()
        
        # Check if the user is already registered
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        
        if user:
            # If user is registered but types "yes" for registration
            if text == 'yes':
                self.bot.send_message(chat_id, "It looks like you have already registered. Type /remind if you would like me to remind you of your username and password, or type 'no' to log in.")
            elif text == 'no':
                self.bot.send_message(chat_id, "Please enter your username to log in:")
                authenticated_users[chat_id] = {"registration": False, "username": None, "authenticated": False}
            else:
                self.bot.send_message(chat_id, "Invalid response. Please reply 'yes' to retrieve your credentials or 'no' to log in.")
        else:
            # If the user is not registered, proceed with registration or login as usual
            if text == 'yes':
                self.bot.send_message(chat_id, "Please enter your desired username:")
                authenticated_users[chat_id] = {"registration": True, "username": None, "authenticated": False}
            elif text == 'no':
                self.bot.send_message(chat_id, "Please enter your username to log in:")
                authenticated_users[chat_id] = {"registration": False, "username": None, "authenticated": False}
            else:
                self.bot.send_message(chat_id, "Invalid response. Please reply 'yes' to register or 'no' to log in.")
