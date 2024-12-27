import requests
import PyPDF2
import uuid
from io import BytesIO
from .globals import authenticated_users, active_files, cache
from .database import cursor, conn
from utilis.chromadb_client import chroma_client, embedder

from utilis.config import API_KEY

class PDFHandler:

    def __init__(self, bot):
        self.bot = bot

    def handle_pdf_upload(self, message):
        chat_id = message.chat.id
        if authenticated_users.get(chat_id, {}).get("authenticated"):
            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            filename = message.document.file_name
            collection_name = filename
        else:
            self.bot.send_message(chat_id, "Please authenticate first by starting with /start.")
            return
        
        try:
            pdf_content = BytesIO(downloaded_file)
            pdf_reader = PyPDF2.PdfReader(pdf_content)
            num_pages = len(pdf_reader.pages)
            
            # Create a collection for the PDF in the database
            # collection_name = f"user_{chat_id}_pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            collection = chroma_client.create_collection(collection_name)
            #save PDF content to the collection
            for i in range(num_pages):
                page = pdf_reader.pages[i]
                text = page.extract_text()
                id = str(uuid.uuid4())
                collection.add(documents=[text], ids = [id],embeddings=[embedder.encode(text).tolist()])
            print("Collection created: ", collection_name)
            cursor.execute("INSERT INTO user_files (chat_id, collection_name, filename) VALUES (?, ?, ?)", (chat_id, collection_name, filename))
            conn.commit()
            
            self.bot.send_message(chat_id, "PDF file uploaded successfully! You can start asking questions now.")
        except Exception as e:
            self.bot.send_message(chat_id, "An error occurred while processing the PDF file. Please try again.")
            self.bot.send_message(chat_id, "Please, consider this:  Don't upload files with the same filename; The filename should contain only alphanumeric characters (3-63), underscores or hyphens, no (..); The filename also should not be a valid IPv4 address.")
            print(e)

    def handle_question(self, message):
        chat_id = message.chat.id
        question = message.text.strip()
        embedded_question = embedder.encode(question).tolist()
        
        if chat_id not in active_files:
            self.bot.send_message(chat_id, "Please select a file first by typing /choose or upload a PDF file.")
            return
        
        selected_file = active_files[chat_id]

        if question in cache.get(chat_id, {}):
            response = cache[chat_id][question]
            print("Using cache")
        else:
            cursor.execute("SELECT collection_name FROM user_files WHERE chat_id = ? AND filename = ?", (chat_id, selected_file))
            result = cursor.fetchone()
            collection_name = result[0]

            # print all existing collections
            existing_collections = chroma_client.list_collections()
            collection_names = [collection.name for collection in existing_collections]
            print("Existing collections: ", collection_names)


            user_collection = chroma_client.get_collection(collection_name)
            print("User collection: ", user_collection)
            print("Collection name: ", collection_name)
            if user_collection:
                user_context = user_collection.query(
                    query_embeddings=[embedded_question],
                    n_results=3
                )
                data = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"Answer the following question: {question}, based only on this document context: {user_context}"
                                }
                            ]
                        }
                    ]
                }
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
                try:
                    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
                    print("Response status: ", response.status_code, "Using LLM")
                    result = response.json()
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                except:
                    answer = "An error occurred while processing the question. Please try again."
                cache.setdefault(chat_id, {})[question] = answer
                
                response = answer
            
            else:
                response = "Please upload a PDF file first to ask questions about it."
        self.bot.send_message(chat_id, response)