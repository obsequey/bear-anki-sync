import re
import os
import sqlite3
import json
import markdown
import shutil
import requests
import yaml

# Patterns
multiline = re.compile('(.+)#flashcard\n((?:.+\n?)+).*')
oneline = re.compile('(.+)\s::\s(.+)\n')

ANKI_CONNECT = 'http://localhost:8765'


def find_cards_by_tag(tag):
    payload = json.dumps({
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": "tag:%s" % tag
        }
    })
    try:
        request = requests.post(ANKI_CONNECT, data=payload)
        if request.json()['error']:
            raise ValueError("Couldn't find cards by tag in Anki. Error: %s" % request.json()['error'])
        return request.json()['result']
    except requests.exceptions.RequestException:
        print("ERROR: couldn't find notes by tag \"%s\"" % tag)
        exit(1)


def delete_cards_by_tag(tag):
    notes = find_cards_by_tag(tag)
    payload = json.dumps({
        "action": "deleteNotes",
        "version": 6,
        "params": {
            "notes": notes
        }
    })
    try:
        request = requests.post(ANKI_CONNECT, data=payload)
        if request.json()['error']:
            raise ValueError("Couldn't delete cards by tag in Anki. Error: %s" % request.json()['error'])
        return request
    except requests.exceptions.RequestException:
        print("ERROR: couldn't delete notes by tag \"%s\"" % tag)
        exit(1)


def create_deck(deck):
    print("DEBUG: creating deck \"" + deck + "\"")
    payload = json.dumps({
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck
        }
    })

    try:
        request = requests.post(ANKI_CONNECT, data=payload)
        if request.json()['error']:
            raise ValueError("Couldn't add the deck to Anki. Error: %s" % request.json()['error'])
    except requests.exceptions.RequestException:
        print("ERROR: couldn't create the deck \"%s\"" % deck)
        exit(1)


# 
def update_card(card):
    # Find the card's id
    payload = json.dumps({
        "version": 6,
        "action": "findNotes",
        "params": {
            "query": "deck:Bear \"front:%s\"" % card['Front']
        }
    })

    try:
        request = requests.post(ANKI_CONNECT, data=payload)
        if request.json()['error']:
            raise ValueError("Couldn't find the note %s in Anki. Error: %s" % (card['Front'], request.json()['error']))
        if len(request.json()['result']) is 0:
            raise ValueError("Didn't find any notes in Anki. Check the search query.")
    except requests.exceptions.RequestException:
        print("ERROR: couldn't find the note \"%s\"" % card['Front'])
        exit(1)

    card['id'] = request.json()['result'][0]

    # Update the card's Back
    payload = json.dumps({
        "version": 6,
        "action": "updateNoteFields",
        "params": {
            "note":{
                "id": card['id'],
                "fields": {
                    "Back": card['Back']
                }
            }
        }
    })

    try:
        request = requests.post(ANKI_CONNECT, data=payload)
        if request.json()['error']:
            raise ValueError("Couldn't update the card. Error: %s" % request.json()['error'])
    except requests.exceptions.RequestException:
        print("ERROR: couldn't update the card \"%s\"" % card['Front'])
        exit(1)


def add_card_to_anki(card, deck):
    anki_tag = 'bear'
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck,
                "modelName": "Basic",
                "fields": card,
                "options": {
                    "allowDuplicate": False,
                    "duplicateScope": "deck",
                    "duplicateScopeOptions": {
                        "deckName": deck,
                        "checkChildren": False,
                        "checkAllModels": False
                    }
                },
                "tags": [anki_tag]
            }
        }
    }

    try:
        request = requests.post(url=ANKI_CONNECT, json=payload)
        if request.json()['error']:
            raise ValueError(request.json()['error'])
        print("DEBUG: Added card " + card['Front'] + " to " + deck)
    except requests.exceptions.RequestException:
        print("ERROR: couldn't add the card " + card['Front'] + " to " + deck)
        exit(1)
    except ValueError as e:
        if e.args[0] == "cannot create note because it is a duplicate":
            update_card(card)
        else:
            exit(1)


def transform_markdown_to_html(text):
    text = text.replace("- ", "", 1)
    text = text.replace("* ", "", 1)

    words = text.split()  # Split the string into words
    # Remove the '~' character from the beginning and end of each word
    cleaned_words = [word.strip('~') for word in words]
    # Reconstruct the cleaned string
    text = ' '.join(cleaned_words)

    return markdown.markdown(text, extensions=['fenced_code', 'nl2br'])


def get_deck_value(text):
    try:
        match = re.search(r'^---\n(.*)\n---', text, re.DOTALL)
        # Check if a match was found
        if match:
            yaml_block = match.group(1)
            yaml_dict = yaml.load(yaml_block, Loader=yaml.FullLoader)
            try:
                anki_deck_value = yaml_dict['anki_deck']
                print("DEBUG: anki_deck value is %s" % anki_deck_value)
            except:
                print("DEBUG: No anki_deck value")
                raise ValueError("No anki_deck was found")
        else:
            raise ValueError("No deck was found")
    except Exception as e:
        anki_deck_value = 'Unsorted'


    return anki_deck_value


def search_and_add_cards(db, pattern):
    for (text, title) in db.execute("select ZTEXT, ZTITLE from ZSFNOTE where ZTRASHED=0 and ZARCHIVED=0"):
        if not text:
            print("WARN : empty text")
            continue
        for (question, answer) in pattern.findall(text):
            print("DEBUG: processed \"" + title + "\" note")
            print("DEBUG: question is \"" + question + "\"")
            print("DEBUG: answer is \"" + answer + "\"")
            card = {'Front': transform_markdown_to_html(question), 'Back': transform_markdown_to_html(answer)}
            deck = "Bear::%s" % get_deck_value(text)
            create_deck(deck)
            add_card_to_anki(card, deck)


def main():
    BEAR_DB_PATH = "/Users/burna/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite"
    # Copy sqlite db to avoid locking the Bear app
    BEAR_DB_COPY_DIR = "/Users/burna/.bear-anki-sync/"

    if os.path.exists(BEAR_DB_COPY_DIR):
        print("DEBUG: folder %s already exists" % BEAR_DB_COPY_DIR)
    else:
        os.makedirs(BEAR_DB_COPY_DIR)
        print("DEBUG: creating %s folder" % BEAR_DB_COPY_DIR)

    BEAR_DB_COPY_PATH = BEAR_DB_COPY_DIR + "database.sqlite"

    shutil.copy(BEAR_DB_PATH, BEAR_DB_COPY_DIR)

    db = sqlite3.connect(BEAR_DB_COPY_PATH)
    create_deck("Bear")
    search_and_add_cards(db, multiline)
    search_and_add_cards(db, oneline)


if __name__ == "__main__":
    main()
