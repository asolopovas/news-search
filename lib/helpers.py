import datetime
import hashlib
import pickle
import shutil
import sys
import numpy
import re
import pandas as pd
import requests
import os
import tempfile

from charset_normalizer import from_bytes
from htmldate import find_date
from dateutil.parser import parse
from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse
from deep_translator import GoogleTranslator
from json import JSONEncoder
from newspaper import Article

dir_tmp = tempfile.gettempdir()
dir_exec = os.getcwd()
# create cache dir in tmp
dir_cache = os.path.join(dir_tmp, "google_news_cache")
if not os.path.exists(dir_cache):
    os.mkdir(dir_cache)


def downloadArticle(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            "title": article.title,
            "text": article.text,
            "publish_date": article.publish_date,
            "authors": article.authors,
            "tob_image": article.top_image,
            "src_url": article.source_url,
            "keywords": article.keywords,
            "meta_keywords": article.meta_keywords,
            "tags": article.tags,
            "meta_description": article.meta_description,
            "meta_lang": article.meta_lang,
            "summary": article.summary,
            "html": article.html,
            "article_html": article.article_html,
            "canonical_link": article.canonical_link,
            "images": article.images,
            "movies": article.movies,
            "top_image": article.top_image,
        }
    except:
        return None


def getArticle(url):
    urlHash = getHash(url)

    return cacheObject(urlHash, lambda: downloadArticle(url))


def clearCache():
    if os.path.exists(dir_cache):
        shutil.rmtree(dir_cache)
    print("Cache cleared")
    sys.exit(0)


def cleanStr(s):
    s = ''.join([i if ord(i) < 128 else ' ' for i in s])
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def cacheStr(key, cb):

    keyPath = os.path.join(dir_cache, key)
    if os.path.exists(keyPath):
        try:
            return open(keyPath, "r", encoding="utf-8").read()
        except Exception as error:
            print(f"An error occurred: {error}")
            print(f"cachStr fn reading {keyPath} {cb()}")

    data = cb()
    if data is None:
        return None

    with open(keyPath, "wt", encoding="utf-8") as file:
        file.write(data)
    return data


def cacheObject(key, cb):
    if not os.path.exists(dir_cache):
        os.mkdir(dir_cache)
    keyPath = os.path.join(dir_cache, key)
    if os.path.exists(keyPath):
        return pickleDeserialize(keyPath)
    data = cb()
    if data is not None:
        return pickleSerialize(keyPath, cb())
    return None


def parseDate(date_string, output_format="%Y-%m-%d"):
    try:
        parsed_date = parse(date_string)
        return parsed_date.strftime(output_format)
    except ValueError:
        return False


def encodeForExcelLink(s):
    if s is None:
        return ""
    s = s.strip()
    s = s.replace("\"", "\"&CHAR(34)&\"")
    s = re.sub(r'\s+', ' ', s)
    return s


def getHash(string):
    hash_object = hashlib.sha256()
    hash_object.update(string.encode())
    hex_digest = hash_object.hexdigest()
    return hex_digest


def pickleSerialize(file_path, data):
    try:
        with open(file_path, "wb") as file:
            pickle.dump(data, file)
        return data
    except Exception as e:
        print(f"Error saving file: {e}")


def pickleDeserialize(file_path):
    try:
        with open(file_path, "rb") as file:
            data = pickle.load(file)
        return data
    except Exception as e:
        print(f"Error loading file: {e}")


def makeExcelFile(data, output_file, debug=False):
    # Create a DataFrame based on the input data type
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    elif isinstance(data, list):
        df = pd.DataFrame(data[1:], columns=data[0])
    else:
        raise ValueError("Invalid columns_data format")

    df.to_excel(output_file, index=False, engine='openpyxl')
    if debug:
        df.to_csv(output_file.replace(".xlsx", ".csv"), index=False)


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def getFinalUrl(url):
    try:
        response = requests.get("https://" + url,  cookies={'CONSENT': 'YES+'})
        if response.history:
            return response.url
    except:
        return url


def translate(text, source, target="en"):
    translated = GoogleTranslator(source, target).translate(text)
    return translated


def urlToLink(url, title="LINK"):
    return f'=HYPERLINK("{unquote(url)}", "{title}")'


def translateUrl(url, lang):
    parsed_url = urlparse(url)
    extra_query = {
        "_x_tr_sl": lang,
        "_x_tr_tl": "en",
        "_x_tr_hl": "en-US",
        "_x_tr_pto": "wapp"
    }
    url_query = parse_qs(parsed_url.query)
    url_query.update(extra_query)
    url_query = {k: v[0] if len(v) == 1 else v for k, v in url_query.items()}
    url_parts = list(parsed_url)
    url_parts[1] = url_parts[1].replace(
        "-", "--").replace(".", "-") + ".translate.goog"
    url_parts[4] = urlencode(url_query)
    return urlunparse(url_parts)


def getDate(url):
    try:
        date = find_date(url)
        results = from_bytes(date.encode('utf-8'))
        best_guess = results.best()
        return str(best_guess)
    except:
        None


def dateFormat(date):
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime("%B %d, %Y at %H:%M")
    except:
        return ''
