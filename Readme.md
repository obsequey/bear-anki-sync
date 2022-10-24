# Bear Anki sync

This yet another implementation of a script to sync notes to Anki. I created this script for my personal use, but plan to improve it over time. If you have any questions, please open an issue.

## How to use

1. Copy this repo and open terminal from the folder
2. Install AnkiConnect plugin, if you haven't done that already
3. Open AnkiConnect settings: Tools > Addons > Choose addon and press Config. Copy values `webBindAddress` and `webBindPort`
4. Paste those values into main.py ANKI_CONNECT variable: `http://webBindAddress:webBindPort`
5. Find the folder containing the bear database and set the full path in BEAR_DB_PATH varible
6. Install pipenv on your system (I am assuming you already have python isntalled): `brew install pipenv` or `pip install pipenv`
7. Install script dependencies: `pipenv install`
8. Run the script: `pipenv run sync`
 
## Features

1. You can define multiline flashcards with #flashcard tag and with a text paragraph
```markdown
Front #flashcard
Multiline
Back
Flashcard

This line won't be captured
```
2. The script also supports Rem oneline flashcard definitions: ` Front :: Back`
