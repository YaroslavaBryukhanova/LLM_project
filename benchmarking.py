import PyPDF2
import requests
import csv
import time
from google.api_core import retry
from google.api_core import exceptions
import json

API_KEY = "AIzaSyDQwaWd2mUS-ySLPQIN7ar1VTcNTsjMm34"

documents = []

id = 1

def extract_text_from_pdf(pdf_path):
    global id
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            if page_num > 200:
                return
            page = pdf_reader.pages[page_num]
            current_page = page.extract_text()
            current_page = current_page.replace('\n', ' ')
            if current_page == '':
                continue
            documents.append({'id': f"doc{id}", 'content': current_page})
            id += 1


@retry.Retry(predicate=retry.if_exception_type(exceptions.ResourceExhausted))
def generate_question(content):
    
    example = {
        "id": "Mercury_SC_415702",
        "question": "George wants to warm his hands quickly by rubbing them. Which skin surface will produce the most heat?",
        "choices": {
            "text": [
            "dry palms",
            "wet palms",
            "palms covered with oil",
            "palms covered with lotion"
            ],
            "label": [
            "A",
            "B",
            "C",
            "D"
            ]
        },
        "answerKey": "A"
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Generate one multi-choice question, possible answers and correct answer, based on the following text - {content} in a json format. Here is the structureexample you must follow - {example}"
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})

        print(response.status_code)
        print(response.json()['candidates'][0])
        response_json = response.json()
        answer = response_json['candidates'][0]['content']['parts'][0]['text']
        answer = answer.replace("```json", "")
        answer = answer.replace("```", "")
        if answer:
            answer = json.loads(answer)
            
        question = answer['question']
        choices = answer['choices']['text']
        answer_key = answer['answerKey']
    except Exception as e:
        print(e)
        time.sleep(2)
        return generate_question(content)
    
    print(question, choices, answer_key)
    print()
    return question, choices, answer_key

def create_csv_with_choices(output_file='questions_with_choices.csv'):
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Document ID', 'Question', 'Choices', 'AnswerKey'])
        
        for doc in documents:
            question, choices, answer_key = generate_question(doc['content'])
            writer.writerow([doc['id'], question, choices, answer_key])

def add_column_to_csv():
    # with open('questions_with_choices.csv', 'r', newline='', encoding='utf-8') as file:
    #     reader = csv.reader(file)
    #     rows = list(reader)
    #     rows[0].append('Correct Answer')
    #     with open('questions_with_choices.csv', 'w', newline='', encoding='utf-8') as file:
    #         writer = csv.writer(file)
    #         writer.writerows(rows)
    with open('questions_with_choices.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
        for row in rows[1:]:
            question = row[1]
            choices = row[2]
            answer = estimate_correct_answers(question, choices)
            row.append(answer)
        with open('questions_with_choices.csv', 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        


@retry.Retry(predicate=retry.if_exception_type(exceptions.ResourceExhausted))
def estimate_correct_answers(question, choices):
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Answer the following question: {question} with the following choices: {choices}. As an answer provide only the letter of the correct answer, which is A, B, C or D accordingly to the choices. You must provide only a letter, don't answer with the whole sentence."
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(response.status_code)
        response_json = response.json()
        answer = response_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(e)
        time.sleep(2)
        return estimate_correct_answers(question, choices)
            
    print(answer)
    print()
    return answer



def main():
    # content = 'src/AI_material.pdf'
    # extract_text_from_pdf(content)
    # create_csv_with_choices()
    # add additional column to the csv file for the correct answer
    add_column_to_csv()


if __name__ == '__main__':
    main()