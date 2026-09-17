import os
import json
import ollama
import sqlite3
from database import setup_database
from pydantic import validate_email
from database import (add_assigment, get_assignments,complete_assignment,delete_assignment)

if os.path.exists("memory.txt"):
    with open("memory.txt", "r") as file:
        name = file.read()
    print ("welcome back," + name + ".")
else:
    name = input ("i don't know your name yet. What's your name?")
    with open("memory.txt","w") as file:
        file.write(name)
    print("Got it. Ill remember you" + name + ".")
if os.path.exists("chat_memory.json"):
    with open("chat_memory.json","r") as file:
        messages = json.load(file)
else:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a personal AI assistant."
                "Remember facts the user tells you during the conversation."
                "When the user says 'my',they are referring to themselves, not you."
                "Use earlier messages to answer follow-up questions"
            )
        }
    ]
if os.path.exists ("user_memory.json"):
    with open ("user_memory.json","r") as file:
        user_memory = json.load(file)
else:
    user_memory={}

mode =  input("Choose a mode:chill or pro:")
if mode == "chill":
    print ("Yo"+ name + ",what's good?")
elif mode == "pro":
    print ("Welcome, " +name +" How may i assist you?")
else:
    print ("i don't recognize that mode.")
conn = sqlite3.connect("taroyo.db")
cursor = conn.cursor()
cursor.execute ("""CREATE TABLE IF NOT EXISTS user_memory ( key TEXT PRIMARY KEY, value Text
)
               """)
for key, value in user_memory.items():
    cursor.execute('INSERT OR IGNORE INTO user_memory("key",value)VALUES (?,?)',
                   (key, value)
                   )
    conn.commit()
    cursor.execute('SELECT "key", value FROM user_memory')
    memory_rows = cursor.fetchall()
    user_memory = {}
    for key, value in memory_rows:
        user_memory[key] = value
setup_database()
while True:
    message = input ("You:").strip()
    if message.lower().startswith("add homework"):
        parts = message.split("|")

        if len(parts) == 4:
            class_name = parts[1].strip()
            assignment_name = parts[2].strip()
            due_date = parts[3].strip()

            add_assigment(class_name, assignment_name, due_date)

            print("Taroyo:Assignment added.")
            continue
        else:
            print("Taroyo:Use this format:")
            print("add homework | class| assignment|due date")
            continue
    if message.lower() =="show homework":
        assignments= get_assignments()
        if not assignments:
            print("Taroyo: You have no assignments stored.")
            continue
        print ("Taroyo: Here's your homework:")


        for assignment in assignments:
            assignment_id = assignment[0]
            class_name = assignment[1]
            assignment_name = assignment[2]
            due_date= assignment[3]
            completed = assignment[4]

            status = "Done" if completed else "Not Done"
            print(
                f"{assignment_id}.{class_name} -"
                f"{assignment_name} - Due:{due_date} - {status}"
            )
        continue
    if message.lower().startswith("complete homework"):
        parts= message.split()

        if len(parts) == 3 and parts[2].isdigit():
            assignment_id = int(parts[2])
            complete_assignment(assignment_id)

            print(f"Taroyo:Homework{assignment_id} marked complete.")
            continue
        else:
            print("Taroyo: Use this format: complete homework 1")
            continue
    if message.lower().startswith("delete homework"):
        parts = message.split()

        if len(parts) == 3 and parts[2].isdigit():
            assignment_id= int(parts[2])

            delete_assignment(assignment_id)

            print(f"Taroyo: Homework {assignment_id} deleted.")
            continue
        else:
            print("Taroyo: Use this format:delete homework 3")
            continue

    if message == "quit":
        print("Goodbye," + name + ".")
        break
    messages.append ({
        "role": "user",
        "content": message
    })
    lower_message= message.lower().strip()
    prefixes = [
        "what is my favorite ",
        "what's my favorite ",
        "who is my favorite ",
        "who's my favorite "
    ]
    memory_answered = False
    for prefix in prefixes:
        if lower_message.startswith(prefix):
            subject= lower_message [len(prefix):].rstrip("?.!")
            key ="favorite_" + subject.replace(" ","_")
            if key in user_memory:
                ai_reply =f"Your favorite {subject} is  {user_memory[key]}."
                print("AI",ai_reply)
                messages.append({
                    "role": "assistant",
                    "content":ai_reply
                })
                with open("chat_memory.json","w") as file:
                    json.dump(messages,file)
                memory_answered = True
                break
    if memory_answered:
        continue

    if not message.endswith("?"):
        memory_check = ollama.chat(
         model="qwen2.5:0.5b-instruct",
         messages =[
             {
                 "role":"system",
                 "content": (
                     "Analyze the user's message for a useful long-term personal fact."
                     "Only set remember to true when the user is giving or correcting a personal fact."
                     "Id the user is asking a question, return remember false."
                     "Do not guess or invent values."
                     "Return ONLY one valid JSON object."
                     "Do not repeat words."
                     "Do not explain your answer."
                     "Do not add text before or after the JSON."
                     "Return ONLY JSON in this format:"
                     '{"remember" : true, "key": "example_key", "value":"example_value"} '
                     "If there is nothing useful to remember, return:"
                        '{"remember":false}'
                                 )
             },
             {
                 "role":"user",
                 "content": message
             }
         ]
        )
        try:
            memory_data= json.loads(memory_check.message.content)
        except json.JSONDecodeError:
            memory_data={"remember":False}
        blocked_keys={
            "message",
            "user_message",
            "text",
            "input"

        }

        if memory_data.get("remember") == True:
            key = memory_data.get("key")
            value = memory_data.get("value")
            if key and value and key not in blocked_keys:
                user_memory[key]=value
                cursor.execute('INSERT OR REPLACE INTO user_memory ("key",value) VALUES (?,?)',
                               (key,value)
                               )

                with open("user_memory.json","w") as file:
                    json.dump(user_memory,file)
        print(user_memory)
    request_messages = [
        {
            "role":"system",
            "content": "long-term user memory : " + str(user_memory)

        }
    ] + messages

    response = ollama.chat (
        model = "qwen2.5:0.5b-instruct",
        messages=request_messages
    )
    ai_reply=response.message.content
    print("AI",ai_reply)

    messages.append({
       "role":"assistant",
       "content":ai_reply
    })


with open("chat_memory.json", "w") as file:
    json.dump(messages,file)
