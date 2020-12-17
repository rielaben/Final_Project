import json
import os
import requests
import sqlite3
from bs4 import BeautifulSoup
import calcs_vis

location_lat_long_api_key = "MQosMrFCrMn14jS6h32hinuTQWrHDd5q"
weather_api_key = "IYyo8JaZe0W8MznnblAr2cRPpDeeTQGa"


def create_connection(database):
    '''This function takes in the name of the database. It makes a 
    connection to the cursor using the name of the database given. 
    It returns the connection variable and cursor variable to allow 
    access into the database.'''
    conn = sqlite3.connect(database)
    cur = conn.cursor()
    return cur, conn

def lat_long_table(cur, conn, lat, long, place):
    '''This function takes in the cursor, connection, latitude,
    longitude, and name for a specific city. It creates a Latitude/Longitude
    table in the database and inserts the city, latitude, and longitude. It returns
    nothing. '''
    cur.execute('CREATE TABLE IF NOT EXISTS LatLongData (city_name INTEGER, latitude INTEGER, longitude INTEGER)')
    cur.execute('INSERT INTO LatLongData (city_name, latitude, longitude) VALUES (?,?,?)', (place, lat, long))

def get_weather_data(cur, conn, location):
    '''This function takes in the cursor, connection, and city name. 
    First request the geocoding API and include the city name in the request.
    Use json to extract the latitude and longitude from this. Then call the lat_long_table function to
    create the latitude/longitude table. Now, call the weather API in order to get a json file of the 
    weather information per month. Add each month's data to a dictionary (key = month number, value = tuple of temperature and 
    precipitation for that month). Return that dictionary. '''
  
    mapquest_url = f"http://open.mapquestapi.com/geocoding/v1/address?key={location_lat_long_api_key}&location={location}" 
    req2 = requests.get(mapquest_url)
    lat_long_info = json.loads(req2.text)
   
    #below gets dictionary of just the lat and long for the city
    results = lat_long_info['results'][0]['locations'][0]['latLng']
    #below are the lat and long strings
    lat_str = results['lat']
    long_str = results['lng']
    lat_long_table(cur, conn, lat_str, long_str, location)

    #the "weather_info" json object should return monthly weather data given the lat and long as imputs
    weather_data = {}
    
    url_weather = f"https://api.meteostat.net/v2/point/climate?lat={lat_str}&lon={long_str}&alt=58&x-api-key={weather_api_key}"
    req = requests.get(url_weather)
    weather_info = json.loads(req.text)

    data_json = weather_info['data']
    for month in data_json:
        #gets month of interest, 1 = Jan, 2 = Feb, 3 = March, etc.
        month_num_string = month['month']
        temp_string_celcius = month['tavg']
        percip = month['prcp']
  
        weather_data[month_num_string] = (temp_string_celcius, percip) #, pressure, sunshine
  
    return weather_data
    

def weather_table(data, cur, conn, location, temp_list):
    '''This function takes in a dictionary of the weather data, the cursor, connection, city name, and list of already seen temperature value
    in the data dictionary. This creates a table for the Weather Data and then gets the temperature and precipitation from the data dictionary
    for each month. It takes the average of these 12 months and inserts the id for the temperature into the table and the value for
    precipitation into the table along with the city name (location). If a new temperature value was found it adds it to the temp_list
    and creates a new id in the Temperatures table. Otherwise, it uses an existing id from that table to describe the avergae temperature
    for the current location being used. It commits to the database and returns nothing.'''

    cur.execute(f'CREATE TABLE IF NOT EXISTS WeatherData (location TEXT, average_temperature_id INTEGER, average_precipitation INTEGER)') 
    temp = 0
    percip = 0
  
    for key in data:
        temp += int(data[key][0])
        percip += int(data[key][1])
 
    avg_temp = temp / 12
    avg_percip = percip / 12
    avg_temp = round(avg_temp, 2)
    avg_percip = round(avg_percip, 2)

    final_temp = 0
    if (avg_temp in temp_list) == False:
        temp_list.append(avg_temp)
        final_temp = temp_list.index(avg_temp)
        cur.execute('INSERT INTO Temperatures (temperature, id) VALUES (?,?)', (avg_temp, final_temp))
    else:
        final_temp = temp_list.index(avg_temp)

    cur.execute(f'INSERT INTO WeatherData (location, average_temperature_id, average_precipitation) VALUES (?,?,?)', (location, final_temp, avg_percip)) 
    conn.commit()

def website_prep():
    '''This function takes in no paramters. It preps the website data to be extracted easily later. It makes a request using the
    happiest places to live url and then uses beautiful soup to find the table that we will extract data from in a later function.
    It returns a list of all of the values within the table.''' 

    url = 'https://wallethub.com/edu/happiest-places-to-live/32619'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table",{"class":"cardhub-edu-table center-aligned sortable"})

    body = table.find("tbody")
    row_tags = body.find_all("tr")
    return row_tags


def get_website_data(i, row_tags):
    '''This function takes in the index for the current city being looked at and the row_tags data list of the table information from the
    website that was found in the website_prep function. It looks at the specific row (i) in the list (row_tags) to find the overall rank,
    city name, total happiness score, emotional/physical score, income/employment score, and community/environment score. It then add these 6 values to a list and 
    returns that list. '''

    tr_tag = row_tags[i]
    td_tags = tr_tag.find_all("td")
    overall_rank = int(td_tags[0].text.strip())
    city_name = td_tags[1].text.strip()

    total_score = float(td_tags[2].text.strip())
    emotional_and_pysical_score = int(td_tags[3].text.strip())
    income_and_employment_score = int(td_tags[4].text.strip())
    community_and_enviornment_score = int(td_tags[5].text.strip())
    row = [overall_rank, city_name, total_score, emotional_and_pysical_score, income_and_employment_score, community_and_enviornment_score]
    return row
    

def website_table(data, cur, conn):
    '''This function takes in the list of data (the 6 values) from the website, the cursor, and connection. It creates a table for the website
    data (HappyData) if one does not already exist. It then inserts the data into each column of the table. It commits the values to the
    database and returns nothing. '''

    cur.execute('CREATE TABLE IF NOT EXISTS HappyData (overall_rank INTEGER, city TEXT, total_score INTEGER, well_being_rank INTEGER, income_employment_rank INTEGER, community_environment_rank INTEGER)')
    cur.execute('INSERT INTO HappyData (overall_rank, city, total_score, well_being_rank, income_employment_rank, community_environment_rank)  VALUES (?,?,?,?,?,?)', (data[0], data[1], data[2], data[3], data[4], data[5]))
    conn.commit()

def get_start_index(cur, conn):
    '''This function takes in the cursor and connection. This function finds where to start gathering data from in the next round of 
    data extraction. It creates the HappyData table if it does not exist already. It then finds all of the 
    cities in the table currently. If that length is 0, then it returns 0 (we are in the first round of data extraction from the API/webstie.
    If it is between 1 and 181, then we return the next value to be extracted (if we ended at 25 extractions, we return 26 to start at the next
    one). If we are out of this range, then we are done collecting data and return -1.'''

    cur.execute('CREATE TABLE IF NOT EXISTS HappyData (overall_rank INTEGER, city TEXT, total_score INTEGER, well_being_rank INTEGER, income_employment_rank INTEGER, community_environment_rank INTEGER)')
    cur.execute('SELECT city FROM HappyData')
    x = cur.fetchall()
    if len(x) >= 1 and len(x) < 182:
        return len(x)
    elif len(x) > 181: #181 is last
        return -1
    else:
        return 0
    

def get_temp_lists(cur):
    '''This function takes in the cursor. It creates the Temperatures table if it does not already exist and selects the temperature values from it.
    It then adds them all to a list and returns that list. This is meant to be used for figuring out the id of temperatures that will
    be extracted from the API and added to the WeatherData table. '''

    cur.execute('CREATE TABLE IF NOT EXISTS Temperatures (temperature INTEGER, id INTEGER)')
    cur.execute('SELECT temperature FROM Temperatures')
    x = cur.fetchall()
    t = []
    for i in x:
        t.append(i)
    return t

def main():
    '''The main function takes in no parameters. It calls the create_connection function on the database name being used. It then creates start and
    stop variables to make sure we don't extract more than 25 things from the APIs and website. Then it calls website_prep and get_temps_list. 
    Then, it does a while loop that continues until around 25 things have been added to the tables. In the loop, we call get_start_index to 
    get the starting point for data extraction. We make sure if it is -1, we do the calculations (see other python file) and then end the running
    of the code. Then, we call get_website_data, get_weather_data, weather_table, and website_table to get the data and add it to the database.
    Then we add one to our starting value for counting how many times we have done a data extraction, and we loop again. This
    function returns nothing. '''

    cur, conn = create_connection("finalProjectDatabase.db")

    start = 1
    stop = 25
    row_tags = website_prep()
    temp_list = get_temp_lists(cur)

    while start < stop:
        current_index = get_start_index(cur, conn)
        if current_index == -1:
            calcs_vis.main()
            cur.close()
            break

        location = get_website_data(current_index, row_tags) #list of current location's data from website table
        weather_data = get_weather_data(cur, conn, location[1])
        weather_table(weather_data, cur, conn, location[1], temp_list)
        website_table(location, cur, conn) 
       
        start += 1


if __name__ == "__main__":
    main()