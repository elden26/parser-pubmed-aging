#Парсер статей из пабмеда по теме "старение"

from bs4 import BeautifulSoup
import requests 
import time 
from fake_useragent import UserAgent
import psycopg2

#создаем таблицу в БД postgreSQL куда будем сохранять информацию
#подключаем БД через докер контейнер
DB_CONFIG = {
    "dbname": "<NAME OF YOUR DATABASE>",    
    "user": "<USERNAME>",         
    "password": "<PASSWORD>",
    "host": "localhost",
    "port": "5432"
}

conn = psycopg2.connect(**DB_CONFIG) 
cursor = conn.cursor()
print("Успешное подключение к PostgreSQL!")

#создаем таблицу в базе данных, сохраняем туда название статьи, год публикации, ссылку и краткое описание
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Aging_publications_pubmed (
        Title TEXT,
        Year INTEGER,
        Link TEXT,
        Description TEXT
    );
""")
conn.commit() 
print('БД создана')

#меняем headers чтобы избежать блокировки парсинга
one_time_agent = UserAgent() 
random_user_agent = one_time_agent.random
headers = {'UserAgent' : random_user_agent}

#собираем URL для парсинга
base_url = "https://pubmed.ncbi.nlm.nih.gov"  

for page_num in range(1, 2): 
    url = (              
        f'{base_url}'
        f'?term=aging'
        f'&page={page_num}')

    print(f'Parsing in process, page {page_num}...')
    print()

    #загружаем HHTP, используем сгенерированный заголовок
    response = requests.get(url, headers=headers) 
    #проверяем была ли загрузка успешной (HTTP код 200), если нет - вывод сообщения об ошибке 
    if response.status_code != 200: 
        print(f'Error request on page {page_num}')
        continue 
    print('HTTP загружен')
    
    #непосредственно парсинг с Beautifulsoup
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select('article')
    for article in articles:
        title = article.select_one('.docsum-title')
        year = article.select_one('.docsum-journal-citation.short-journal-citation').text[-5:-1]
        link = 'https://pubmed.ncbi.nlm.nih.gov' + article.select_one('a').get('href')
        abstract = article.select_one('.full-view-snippet')
        print('добавлям данные в таблицу')
        cursor.execute(
            "INSERT INTO Aging_publications_pubmed (Title, Year, Link, Description) VALUES (%s, %s, %s, %s);",
            (title.text.strip(), int(year), link, abstract.text.strip()))
        conn.commit()

time.sleep(2) #временная задержка чтобы избежать блокировки парсинга

print('Информация сохранена в базе данных. Вывести на экран? y/n')
if input() == 'y':
    cursor.execute("SELECT Title, Year, Link, Description FROM Aging_publications_pubmed;")
    rows = cursor.fetchall()  
    for row in rows:
        print(f'Title: {row[0]}\nYear: {row[1]}\n'
              f'Link: {row[2]}\nDescription:\n{row[3]}')
        print()
    
cursor.close()
conn.close()
print('Работа с базой данных завершена')

