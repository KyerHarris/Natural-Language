import json
from openai import OpenAI
import os
import mysql.connector
from time import time

print("Running mtg_db_bot.py!")

fdir = os.path.dirname(__file__)

def getPath(fname):
    return os.path.join(fdir, fname)

# OPENAI
configPath = getPath("config.json")
with open(configPath) as configFile:
    config = json.load(configFile)

openAiClient = OpenAI(
    api_key=config["openaiKey"],
    organization=config["orgId"]
)

#MySQL
mysqlCon = mysql.connector.connect(
    host="localhost",
    port=3306,
    user=config["user"],
    password=config["password"],
)
mysqlCursor = mysqlCon.cursor()
database_name = "mtg_db"

def create_database(cursor):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"Database {database_name} created or already exists.")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

create_database(mysqlCursor)

mysqlCon.database = database_name
if mysqlCon.is_connected():
    print("Successfully connected to the database.")
else:
    print("Failed to connect to the database.")

setupSqlPath = getPath("setup.sql")
cardsJsonPath = getPath("cards.json")

with open(setupSqlPath) as setupSqlFile:
    setupSqlScript = setupSqlFile.read()

for statement in setupSqlScript.split(';'):
    if statement.strip():
        mysqlCursor.execute(statement)

# Load data from cards.json
with open(cardsJsonPath, 'r', encoding='utf-8') as cardsFile:
    cardsData = json.load(cardsFile)

# Prepare batch insertion
def insert_batch(cards):
    query = """
    INSERT INTO Cards (id, oracle_id, name, released_at, 
                       mana_cost, cmc, type_line, oracle_text, colors, color_identity, 
                       rarity, artist, set_name, usd_price)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    batch_values = []
    for card in cards:
        # Prepare values for each card (adapting to your table structure)
        values = (
            card['id'],
            card.get('oracle_id', None),
            card['name'],
            card['released_at'],
            card.get('mana_cost', None),
            card.get('cmc', 0),
            card.get('type_line', None),
            card.get('oracle_text', None),
            ','.join(card.get('colors', [])),
            ','.join(card.get('color_identity', [])),
            card.get('rarity', None),
            card.get('artist', None),
            card.get('set_name', None),
            card['prices'].get('usd', None)
        )
        batch_values.append(values)

    try:
        mysqlCursor.executemany(query, batch_values)
        print("batch success\n")
    except mysql.connector.Error as err:
        print(f"Error during batch insertion: {err}")
        mysqlCon.rollback()

# Insert data in batches
batch_size = 1000  # Insert 1000 cards per batch (tweak this based on performance)
for i in range(0, len(cardsData), batch_size):
    batch = cardsData[i:i + batch_size]
    insert_batch(batch)
    mysqlCon.commit()  # Commit after every batch

def runSql(query):
    mysqlCursor.execute(query)
    return mysqlCursor.fetchall()

def getChatGptResponse(content):
    stream = openAiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    return result

# strategies
commonSqlOnlyRequest = " Give me a sqlite select statement that answers the question. Only respond with sqlite syntax. If there is an error, do not explain it!"

strategies = {
    "zero_shot": setupSqlScript + commonSqlOnlyRequest,
    "single_domain_double_shot": (setupSqlScript + 
        " What card has the longest name? " + 
        "\nSELECT name FROM Cards ORDER BY LENGTH(name) DESC LIMIT 1;\n " + 
        commonSqlOnlyRequest)
}

questions = [
    "What card has the longest name?",
    "How many green cards were released in 2024?",
    "What are the top 5 most expensive cards?",
    "How many cards were illustrated by David Robert Hovey?",
    "What are the names of the cards with a mana cost of 0?",
    "How many cards cost 15 mana?",
    "What card has the shortest name?",
    "How many cards are worth more than $1000?"
]

def sanitizeForJustSql(value):
    gptStartSqlMarker = "```sql"
    gptEndSqlMarker = "```"
    if gptStartSqlMarker in value:
        value = value.split(gptStartSqlMarker)[1]
    if gptEndSqlMarker in value:
        value = value.split(gptEndSqlMarker)[0]
    return value

for strategy in strategies:
    responses = {"strategy": strategy, "prompt_prefix": strategies[strategy]}
    questionResults = []
    
    for question in questions:
        print(question)
        error = "None"
        friendlyResponse = ""
        sqlSyntaxResponse = ""
        queryRawResponse = ""
        friendlyResponse = ""
        try:
            sqlSyntaxResponse = getChatGptResponse(strategies[strategy] + " " + question)
            sqlSyntaxResponse = sanitizeForJustSql(sqlSyntaxResponse)
            print(sqlSyntaxResponse)
            queryRawResponse = str(runSql(sqlSyntaxResponse))
            print(queryRawResponse)
            
            friendlyResultsPrompt = f'I asked a question "{question}" and the response was "{queryRawResponse}". Please, just give a concise response in a more friendly way?'
            friendlyResponse = getChatGptResponse(friendlyResultsPrompt)
            print(friendlyResponse)
        except Exception as err:
            error = str(err)
            print(err)

        questionResults.append({
            "question": question,
            "sql": sqlSyntaxResponse,
            "queryRawResponse": queryRawResponse,
            "friendlyResponse": friendlyResponse,
            "error": error
        })

    responses["questionResults"] = questionResults

    with open(getPath(f"response_{strategy}_{time()}.json"), "w") as outFile:
        json.dump(responses, outFile, indent=2)

mysqlCursor.close()
mysqlCon.close()
print("Done!")
