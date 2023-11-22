import requests
from bs4 import BeautifulSoup
import json
from time import sleep
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

DB = os.getenv("DB")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
TABLE = os.getenv("TABLE")
COLUMN = os.getenv("COLUMN")


def clouds(data):
    try:
        data = data.find('img', class_='label_icon label_small screen_icon')
        data = str(data['src'])

        if data.find("sun.png") != -1:
            cloud="0"
        elif data.find("sunc.png") != -1:
            cloud="1"
        elif data.find("suncl.png") != -1:
            cloud="2"
        elif data.find("dull.png") != -1:
            cloud="3"
        else:
            cloud="0"
    except:
        cloud="0"
    # ясно - 0
    # sun.png

    # малооблачно - 1
    # sunc.png
    
    # облачно - 2 
    # suncl.png

    # пасмурно - 3
    # dull.png
    return cloud

def downfalls(data):
    try:
        data = data.find('img', class_='label_icon label_small screen_icon')

        if data:
            data = str(data['src'])
            if data.find("rain.png") != -1:
                downfall = "1"
            elif data.find("snow.png") != -1:
                downfall = "2"
            elif data.find("storm.png") != -1:
                downfall = "3"
            else:
                downfall = "0"
        else:
            downfall = "0"
    except:
        downfall = "0"
    #  пусто - 0
    #  
    # дождь - 1
    # rain.png
    
    # снег - 2
    # snow.png

    # гроза - 3
    # storm.png
    return downfall

def winds(data):
    try:
        data = data.get_text()
        data = data.split()
        match data[0]:
            case "С":
                direction = '0'
            case "СВ":
                direction = '1'
            case "В":
                direction = '2'    
            case "ЮВ":
                direction = '3'
            case "Ю":
                direction = '4'
            case "ЮЗ":
                direction = '5'
            case "З":
                direction = '6'
            case "СЗ":
                direction = '7'
            case "":
                direction = "0"
        speed = data[1].replace('м/с', '')

        wind = {'direction': direction, 'speed': speed}
    except:
        wind = {'direction': '0', 'speed': '0'}
    # "0" - северный
    # "1" - северо-восточный
    # "2" - восточный
    # "3" - юго-восточный
    # "4" - южный
    # "5" - юго-западный
    # "6" - западный
    # "7" - северо-западный
    return wind

def temps(data):
    try:
        string = data.get_text()
        numberString = ""
        for later in string:
            if later.isdigit():
                numberString= numberString+ later
        
        if numberString == "":
            numberString = 0

        temp = int(numberString) + 273
        # 0 °C + 273 = 273 K
    except:
        temp = 273
    return temp

def dbInit():
    connection = psycopg2.connect(
        dbname=DB,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    cursor = connection.cursor()

    create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({} TEXT);").format(
        sql.Identifier(TABLE),
        sql.Identifier(COLUMN)
    )

    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()
    connection.close()

    return

def dbSend(data):
    data = str(data)
    connection = psycopg2.connect(
        dbname=DB,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    cursor = connection.cursor()
    insert_data_query = sql.SQL("INSERT INTO {} ({}) VALUES (%s);").format(
        sql.Identifier(TABLE),
        sql.Identifier(COLUMN)
    )

    cursor.execute(insert_data_query, (data,))
    connection.commit()
    cursor.close()
    connection.close()
    return

def parser(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = []

        rows = soup.find_all('tr')
        del rows[0]
        del rows[0]
        
        for row in rows:
            cells = row.find_all('td')

            data = {
                "region": url.split("/")[-4],

                "year": url.split("/")[-3],
                "mounth": url.split("/")[-2],
                "day": cells[0].get_text(),

                "temperatureDay": temps(cells[1]),
                "presherDay": cells[2].get_text(),
                "cloudDay": clouds(cells[3]),
                "downfallDay": downfalls(cells[4]),
                "windDayDirection": winds(cells[5])["direction"],
                "windDaySpeed": winds(cells[5])["speed"],

                "temperatureNight": temps(cells[6]),
                "presherNight": cells[7].get_text(),
                "cloudNight": clouds(cells[8]),
                "downfallNight": downfalls(cells[9]),
                "windNightDirection": winds(cells[10])["direction"],
                "windNightSpeed": winds(cells[10])["speed"],
            }
            
            dbSend(data)
            print("//__//__//__//__")
            print(data)
            sleep(3)


    else:
        print(f"Error: Status code {response.status_code}")




def main():

    dbInit()

    data = {"year":"2015", "mounth":"11"}
    urlO = "https://www.gismeteo.ru/diary/4079/"


    yearO = int(data["year"])
    mounth = int(data["mounth"])
    
    r = 2024 - yearO
    for y in range(r):
        year = y + yearO
        while mounth <= 12:
            url = urlO + str(year) + "/" + str(mounth) + "/"

            parser(url)

            mounth += 1
        else:
            mounth = 1
    return 


main()