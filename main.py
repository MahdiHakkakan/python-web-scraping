from bs4 import BeautifulSoup as bS
import requests as re
from re import findall
from mysql.connector import connect
from time import sleep
from sklearn import preprocessing, linear_model
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

user = input("USERNAME: ")
password = input("PASSWORD: ")
host = input("HOST_IP: ")
database = input("DATABASE: ")
page_number = int(input("How many page do you want to search: "))
user_car_name = [input("The Car You Want Made by: ").capitalize()]
user_car_model = [input("The Car Model is: ").capitalize()]
user_cars_exterior_color = [input("It\'s Exterior Color is: ").capitalize()]
user_cars_interior_color = [input("And It\'s Interior Color is: ").capitalize()]
user_cars_age = int(input("The Car Made in(year): "))
user_cars_mileage = int(input("And It's mileage: "))
user_cars_accident = int(input("Had accident(1 is True and 0 is False): "))

# Let's go to web scrapping
cars = []
page = 1
while page != (page_number + 1):
    url = f"https://www.truecar.com/used-cars-for-sale/listings/price-above-1/?page={page}"
    response = re.get(url)
    html = response.text
    soup = bS(html, "html.parser")
    cars.append(soup)
    page += 1
    # print(response.ok)
    sleep(5)

cars_age = []
cars_price = []
cars_name = []
cars_model = []
cars_mileage = []
cars_accidents = []
cars_exterior_color = []
cars_interior_color = []
for car in cars:
    cars_age.append(car.find_all("span", attrs={"class": "vehicle-card-year text-xs"}))
    cars_name.append(car.find_all("span", attrs={"class": "truncate"}))
    cars_model.append(car.find_all("span", attrs={"class": "truncate"}))
    cars_price.append(car.find_all("div", attrs={"data-test": "vehicleCardPricingBlockPrice"}))
    cars_mileage.append(car.find_all("div", attrs={"data-test": "vehicleMileage"}))
    cars_accidents.append(car.find_all("div", attrs={"data-test": "vehicleCardCondition"}))
    cars_exterior_color.append(car.find_all("div", attrs={"data-test": "vehicleCardColors"}))
    cars_interior_color.append(car.find_all("div", attrs={"data-test": "vehicleCardColors"}))
# print("✅ 1 successful")
age = []
price = []
name = []
model = []
mileage = []
accident = []
exterior_color = []
interior_color = []
for page in range(page_number):
    age.extend(findall(r'>(\S*)<', str(cars_age[page])))
    price.extend(findall(r'\$(\S*)<', str(cars_price[page])))
    name.extend(findall(r"\"truncate\">(\S*)<", str(cars_name[page])))
    model.extend(findall(r"<!-- --> <!-- -->(\S*.\w*.\S*)</span>", str(cars_model[page])))
    mileage.extend(findall(r"/svg>(\S*)<", str(cars_mileage[page])))
    accident.extend(findall(r"/svg>(\S* \w*)", str(cars_accidents[page])))
    exterior_color.extend(findall(r"/svg>(\S*)<", str(cars_exterior_color[page])))
    interior_color.extend(findall(r"<!-- -->(\S*)<!", str(cars_interior_color[page])))

# print("✅ 2 successful")

# print(price)
accidents = list(map(lambda element: 0 if "No" in element else 1, accident))
ages = list(map(lambda age_number: int(age_number), age))
prices = list(map(lambda price_number: int(price_number.replace(",", "")), price))
mileages = list(map(lambda mileage_number: int(mileage_number.replace(",", "")), mileage))
model = list(map(lambda model_name: model_name.replace(" <!-- -->", ""), model))
# print("✅ 3 successful")

connection = connect(user=user, password=password,
                     host=host,
                     database=database)

# print("✅ 4 successful")

cursor = connection.cursor()
cursor.execute("DELETE FROM cars;")
for i in range(len(name)):
    car_name = name[i]
    car_model = model[i]
    car_age = ages[i]
    car_exterior_colors = exterior_color[i]
    car_interior_colors = interior_color[i]
    car_mileage = mileages[i]
    car_accident = accidents[i]
    car_price = prices[i]
    cursor.execute("INSERT INTO cars VALUES (\"%s\", \"%s\", %i, \"%s\", \"%s\", %i, %i, %i)" % (car_name,
                                                                                                 car_model,
                                                                                                 car_age,
                                                                                                 car_exterior_colors,
                                                                                                 car_interior_colors,
                                                                                                 car_mileage,
                                                                                                 car_accident,
                                                                                                 car_price))
connection.commit()

# print("✅ 5 successful")

connection.close()

# print("✅ 6 successful")


# Let's go to ML

connection = connect(user=user,
                     password=password,
                     host=host,
                     database=database)
myCursor = connection.cursor()


def encode_database_info(element, number, user_input):
    myCursor.execute("SELECT %s FROM cars;" % element)
    element_list = [myCursor_fetch[0] for myCursor_fetch in myCursor.fetchall()]
    element_encode = preprocessing.LabelEncoder()
    element_encode.fit(element_list)
    if number == 1:
        element_encoded = element_encode.transform(user_input)
    else:
        element_encoded = element_encode.transform(element_list)
    return element_encoded


def convert_to_np_array(element):
    myCursor.execute("SELECT %s FROM cars;" % element)
    element_fetch = myCursor.fetchall()
    element_list = [element_fetch_index[0] for element_fetch_index in element_fetch]
    element_array = np.array(element_list, dtype=float)
    return element_array


d = {"cars_name": encode_database_info("car_name", 0, ""),
     "cars_model": encode_database_info("car_model", 0, ""),
     "cars_exterior_color": encode_database_info("car_exterior_color", 0, ""),
     "cars_interior_color": encode_database_info("car_interior_color", 0, ""),
     "cars_age": convert_to_np_array("car_age"),
     "cars_mileage": convert_to_np_array("car_mileage"),
     "cars_accident": convert_to_np_array("car_accident"),
     "cars_price": convert_to_np_array("car_price")}

df = pd.DataFrame(data=d)


all_info = ['cars_name', 'cars_model', 'cars_exterior_color',
            'cars_interior_color', 'cars_age', "cars_mileage", "cars_accident", "cars_price"]

cdf = df[all_info]
msk = np.random.rand(len(df)) < 0.8
train = cdf[msk]
test = cdf[~msk]

variable = ['cars_name', 'cars_model', 'cars_exterior_color',
            'cars_interior_color', 'cars_age', "cars_mileage", "cars_accident"]


regression = linear_model.LinearRegression()
X = np.asarray(train[variable])
Y = np.asarray(train[["cars_price"]])
regression.fit(X, Y)

y_hat = regression.predict(test[variable])
x = np.asarray(test[variable])
y = np.asarray(test["cars_price"])
# print("Residual sum of squares: %.2f"
#       % np.mean((y_hat - y) ** 2))
# print('Variance score: %.2f' % regression.score(x, y))
user_car_name_encoded = encode_database_info("car_name", 1, user_car_name)
user_car_model_encoded = encode_database_info("car_model", 1, user_car_model)
user_car_exterior_color_encoded = encode_database_info("car_exterior_color", 1, user_cars_exterior_color)
user_car_interior_color_encoded = encode_database_info("car_interior_color", 1, user_cars_interior_color)

x_predict = [[user_car_name_encoded[0],
              user_car_model_encoded[0],
              user_car_exterior_color_encoded[0],
              user_car_interior_color_encoded[0],
              user_cars_age,
              user_cars_mileage,
              user_cars_accident]]
y_predict = regression.predict(x_predict)
print(np.round(y_predict[0][0]), "$")
connection.close()
