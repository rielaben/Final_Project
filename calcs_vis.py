import unittest
import sqlite3
import json
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from numpy import percentile
import csv

def setUpDatabase(db_name):
    '''This function takes in the name of the database and creates a connection and cursor to it.
    It returns the cursor and connection.'''

    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def calculation(cur):
    '''This function takes in the cursor for finalData1 as input. Uses SQL SELECT...FROM...JOIN 
    statement to find where temperature that results from joining the WeatherData and Temperature
     tables together. This list of temperatures is extracted with the fetchall() command. The uses 
     SELECT statement to extract a list of the happiness rating scores from the HappyData table. 
     Then performs a SELECT statement to extract a list of average precipitation figures from the 
     WeatherData table. Finally, extracts a list of city names using a SELECT statement to extract 
     city names from the HappyData table. Returns a tuple of lists for temperature, happiness scores,
    precipitation, and city names.'''

    cur.execute('SELECT temperature FROM WeatherData JOIN Temperatures ON Temperatures.id = WeatherData.average_temperature_id')
    temperatures = cur.fetchall()
    cur.execute('SELECT total_score FROM HappyData')
    happy_scores = cur.fetchall()
    cur.execute('SELECT average_precipitation FROM WeatherData')
    precip = cur.fetchall()
    cur.execute('SELECT city FROM HappyData')
    city_names = cur.fetchall()
    return temperatures, happy_scores, precip, city_names

def write_csv(x, y, names_city, file_name, headers):
    '''This function takes in x and y axis data as lists, a list of city names, the csv file to 
    write to, and the headers to include at the top of the csv file. Writes to the csv file all of the
    information passed in from the x data, y data and city lists and does not return anything.'''

    file = open(file_name, mode='w', newline='', encoding="utf8")
    writer = csv.writer(file, delimiter=',')
    writer.writerow(headers)
    for i in range(len(x)):
        writer.writerow([names_city[i], x[i], y[i]])
    file.close() 

def visualization1(temp, happy, city_names):
    '''This function takes in a list of temperatures, a list of happiness scores, and a list of city 
    names as inputs. Calls the write_csv function to write to the csv the data from these lists, and 
    then plots the data on a matplotlib plot. The figure is saved as ‘v1.png’ and does not return 
    anything.'''

    x = []
    y = []
    names_city = []
    for i in temp:
        x.append(i[0])
    for i in happy:
        y.append(i[0])
    for i in city_names:
        names_city.append(i[0])

    write_csv(x, y, names_city, "tempHappy.csv", ['City', 'Temperature', 'Happiness Score'])
    fig, ax = plt.subplots()
    ax.scatter(x, y, color='#32db84')
    ax.set_xlabel('temperature in degrees Celcius')
    ax.set_ylabel('total happiness score')
    ax.set_title('Happiness Scores vs. Average Temperatures for Different US Cities')
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r-")
    r = np.corrcoef(x, y)
    print("correlation coefficient for temperature and happiness scatterplot: " + str(r[0,1]))

    s1 = sorted(x)
    s2 = sorted(y)
    avg1 = (s1[0] + s1[-1]) / 2
    avg2 = (s2[0] + s2[-1]) / 2
    plt.axvline(avg1)
    plt.axhline(avg2)
    fig.savefig('tempHappyScatterplot.png')
    plt.show()

def visualization2(precip, happy, city_names):
    '''This function takes in a list of precipitation data, a list of happiness scores, and a list of
     city names as inputs. Calls the write_csv function to write to the csv the data from these lists,
      and then plots the data on a matplotlib plot. The figure is saved as ‘v2.png’ and does not return anything.'''

    x = []
    y = []
    names_city = []
    for i in precip:
        x.append(i[0])
    for i in happy:
        y.append(i[0])
    for i in city_names:
        names_city.append(i[0])

    write_csv(x, y, names_city, "precipHappy.csv", ['City', 'Precipitation', 'Happiness Score'])

    fig, ax = plt.subplots()
    ax.scatter(x, y, color='#7303fc')
    ax.set_xlabel('precipitation in mm')
    ax.set_ylabel('total happiness score')
    ax.set_title('Happiness Scores vs. Precipitation for Different US Cities')
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r-")
    r = np.corrcoef(x, y)
    print("correlation coefficient for precipitation and happiness scatterplot: " + str(r[0,1]))

    s1 = sorted(x)
    s2 = sorted(y)
    avg1 = (s1[0] + s1[-1]) / 2
    avg2 = (s2[0] + s2[-1]) / 2
    plt.axvline(avg1)
    plt.axhline(avg2)

    fig.savefig('precipHappyScatterplot.png')
    plt.show()

def box_and_wiskers(data, x_label, fig_name, title, csv_name):
    '''This function takes in a list of the data of interest we want to plot, the x_label for the plot, 
    the name of the figure, title, and the name of the csv file that is desired to save the data into.
     Creates a box-and-wiskers plot, which includes the quartiles for the data and the iqr as well. It
      then writes to the csv file the Min, q1, Median, Q3, Max, and IQR data for the data passed into 
      the the function. The function returns nothing.'''

    good_data = []
    for i in data:
        good_data.append(i[0])
    fig1, ax1 = plt.subplots()

    ax1.set_title(title)
    ax1.set_xlabel(x_label)

    plt.boxplot(good_data, vert=False)
    fig1.savefig(fig_name)   
    plt.show()

    quartiles = percentile(good_data, [25, 50, 75]).tolist()
    data_min, data_max = min(good_data), max(good_data)

    iqr = stats.iqr(good_data, interpolation='midpoint')

    file = open(csv_name, mode='w', newline='', encoding="utf8")
    writer = csv.writer(file, delimiter=',')
    writer.writerow(['Min', 'Q1', 'Median', 'Q3', 'Max', 'IQR'])
    writer.writerow([data_min, quartiles[0], quartiles[1], quartiles[2], data_max, iqr])
    file.close()


def main():
    '''The main() function akes in no inputs. It calls the calculations function to return data for 
    temperature, happiness scores, precipitation, and city names, and uses these to call the 
    visualization1() and visualization2() functions. Finally, the box_and_wiskers() function is called
     on precipitation, temperatures and happiness scores individually so we can see the box-and-whiskers
      plots for each of these lists of data. Main()returns nothing.'''

    cur, conn = setUpDatabase('finalProjectDatabase.db')
    temperatures, happy_scores, precipitation, city_names = calculation(cur)
    visualization1(temperatures, happy_scores, city_names)
    visualization2(precipitation, happy_scores, city_names)
    box_and_wiskers(precipitation, 'Precipitation (mm)', 'precipBoxplot.png', 'Boxplot Precipitation', 'precip.csv')
    box_and_wiskers(temperatures, 'Temperature (Deg. Celcius)', 'tempBoxplot.png', 'Boxplot Temperature', 'temp.csv')
    box_and_wiskers(happy_scores, 'Happiness Scores', 'happyBoxplot.png', 'Boxplot Happiness Scores', 'happy.csv')

    


if __name__ == "__main__":
    main()