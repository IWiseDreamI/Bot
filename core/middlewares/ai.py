import os
import json
from dotenv import find_dotenv, load_dotenv
from db.queries import get_topic_random_word
from openai import OpenAI

load_dotenv(find_dotenv())
PROXY_API_KEY = os.environ.get("AI_API_KEY")

client = OpenAI(
    api_key=PROXY_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

requests = {
    "missing": """Составь 3 разных вопроса в формате предложения с пропущенным словом |rword|(|eword|) на тему |topic| с ответом |rword|. 
    Верни список составленных вопросов в формате json пример ниже, в поля eng и rus вставляй предложения без пропущенных слов
    {
        "eng": "The net is the barrier dividing the court. Players hit the ball over it, aiming for the opponent's side. ",
        "rus": "Сетка - это барьер, разделяющий корт. Игроки отбивают мяч через нее, целясь в сторону соперника.",
        "eng_answer": "Net",
        "rus_answer": "Сетка",
        "quest_type": "missing",
        "difficulty": "0",
        "topic": "|topic|"
    }
    """,
    "knowledge": """Составь 3 разных вопроса на тему |topic| с коротким ответом |eword|, верни список составленных вопросов в формате json пример ниже   
    {
        "eng": "",
        "rus": "",
        "eng_answer": "|eword|",
        "rus_answer": "|rword|",
        "quest_type": "knowledge",
        "difficulty": "0",
        "topic": "|topic|"
    }
    """,
    "definition": """Составь 3 разных вопроса на тему |topic| с ответом |eword|, верни список составленных вопросов в формате json пример ниже   
    {
        "eng": "",
        "rus": "",
        "eng_answer": "",
        "rus_answer": "",
        "quest_type": "definition",
        "difficulty": "0",
        "topic": "|topic|"
    }
    """,
    "translate": """Составь 3 коротких предложений по тематике |topic| и запиши это в json формате, пример ниже
    {
        "eng": "",
        "rus": "",
        "quest_type": "translate",
        "difficulty": "0",
        "topic": "|topic|"
    }
    """,
    "boolean": """Составь 3 разных вопроса по тематике |topic| в формате правда или ложь.
    Запиши это в json формате, пример ниже, в полях rus_answer = (Правда или Ложь), eng_answer = (True/False)
    {
        "eng": "",
        "rus": "",
        "eng_answer": "",
        "rus_answer": "",
        "quest_type": "boolean",
        "difficulty": "0",
        "topic": "|topic|"
    }
    """
}

def get_question(topic, qt):
    word = get_topic_random_word(topic)
    answer = False
    text = requests[qt].replace("|topic|", topic).replace("|rword|", word.rus).replace("|eword|", word.eng)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Ты - преподаватель английского языка, обладаешь большим словарным запасом, в частности в области {topic}"},
            {"role": "user", "content": text}
        ]
    )

    try: answer = json.loads(completion.choices[0].message.content)
    except: pass
    
    return answer


def check_translate_ai(quest_text, user_text, topic):
    answer = False
    text = """Является ли предложение 2 правильным переводом предложения 1 на другой язык? Правильно ли составлено предложение 2? Предложения написаны на разных языках? Отвечай в json формате {"translate":  "True",  "correct": "True", "different_lang": "True"}
    
    1. quest_text
    2. user_text
    """.replace("quest_text", quest_text).replace("user_text", user_text)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Ты - переводчик, понимаешь смысл предложений в сфере {topic} на русском и английском языках и можешь их переводить."},
            {"role": "user", "content": text}
        ]
    )

    try: 
        answer = json.loads(completion.choices[0].message.content)
        answer = answer["translate"] == "True" and answer["correct"] == "True" and answer["different_lang"] == "True"
    
    except: pass

    return answer



# def gen_sentence(topic):
#     messages = [SystemMessage(
#         content=f"Ты - преподаватель английского языка, обладаешь большим словарным запасом, в частности в области {topic}"
#     )]

#     text = f"""Составь 10 коротких предложений по тематике {topic} и запиши это в json формате, пример ниже
#     {{
#         "eng": "Lose a point.",
#         "rus": "Проиграть очко.",
#         "quest_type": "translate",
#         "difficulty": "0"
#     }}
#     """

#     messages.append(HumanMessage(content=text))
#     res = chat(messages)
#     messages.append(res)

#     return res.content