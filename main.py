import re
import sqlite3
import markdown
import requests

BEAR_DB_PATH = "/Users/burna/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite"

# Patterns
multiline = re.compile('(.+)#flashcard\n((?:.+\n?)+).*')
oneline = re.compile('(.+)\s::\s(.+)\n')

ANKI_CONNECT = 'http://localhost:8765'


def delete_cards_by_tag(tag):
    payload = {
        "action": "deleteNotes",
        "version": 6,
        "params": {
            "tags": [tag]
        }
    }
    request = requests.post(ANKI_CONNECT, data=payload)


def add_card_to_anki(card):
    anki_tag = 'bear'
    default_deck = 'Default'
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": default_deck,
                "modelName": "Basic",
                "fields": card,
                "options": {
                    "allowDuplicate": False,
                    "duplicateScope": "deck",
                    "duplicateScopeOptions": {
                        "deckName": default_deck,
                        "checkChildren": False,
                        "checkAllModels": False
                    }
                },
                "tags": [anki_tag]
            }
        }
    }
    request = requests.post(ANKI_CONNECT, json=payload)
    print("DEBUG: Added card " + card['Front'] + " to " + default_deck)


def transform_markdown_to_html(text):
    return markdown.markdown(text, extensions=['fenced_code', 'nl2br'])


def search_and_add_cards(db, pattern):
    for (text, title) in db.execute("select ZTEXT, ZTITLE from ZSFNOTE"):
        if not text:
            print("WARN: empty text")
            continue
        for (question, answer) in pattern.findall(text):
            print("DEBUG: processed \"" + title + "\" note")
            print("DEBUG: question is \"" + question + "\"")
            print("DEBUG: answer is \"" + answer + "\"")
            card = {'Front': title + " > " + question.strip(), 'Back': transform_markdown_to_html(answer.strip())}
            add_card_to_anki(card)


def main():
    db = sqlite3.connect(BEAR_DB_PATH)
    delete_cards_by_tag('bear')
    search_and_add_cards(db, multiline)
    search_and_add_cards(db, oneline)


if __name__ == "__main__":
    main()
