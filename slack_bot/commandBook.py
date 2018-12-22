# -*- coding: utf-8 -*-
import random
import pandas as pd
import datetime
import time

from urllib import parse
import urllib
from bs4 import BeautifulSoup
from slackclient import SlackClient

from util import OUTPUT, FOOD_DATA, LOCLOG, IMAGEDF, IMAGEPATH, PATH
from visualize_weight_change import plotAndMakeURL
from pickWithWeightV2 import pick_main

TOKEN = "xoxb-506472500310-508628858594-dsjEuTj023eLFktctRFjeKZw"
slack_client = SlackClient(TOKEN)

#command Books
def _crawl_food_best(text, user):
   data = pd.read_csv(LOCLOG)
   if user in data["id_code"].values:
       index = data[data["id_code"]==user].index[0]
       location = data.loc[index,"location"]
   else:
       location = "강남역"
   food = text
   query = location + ' ' + food
   url = 'https://www.diningcode.com/list.php?query=' + parse.quote(query)
   soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
   region = []
   menu = []
   address = []
   href = []
   loca = []
   keywords = []
   for i in soup.find_all("ul",class_="list"):
       for j in i.find_all("span",class_="btxt"):
           region.append(j.get_text())
       for j in i.find_all("span",class_="stxt"):
           menu.append(j.get_text())
       for j in i.find_all("span",class_="ctxt"):
           address.append(j.get_text())
           for k in j.find_all("i",class_="loca"):
               loca.append(k.get_text())
       for j in i.find_all("li"):
           href.append('https://www.diningcode.com' + j.find("a")["href"])

   for i in range(0,len(loca)):
       address[2*i+3] = address[2*i+3][len(loca[i]):]

   for i in range(1,len(region)):
       keywords.append(region[i]+'\n'+menu[i]+'\n'+address[2*i+1]+'\n'+href[i]+'\n')
   keywords= keywords[:3]
#   print(keywords)
   # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
   return u'\n'.join(keywords), location

def dice():
    ran_num = random.randint(1,100)
    return ran_num

def food(user, channel):
    get_food = pick_main(user)
    imageDF = pd.read_excel(IMAGEDF)
    foodfile = imageDF[imageDF["food"]==get_food]["name"].values[0] + ".jpg"
    foodlink = IMAGEPATH + foodfile
    start = time.time()
    slack_client.api_call('files.upload', channels=channel, filename=foodfile, file=open(foodlink, 'rb'))
    image_call_time = round(time.time()-start,3)
    text_format = "Image loading time: {} seconds".format(image_call_time)
    slack_client.api_call("chat.postMessage", channel=channel, text=text_format)
    response = "추천 음식은 {} 입니다.\n Yes or No를 입력해주세요.".format(get_food)
    return response    

def yes(user):
    log = pd.read_excel(OUTPUT)
    timeDiff = datetime.datetime.now()- log.loc[log.index[-1],["time"]].values[0]
    if timeDiff.seconds <= 120:
        log.set_value(log.index[-1],"choice",1)
        log.to_excel(OUTPUT, index=None)
        food_data = pd.read_excel(FOOD_DATA)
        food_id = log.loc[log.index[-1],["food_id"]].values[0]
        food = food_data["food"][food_id-1]
        result, location = _crawl_food_best(food, user)
        response = "Yes로 기록했습니다.\n\n{} 지역의 {} 맛집입니다.\n\n".format(location,food)
        response += result
    else:
        response = "응답이 너무 늦었습니다."    
    return response

def no(user, channel):
    log = pd.read_excel(OUTPUT)
    timeDiff = datetime.datetime.now()- log.loc[log.index[-1],["time"]].values[0]
    if timeDiff.seconds <= 120:
        log.set_value(log.index[-1],"choice",0)
        log.to_excel(OUTPUT, index=None)
        get_food = pick_main(user)
        imageDF = pd.read_excel(IMAGEDF)
        foodfile = imageDF[imageDF["food"]==get_food]["name"].values[0] + ".jpg"
        foodlink = IMAGEPATH + foodfile
        start = time.time()
        slack_client.api_call('files.upload', channels=channel, filename=foodfile, file=open(foodlink, 'rb'))
        image_call_time = round(time.time()-start,3)
        text_format = "Image loading time: {} seconds".format(image_call_time)
        slack_client.api_call("chat.postMessage", channel=channel, text=text_format)
        response = "No로 기록했습니다.\n 다음 추천 음식은: {} 입니다.".format(get_food)
    else:
        response = "응답이 너무 늦었습니다."  
    return response

def guide():
    text = """1. !food: 음식 하나를 추천해줍니다. 
2. !yes: !food 입력 후 이 음식이 마음에 들 경우, 근처 맛집을 검색할 수 있습니다.
3. !no: !food 입력 후 이 음식이 마음에 안 들 경우, 다음 음식을 추천 받을 수 있습니다.
4. !food_list: 명령어를 통해 전체 음식 리스트를 출력할 수 있습니다.
5. !location 위치: 명령어를 통해 검색할 지역을 지정할 수 있습니다. default는 강남역입니다. 
ex). !location 신촌역
6. !visualize: 음식의 선택 기준을 데이터 입력 갯수에 따라 시각화합니다.
7. !evaluation: 평가표를 출력합니다.
처음 이 서비스를 이용하는 경우, 10번동안 무작위 랜덤 추출로 음식을 추천해줍니다.
이후부터 음식 선호도 결과를 반영해 음식을 추천해줍니다."""
    return text

def food_list():
    data = pd.read_excel(FOOD_DATA)
    text = ""
    count = 1
    for i in data["food"].values:
        text+= str(count) + ": " + i +"\n"
        count+=1  
    return text

def set_loc(user, location):
    data = pd.read_csv(LOCLOG)
    if user in data["id_code"].values:
        index = data[data["id_code"]==user].index[0]
        original = data.loc[index,"location"]
        data.set_value(index,"location",location)
        data.to_csv(LOCLOG, index=None)
        text = "사용자의 위치를 {}에서 {}로 변경했습니다.".format(original, location)
    else:
        original = "강남역"
        data = data.append({"id_code":user, "location": location}, ignore_index= True)
        data.to_csv(LOCLOG, index=None)
        text = "사용자의 위치를 {}에서 {}로 변경했습니다.".format(original, location)
    return text

def visualize(user):
    url = plotAndMakeURL(user)
    return url

def evaluation(channel):
    evaluationfile = PATH+"images\\evalutaion.png"
    slack_client.api_call('files.upload', channels=channel, filename="evaluation", file=open(evaluationfile, 'rb'))
    