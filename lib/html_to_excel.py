import os
import pandas as pd
import argparse
import requests
from urllib.parse import urlparse, unquote, urlencode, parse_qs, urlunparse
from htmldate import find_date
from bs4 import BeautifulSoup


columns = ['heading', 'url', 'datetime', 'url_original']


def extractData(filename, output="output.xlsx"):
    if os.path.exists(output):
        os.remove(output)

    with open(filename, 'r', encoding='utf-8') as f:
        htmlStr = f.read()
    soup = BeautifulSoup(htmlStr, 'html.parser')
    divs = soup.find_all('div', {"class": "article"})
    data = []
    for div in divs:
        child = div.find('div', {'role': 'heading'})

        try:
            href = div.find('a')['href']
        except:
            href = None

        if child is not None:
            heading = child.text.strip().replace('\n', ' ')
            heading = ' '.join(heading.split())
            if heading in [x[0] for x in data]:
                continue
            data.append([heading, href, None, href])

    df = pd.DataFrame(data, columns=columns, index=None)
    df.to_excel(output, index=False)

def extract_datetime(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        datetime_string = soup.find('time')['datetime']
        datetime_obj = pd.to_datetime(datetime_string).tz_localize(None)
        return datetime_obj
    except:
        try:
           return find_date(url, outputformat="%Y-%m-%d %H:%M")
        except:
            return None


def get_soup(target_url):
    response = requests.get(target_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup



def list_languages_with_target(target):
    results = translate_client.get_languages(target_language=target)
    for language in results:
        print(u"{name} ({language})".format(**language))


def updateData(filename, output="output.xlsx"):
    df = pd.read_excel('output.xlsx')
    df['datetime'] = df['url'].apply(extract_datetime)
    df['url'] = df['url'].apply(translate_url)
    df['url_original'] = df['url_original'].apply(translate_url_original)
    df['heading'] = df['heading'].apply(translate_heading)
    os.remove(output)
    df.to_excel(output, index=False)


# add arguments to the script
parser = argparse.ArgumentParser(
    description='Extract Google News from HTML files to Excel')
parser.add_argument('-i', '--input',  type=str,
                    default="index.html",  help='Input file path')
parser.add_argument('-o', '--output',  type=str,
                    default="index.xlsx", help='Output file path')
args = parser.parse_args()

input_file = args.input
output_file = args.output

extractData(input_file)
updateData(output_file)
