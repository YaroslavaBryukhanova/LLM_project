Final project in ATLLM course

Project includes a telegram bot that helps students to recap lecture material by interacting with the document.
A user needs to register or login, afterwards the user is allowed to ask questions about this PDF.
By default, the user is given an opportunity to ask questions about the "Introduction to AI course".

Bot uses API call to answer user questions. To make answers more accurate RAG system is implemented, as well as modular RAG.

I used Gemini API call, but you can replace API_KEY in utilis/config.py with any other API you prefer.

Key features:

* Sqlite databases to store users info and PDF content

* Temporary caching

* RAG system

* Access to previously uploaded files

* Friendly interface