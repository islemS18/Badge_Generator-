# Badge Generator

A Python application that automatically generates printable event badges from an Excel spreadsheet and participant photos then exports the result as an HTML page

## Features

- Read participant information from an Excel file
- Automatically match participant photos
- Generate printable badges
- Export badges as an HTML page
- Fast and customizable workflow

## Technologies
Python 3
HTML
CSS

## Librairies
Pandas
Jinja2
argparse (Python Standard Library)
pathlib (Python Standard Library)
base64 (Python Standard Library)
os 

## Running

python badge_generator.py participants.xlsx photos --output badges.html