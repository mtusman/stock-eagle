import os
import re
import requests
import bs4
import smtplib
import networkx as nx
import json
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from newspaper import Article
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
from math import log
from datetime import datetime 
from dateutil.relativedelta import relativedelta
from dateutil.rrule import *


def getArticle(tick, hourspast):
    orig_list = []
    # Words to look for in a headline.
    words = ['up', 'down', 'failing', 'successs', 'stock', 'slide', 'report', 'buy', 'sell', 'dividend', 'report', '%', 'movers', 'rating', 'rallying']
    # Defines a regex to extract the a href tag of an artice
    linkRegex = re.compile(r'class="nuEeue hzdq5d ME7ew" href="(.*)" jsname="(.*)">')

    url = requests.get('https://news.google.com/news/search/section/q/{}/{}?hl=en-GB&ned=uk'.format(tick, tick))
    soup = bs4.BeautifulSoup(url.text)

    '''Google news is broken into so called 'cards'. Different cards
    have different number of articles'''
    cards = soup.select('.lPV2Xe')
    for card in cards:
        articles = card.select('.M1Uqc')
        for article in articles: 
            temp_dict = {}
            temp_dict['date'] = article.select('.d5kXP')[0].getText()
            # Skips over articles that are were posted 24 hours ago
            if not temp_dict['date'].endswith('ago'):
                continue
            # Skips over articles that are past the hourspast specified 
            if "h ago" in temp_dict['date']:
                if int(temp_dict['date'].replace("h ago", "").strip()) > hourspast:
                    continue
            temp_dict['url'] = linkRegex.search(str(article.select('.nuEeue')[0])).group(1)
            temp_dict['name'] = article.select('.nuEeue')[0].getText()
            temp_dict['point'] = 0
            for word in words:
                if word in temp_dict['name'].lower() or word in temp_dict['url'].lower():
                    temp_dict['point'] += 1
            temp_dict['source'] = article.select('.IH8C7b')[0].getText()
            orig_list.append(temp_dict) 

    sorted_list_by_points = sorted(orig_list, key=lambda article: article['point'])[::-1]
    return orig_list

'''Summarises the articles'''
def sentence(text):
    '''Break the text into sentences'''
    return sent_tokenize(text)

def dedupe(items):
    '''Removes repeated word in a node - a sentence '''
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen

def similarity(c1, c2):
    '''stop words are words like "it" and "the" , that have no massive impact on the 
    sentence'''
    stop_words = list(stopwords.words("english"))
    # Removes stop words in both sentences
    c1_cleaned = [x for x in word_tokenize(c1) if x not in stop_words]
    c2_cleaned = [x for x in word_tokenize(c2) if x not in stop_words]
    c1_words = Counter(dedupe(c1_cleaned))
    c2_words = Counter(dedupe(c2_cleaned))
    total_words = c1_words + c2_words
    similarity_between_words = 0
    for key, val in total_words.items():
        ''' Looks at whether the two articles share a word'''
        if total_words[key] > 1:
            similarity_between_words += 1

    return similarity_between_words / (log(len(c1_words)) + log(len(c2_words)))


def connect(nodes):
    ''' Measures the amound of similirity between each sentece '''
    return [(start, end, similarity(start, end)) for start in nodes for end in nodes if start is not end]

def rank(nodes, edges):
    ''' Creates the graph with the calculates nodes (sentences) and their weight'''
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_weighted_edges_from(edges)
    ''' Uses google's pagerank formula to find the most important senteces'''
    return nx.pagerank(graph)

def summarize(text):
    nodes = sentence(text)
    edges = connect(nodes)
    scores = rank(nodes, edges)
    ''' Sorts the array according to their weight '''
    important_nodes = sorted(scores, key= lambda k: scores[k])[:6]
    return " ".join(important_nodes)

''' Anaylsis each article for each ticker'''
def analyse(tick, hourspast):
    articles = getArticle(tick, hourspast)
    summary = []
    for article in articles:
        article_analysis = Article(article['url'])
        try:
            article_analysis.download()
            article_analysis.parse()
            # article_analysis.nlp()
            article['summary'] = summarize(article_analysis.text)
            summary.append(article)
        except: 
            article['summary'] = "Failed"
    return summary

def get_last_trading_date():
    now = datetime.now()
    # if the weekday is saturday or sunday then it get's last friday's date
    if now.weekday() == 5 or 6:
        last_friday = now + relativedelta(weekday=FR(-1))
        date = datetime.strftime(last_friday, "%Y-%m-%d'")
        return date
    else:
        yesterday = now - relativedelta(days=1)
        date = datetime.strftime(yesterday, "%Y-%m-%d'")
        return date

def stats(tick):
    data = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ex Dividend', 'Split Ratio']
    ticker = {}
    date = get_last_trading_date()
    url = "https://www.quandl.com/api/v3/datasets/WIKI/{}.json?".format(tick)
    params = {
        'start_date': date, 
        'end_date': date
    }
    resp = requests.get(url, data=params).json()
    for index, value in enumerate(data):
        ticker[value] = resp['dataset']['data'][0][index]
    return ticker

def get_stock(symbol):
    last_year_date = datetime.strftime(datetime.now() - relativedelta(years=1), "%Y-%m-%d")
    date = get_last_trading_date()
    url = requests.get('https://www.quandl.com/api/v3/datasets/WIKI/{}.json?start_date={}&end_date={}'.format(symbol, last_year_date, date))
    json_dataset = url.json()
    json_data = json_dataset['dataset']['data']
    dates = []  
    closing = []
    for day in json_data:
        dates.append(datetime.strptime(day[0], "%Y-%m-%d"))
        closing.append(day[4])
    plt.plot_date(dates, closing, '-')
    plt.title(symbol)
    plt.xlabel('Date')
    plt.ylable('Stock Price')
    plt.savefig('foo.png')


def sendMailer(tick, _from, to, password):
    msg = MIMEMultipart()
    msg['Subject'] = tick
    msg['From'] = _from
    msg['To'] = to
    
    get_stock(tick)
    msgText = MIMEText('<center><br><img src="cid:image"><br></center>', 'html')
    msg.attach(msgText)

    # Encode's the image
    image = open('foo.png', 'rb')
    msgImage = MIMEImage(image.read())
    msgImage.add_header('Content-ID', '<image>')
    msg.attach(msgImage)
    image.close() 

    stats_dict = stats(tick)
    stats_html = '''
    <h3 style="text-align:center;">{}</h3>
    <table style="margin:0 auto;">
        <col width="130">
    '''.format(tick)
    for key, value in stats_dict.items():
        stats_html += "<tr><td>" + str(key).capitalize() + "</td><td>" + str(value) + "</td></tr>"
    stats_html += '''
    </table>
    '''
    msg.attach(MIMEText(stats_html, 'html'))

    articles_list = analyse(tick, 24)
    article_html = ''
    for index, article in enumerate(articles_list, 1):
        article_html += '''

        <div class="articles">
         <h4>{} :<a href="{}">{}</a></h4> 
        <p>Published {} by {}</p>
        <p><span style="font-weight:bold;">Summary: </span>{}</p>
        </div>
        '''.format(index, article['url'], article['name'], article['date'], article['source'], article['summary'])

    msg.attach(MIMEText(article_html, 'html'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(_from, password)
    server.sendmail(_from, to, msg.as_string())
    server.quit()

def main(tickers, _from, to, password):
    for tick in tickers:
        sendMailer(tick, _from, to, password)
