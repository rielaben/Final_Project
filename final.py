import json
import unittest
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import sqlite3

client_id = "m8K0vXjoUNXwMo4AfkpZnw"
API_KEY = "U-Y8QD3RL11wbcrmj9w3Yt3i_vFz97mdYqynngNtmGCFGZpmcdFRkGrMMztgvFwtvo7YR9JHpIkJk_pxr8qy9J9CGorVcWj0ac5poi4yMXWbliWoTxpgyIyIol-zX3Yx"
headers = {'Authorization': 'Bearer %s' % API_KEY}
base_url = "https://api.yelp.com/v3"

import requests
from pprint import pprint

# locationUrlFromLatLong = "https://developers.zomato.com/api/v2.1/cities?lat=28&lon=77"
# header = {"User-agent": "curl/7.43.0", "Accept": "application/json", "user_key": API_KEY}
# response = requests.get(locationUrlFromLatLong, headers=header)
# pprint(response.json())


# search = BASE_URL + "/search?entity_id=280&entity_type=city&count=4&sort=rating"
# header = {"User-agent": "curl/7.43.0", "Accept": "application/json", "user_key": API_KEY}
# r = requests.get(search, headers=header)
# response = r.json()
# pprint(response)
# name_restaurant = response["restaurants"][0][]
def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def city_restaurant_data(city_name, term_name):
    url = base_url + "/businesses/search"
    params = {'term': term_name, 'location': city_name, 'limit': 25, 'sort_by': 'rating'}
    req = requests.get(url, params=params, headers=headers, timeout=100)
    info = json.loads(req.text)
    return info
    
def table_set_up(data, conn, cur, city_name):
    cur.execute(f'CREATE TABLE IF NOT EXISTS {city_name}')
    restaurant_list = data['businesses']
    for restaurant in restaurant_list:
        id_num = restaurant['id']
        name = restaurant['name']
        rating = restaurant['rating']
        longitude = restaurant['coordinates']['longitude']
        latitude = restaurant['coordinates']['latitude']
        type_of_food = restaurant['categories'][0]['title']
        cur.execute(f'INSERT INTO {city_name} (id_num, name, food_type, rating, longitude, latitude) VALUES ({id_num}, {name}, {type_of_food}, {rating}, {longitude}, {latitude})')
    conn.commit()

def wiki_data():
    soup = BeautifulSoup(requests.get('https://en.wikipedia.org/wiki/List_of_North_American_metropolitan_areas_by_population').text, 'html.parser')

    table = soup.find("table",{"class":"wikitable sortable"})
    body = table.find('tbody')
    table_rows = body.find_all('tr')
    d = []

    for tr in table_rows:
        td = tr.find_all('td')
        row = [tp.text.strip() for tp in td]
        d.append(row)   
            
    df = pd.DataFrame(d) 
    df = df[[1, 2, 3]]
    df.head()

    h = []
    header_cols = table.find_all('th')
    for col in header_cols:
        results_str = col.text.strip()
        split = results_str.split('\n')
        h.append(split[0])  
    
    df.columns = h[1:]
    df = df.iloc[1:]

    is_us = df['Country'] == 'United States'
    us_cities = df[is_us]
    list_of_cities = us_cities['Metropolitan area'].to_list()

    return list_of_cities

def main():
    cur, conn = setUpDatabase('final_db.db')
    #cities = wiki_data()
    #print(cities)
    table_set_up(city_restaurant_data("New York City", "restaurant"), conn, cur, "New York City")

#average income of cities compared to price of most popular restaurant in that city
#income of area in NYC compared to most popular restaurant (by rating) for that area
#major 5 cities incomes compared to 20 most popular restaurants for that city
#table for cities- name, income, population
#table for restaurants- name, location, rating, price
#database- city name, restaurant name, income, population, restaurant rating, price of restaurant
#comparing the top rated restaurants in the most popular cities to see if the neighborhood's income is related to the rating and price of the modt popular restaurants
#our data will either support this claim or we will be surprised by the results
#calculate average rating per area and see which city has the highest rating on average
#can switch to yelp

if __name__ == "__main__":
    main()
    #unittest.main(verbosity=2)