import argparse
import datetime
import os
import inspect
import sys

from urllib.parse import unquote
from lib.google_news import GoogleNews
from lib.helpers import cacheObject, cacheStr, cleanStr, clearCache, encodeForExcelLink, getFinalUrl, getHash, makeExcelFile, parseDate, translate, translateUrl, urlToLink, getArticle, getDate


dir_exec = os.getcwd()
dir_script = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        print(hasattr(self.__class__, 'query'))
        sys.stderr.write('\nError: {}\n'.format(message))
        sys.exit(2)


def processNews(results, lang="en"):
    print("Processing Results...")
    data = []
    idx = 0
    if not results is None:
        for result in results:
            title = result['title']
            date = result['datetime']
            link = result['link']
            resultHash = getHash(''.join([title, link]))

            if lang != "en":
                titleHash = getHash(resultHash.join('title'))
                title = cacheStr(getHash(titleHash),
                                 lambda: cleanStr(translate(title, lang)))

            linkHash = getHash(resultHash.join('link'))
            link = cacheStr(linkHash, lambda: getFinalUrl(unquote(link)))

            if date is None:
                article = getArticle(link)
                if article is not None and article['publish_date'] is not None:
                    date = article['publish_date']
                    date = date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date = cacheStr(
                        getHash(resultHash.join('date')), lambda: getDate(link))

            link = translateUrl(link, lang)
            idx = idx + 1
            nr = str(idx).zfill(3)
            print(
                f"{nr} --------------------------- \n Processing: {title} \n Date: {date}")
            data.append([date, urlToLink(link,  encodeForExcelLink(title))])

        return data


def getNews(query, start_date, end_date, lang, encode="utf-8"):
    print("Searching for query: \"" + query + "\" from " +
          start_date + " to " + end_date + " in " + lang)
    cacheKey = getHash(''.join([query, start_date, end_date, lang, encode]))
    googlenews = GoogleNews()
    googlenews.set_lang(lang)
    googlenews.set_time_range(start_date, end_date)
    googlenews.set_encode(encode)
    googlenews.get_news(query)
    return cacheObject(cacheKey, lambda: googlenews.results())


yesterday = (datetime.datetime.now() -
             datetime.timedelta(1)).strftime("%d/%m/%Y")
today = datetime.datetime.now().strftime("%d/%m/%Y")
args_list = [
    {"name": "query", "type": str, "help": "Query to search for",
        "default": False, "nargs": "?"},
    {"name": "-s", "dest": "start_date", "type": str, "default": yesterday,
     "help": "Date from which to start the search"},
    {"name": "-e", "dest": "end_date", "type": str, "default": today,
     "help": "Date before which to end the search"},
    {"name": "--clear-cache", "action": "store_true", "default": False,
     "help": "Clear search cache"},
    {"name": "-l", "dest": "lang", "type": str, "default": "en",
     "help": "Select language to search in"},
    {"name": "--debug", "action": "store_true", "default": False, "help": "Debug mode"},
]

if __name__ == "__main__":
    parser = CustomArgumentParser(
        description='Search Google News and export to Excel File')
    _ = [parser.add_argument(arg.pop("name"), **arg) for arg in args_list]

    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code == 2:
            sys.exit(0)

    if args.clear_cache:
        clearCache()

    if not args.clear_cache and not args.query:
        parser.error(
            "At least one of the following arguments must be provided: --clear-cache, query")

    startDate = parseDate(args.start_date)
    endDate = parseDate(args.end_date)

    suffixStart = parseDate(startDate, "%Y-%m-%d")
    suffixEnd = parseDate(endDate, "%Y-%m-%d")
    suffix = f"{suffixStart} to {suffixEnd}"

    if not startDate or not endDate:
        print("Invalid date format: please use something like 01/01/2020 or 01-01-2020")
        exit()
    newsRawData = getNews(args.query, startDate, endDate, args.lang)

    headings = [["Date", "Title"]]
    if newsRawData is not None:
        data = headings + processNews(newsRawData, args.lang)

        makeExcelFile(data, os.path.join(
            dir_exec, f"results - {args.query} - {suffix}.xlsx"), args.debug)
    else:
        print("No results found")
