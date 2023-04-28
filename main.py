from tkinter import *
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.animation as animation
import numpy as np
import requests
import mysql.connector
from datetime import date

current_date = date.today()
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="water_tank2"
)

root = Tk()
root.title('Panel użytkownika')
# icon = PhotoImage(file='G:\Workspace\PythonProjects\Automatyka\Automatyka2\logo.jpg')
# root.iconphoto(False, icon)
root.geometry("410x650")

my_label = Label(root, text="Wprowadź wymagane informacje", font=("Helvetica", 20))
my_label.grid(row=0, column=1)

# Create Slide Function
user_window = Label(root, text="Pojemność zbiornika")
user_window.grid(row=2, column=1)
tank_capacity_field = Entry(root, width=20)  # pojemnosc_zbiornika
tank_capacity_field.grid(row=3, column=1, pady=20)

user_window = Label(root, text="Minimalny poziom wody w zbiorniku")
user_window.grid(row=4, column=1)
minimum_water_level_field = Entry(root, width=20)
minimum_water_level_field.grid(row=5, column=1, pady=20)

user_window = Label(root, text="Dzienne zużycie wody")
user_window.grid(row=6, column=1)
daily_water_consumption_field = Entry(root, width=20)  # dzienne_zuzycie_wody
daily_water_consumption_field.grid(row=7, column=1, pady=20)

user_window = Label(root, text="Powierzchnia dachu")
user_window.grid(row=8, column=1)
roof_surface_field = Entry(root, width=20)  # powierzchnia_dachu
roof_surface_field.grid(row=9, column=1, pady=20)

user_window = Label(root, text="Miejscowość")
user_window.grid(row=10, column=1)
city_field = Entry(root, width=20)
city_field.grid(row=11, column=1, pady=20)

# Create a label
slide_label = Label(root, text='')
slide_label.grid(row=1, column=1, pady=20)


# Open new Window
def new_window():
    tank_capacity = int(tank_capacity_field.get())  # wprowadzane_przez_uzytkownika
    minimum_water_level = int(minimum_water_level_field.get())  # wprowadzane_przez_uzytkownika
    daily_water_consumption = int(daily_water_consumption_field.get())  # wartość podana przez użytkownika
    roof_surface = int(roof_surface_field.get())  # wartość podana przez użytkownika
    location = city_field.get()  # wartość podana przez użytkownika

    # Dane potrzebne do rysowania wykresów
    water_amount_in_tank = []
    radius = 1  # Promień zbiornika na potrzeby wykresu
    bottom = 0  # Wartość początkowa / minimalna wody w zbiorniku NIE ZMIENIAĆ NAZWY ZMIENNEJ
    width_ratio = 1  # Necessary for the horizontal axis
    interval = 0.04  # Time interval
    t0 = 0  # startujemy symulację o 0 (s)
    t_end = 720  # symulacja kończy się po 720sekundach
    frame_amount = int(t_end / interval)  # Frame amount of the simulation
    t = np.arange(t0, t_end + interval, interval)  # Time vector
    density_water = 1000  # [kg/m^3] gęstość cieczy (wody)
    kp1 = 1000  # prędkość napełniania zbiornika ????
    tank_liter_scale = tank_capacity / 10  # podziałka na zbiorniku (co ile litrów)

    # Założenia dotyczące zbiornika na wodę
    maximum_water_level = tank_capacity * 95 / 100  # zakładamy, że w zbiorniku maksymalnie może być 95% jego pojemności

    # Pobieranie poziomu wody w zbiorniku na dzień dzisiejszy
    mycursor = db.cursor(buffered=True)
    select_query = "SELECT water_amount FROM water_balance WHERE date = date(now());"
    mycursor.execute(select_query)
    current_day_water_level = []

    result = mycursor.fetchone()
    if result is not None:
        for i in result:
            current_day_water_level.append(i)

    # Wyliczane wartości
    water_level = 0
    saved_water = 0
    pumped_up_water = 0
    initial_water_level = 0

    # Jeśli w bazie istnieje wpis z poziomem wody na dzień dzisiejszy, pobieramy i ustawiamy jako stan początkowy wody w zbiorniku
    if current_day_water_level and current_day_water_level[0] != 0 and current_day_water_level[0] is not None:
        initial_water_level = current_day_water_level[0]

    # Wartość początkowa wody w zbiorniku @TODO pobierać z bazy jeśli null to 0 wpw ustawiać na odpowiednią wartość
    final_water_amount = []  # @TODO zapisywać do bazy
    saved_water_amount = []  # @TODO zapisywać do bazy
    pumped_up_water_amount = []  # @TODO zapisywać do bazy
    pumped_out_water_amount = []  # @TODO zapisywać do bazy

    # Zbiornik
    vol_r1 = np.zeros(len(t))  # 0 vector for storing reference volume values
    volume_tank1 = np.zeros(len(t))  # 0 vector for true volume values
    volume_tank1[0] = initial_water_level  # Insert the initial true volume as the initial element of the vector
    error1 = np.zeros(len(t))  # Create a 0 vector to store errors in the simulation
    m_dot1 = kp1 * error1  # Compute a 0 vector to store massflow control inputs

    # Pobieranie ilości opadów na 30 dni od dnia dzisiejszego
    # API_KEY - XNM3CL9GNL543APCQ9RUTV8Z5
    # API_KEY#2 - WBGD4FB23FTPVH9NGQGV2QMSX
    complete_api_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/" + location + "/next30days?unitGroup=metric&include=days&key=WBGD4FB23FTPVH9NGQGV2QMSX&contentType=json"
    api_link = requests.get(complete_api_url)
    api_data = api_link.json()

    print("Weather status for city - {}".format(location))
    rainfall_data = []

    for i in range(30):
        date = api_data['days'][i]['datetime'] #@TODO usunąć na końcu
        preciptype = api_data['days'][i]['preciptype']

        if preciptype is None or 'rain' not in preciptype:
            # print("There will be no rainfall on {}".format(date)) #@TODO usunąć na końcu
            rainfall_data.insert(i + 1, 0)
        else:
            daily_rainfall = api_data['days'][i]['precip']
            # print("Rainfall for {0} will measure {1} mm per square meter".format(date, daily_rainfall)) #@TODO usunąć na końcu
            rainfall_data.insert(i + 1, daily_rainfall)

    # Uzupełniamy powyższe tablice o to jak zmienia się poziom wody w zbiorniku,
    # ile wody możemy zaoszczędzić, ile wody należy dopompować z niezależnego źródła
    x = 0
    for i in range(61):
        if i == 0:  # pierwsze uruchomienie aplikacji
            if current_day_water_level and current_day_water_level[0] != 0:# and current_day_water_level[0] is not None:
                water_level = current_day_water_level[0]  # uzupełniamy zbiornik z wodą do minimum
                water_amount_in_tank.append(water_level)
            else:
                water_level = minimum_water_level
                water_amount_in_tank.append(water_level)
                # print(water_level) #@TODO usunąć na końcu
                # print(database_water_level[0]) #@TODO usunąć na końcu

        # water_level = minimum_water_level  # uzupełniamy zbiornik z wodą do minimum
        # water_amount_in_tank.append(water_level)  # zapisujemy poziom wody w zbiorniku

        mycursor = db.cursor(buffered=True)

        # Wstawiamy do bazy wpis z pierwszego uzupełnienia zbiornika, gdyż API zwraca dane od dnia następnego
        query = "INSERT INTO water_balance (date, water_amount, rainfall_amount, daily_consumption, saved_water, pumped_up_water, pumped_out_water)" \
                "SELECT * FROM (SELECT %s AS day, %s AS water_amount, %s AS rainfall_amount, %s AS daily_consumption, %s AS saved_water, %s AS pumped_up_water, %s AS pumped_out_water ) AS temp " \
                "WHERE NOT EXISTS (" \
                "SELECT date FROM water_balance WHERE date = day" \
                ") LIMIT 1;"
        water_balance = (current_date, minimum_water_level, 0, 0, 0, minimum_water_level, 0)
        mycursor.execute(query, water_balance)
        db.commit()

        if i % 2 == 1:
            water_level -= daily_water_consumption  # pobieramy wodę ze zbiornika
            water_amount_in_tank.append(water_level)  # zapisujemy stan wody w zbiorniku po pobraniu wody

        if i % 2 == 0 and i != 0:  # i != 0 musi być żeby wykluczyć pierwsze odpalenie aplikacji
            saved_water = rainfall_data[x] * roof_surface  # ile litrów wody pozyskaliśmy z deszczówki
            saved_water_amount.append(saved_water)  # zapisujemy ile wody zaoszczędziliśmy tego dnia
            water_level += saved_water  # dodajemy deszczówkę do zbiornika

            if water_level < minimum_water_level:  # sprawdzamy, czy deszczówka wystarczyła, żeby osiągnąć poziom minimalny
                pumped_up_water = minimum_water_level - water_level  # obliczamy ile wody trzeba dopompować do stanu minimum
                pumped_up_water_amount.append(pumped_up_water)  # zapisujemy ile wody musieliśmy dociągnąć z rurociągu
                water_level += pumped_up_water  # dociągamy brakującą wodę do zbiornika
                water_amount_in_tank.append(water_level)  # zapisujemy poziom wody w zbiorniku
                pumped_out_water_amount.append(0)
                final_water_amount.append(water_level)  # zapisujemy ile wody mamy na koniec dnia

            elif water_level > maximum_water_level: #sprawdzamy czy poziom wody nie przekroczy poziomu maksymalnego w zbiorniku
                water_to_pumped_out = water_level - maximum_water_level #wyliczamy ile wody trzeba wypompować ze zbiornika, żeby się zmieściła
                water_level -= water_to_pumped_out
                water_amount_in_tank.append(water_level)
                pumped_out_water_amount.append(water_to_pumped_out)
                pumped_up_water_amount.append(0)  # poziom wody w zbiorniku był za duży więc nie dopompowywaliśmy
                final_water_amount.append(water_level)  # zapisujemy ile wody mamy na koniec dnia

            else:
                water_amount_in_tank.append(water_level)  # zapisujemy poziom wody w zbiorniku jeśli poziom wody > minimum
                pumped_up_water_amount.append(0)
                pumped_out_water_amount.append(0)
                final_water_amount.append(water_level)  # zapisujemy ile wody mamy na koniec dnia

            x += 1

    # zapisujemy dane przechowywane w tablicy do bazy
    for i in range(30):
        date = api_data['days'][i]['datetime']

        mycursor = db.cursor(buffered=True)

        # Wstawianie bez duplikatów
        query = "INSERT INTO water_balance (date, water_amount, rainfall_amount, daily_consumption, saved_water, pumped_up_water, pumped_out_water)" \
                "SELECT * FROM (" \
                "SELECT %s AS day, %s AS water_amount," \
                "%s AS rainfall_amount, %s AS daily_consumption," \
                "%s AS saved_water, %s AS pumped_up_water," \
                "%s AS pumped_out_water " \
                ") AS temp " \
                "WHERE NOT EXISTS (" \
                "SELECT date FROM water_balance WHERE date = day" \
                ") LIMIT 1;"

        water_balance = [(
                date,
                final_water_amount[i],
                rainfall_data[i],
                daily_water_consumption,
                saved_water_amount[i],
                pumped_up_water_amount[i],
                pumped_out_water_amount[i]
            )]

        mycursor.executemany(query, water_balance)
        db.commit()

    # aktualizujemy dane przy kolejnych uruchomieniach aplikacji
    database_rainfall_data = []
    mycursor = db.cursor(buffered=True)

    #pobieramy dane o opadach z bazy
    mycursor.execute(
        "SELECT rainfall_amount FROM water_balance WHERE date BETWEEN date(now()) AND date(now() + INTERVAL 30 day);")

    # pobieramy dane o opadach z bazy do tablicy
    for i in range(30):
        result = mycursor.fetchone()
        for x in result:
            database_rainfall_data.append(x)

    # sprawdzamy czy dane się zmieniły, jeśli tak to aktualizujemy wpisy w bazie
    has_data_changed = False
    for i in range(30):
        date = api_data['days'][i]['datetime']

        # Sprawdzamy czy nastąpiła jakaś zmiana w ilości przewidywanych opadów
        if rainfall_data[i] != database_rainfall_data[i]:
            has_data_changed = True

        # jeśli nastapiła zmiana aktualizujemy dane w bazie
        if has_data_changed:
            update_cursor = db.cursor(buffered=True)
            query = "UPDATE water_balance SET water_amount=%s, rainfall_amount=%s, saved_water=%s, pumped_up_water=%s, pumped_out_water=%s WHERE date=%s"

            new_water_balance = (
                final_water_amount[i],
                rainfall_data[i],
                saved_water_amount[i],
                pumped_up_water_amount[i],
                pumped_out_water_amount[i],
                date
            )

            update_cursor.execute(query, new_water_balance)
            db.commit()

    # Rysujemy wykresy
    y = 0
    z = 0
    for i in range(1, len(t)):  # Iterate throughout the simulation (i goes from 1 till the length of the time vector, last element not counted, if len(t)=1251, then you go till 1250)
        y += 1

        if y == 600:
            y = 0

        if y == 299:
            z += 1

        if y == 599:
            z += 1

        if y < 300:
            vol_r1[i] = water_amount_in_tank[z]
        else:
            vol_r1[i] = water_amount_in_tank[z]

        # Compute the errors between the reference values and the true values for tanks 1, 2, 3
        error1[i - 1] = vol_r1[i - 1] - volume_tank1[i - 1]  # potrzebne do rysowania

        # Compute the control inputs for all the tanks
        m_dot1[i] = kp1 * error1[i - 1]  # potrzebne do rysowania

        # Compute the true tank volumes in the next time step through this numerical integration (trapezoidal rule)
        volume_tank1[i] = volume_tank1[i - 1] + (m_dot1[i - 1] + m_dot1[i]) / (2 * density_water) * interval  # to też potrzebne do rysowania

    # Start the animation
    vol_r1_2 = vol_r1

    def update_plot(num):
        if num >= len(volume_tank1):
            num = len(volume_tank1) - 1

        initial_drawing_value = 63
        final_drawing_value = initial_drawing_value * tank_capacity / 100

        tank_12.set_data([0, 0], [final_drawing_value * (-1), volume_tank1[num] - final_drawing_value])  # a to ustawia poziom wody w zbiorniku
        tnk_1.set_data(t[0:num], volume_tank1[0:num])  # to rysuje dolny wykres
        vol_r1.set_data([-radius * width_ratio, radius * width_ratio], [vol_r1_2[num], vol_r1_2[num]])  # to chyba czerwoną linię w zbiorniku xd
        vol_r1_line.set_data([t0, t_end], [vol_r1_2[num], vol_r1_2[num]])  # to nie wiem, chyba ustawia czerwoną linię na dolnym wykresie?

        return vol_r1, tank_12, vol_r1_line, tnk_1  # to nie wiem ale odpowiada za animację

    # Set up your figure properties20
    figure = plt.figure(figsize=(12, 8))  # tu ustawia się rozmiar okna, tak jak rozdzielczość np. 16x9 ale można dowolnie
    grid_spec = gridspec.GridSpec(2, 3)

    # Create object for Tank1
    ax0 = figure.add_subplot(grid_spec[0, 0])
    vol_r1, = ax0.plot([], [], 'r', linewidth=2)  # to wiadomo czerwona linia w zbiorniku
    tank_12, = ax0.plot([], [], 'royalblue', linewidth=255, zorder=0)  # to też nie ogarniam, coś z poziomem wody w zbiorniku
    plt.xlim(-radius * width_ratio, radius * width_ratio)  # to nie wiem co robi, wygląda jak niepotrzebne
    plt.xticks(np.arange(-radius, radius + 1, radius))
    plt.yticks(np.arange(bottom, tank_capacity + tank_liter_scale, tank_liter_scale))  # to nie wiem co robi chyba ustawia podziałkę na osy y na zbiorniku
    plt.ylabel('Liczba litrów w zbiorniku')
    plt.title('Zbiornik na wodę')

    x = [0, 721]
    # Create volume function
    ax3 = figure.add_subplot(grid_spec[1, :])
    vol_r1_line, = ax3.plot([], [], 'r', linewidth=2)  # r - czerwony kolor linii, linewidth - grubość czerwonej lini na dolnym wykresie
    tnk_1, = ax3.plot([], [], 'blue', linewidth=4, label='Poziom wody w zbiorniku')  # linewidth - grubość lini na dolnym wykresie
    plt.xticks(np.arange(min(x), max(x), 24.0))  # to pozwala na zdefiniowanie przedziału czasowego na osi X (co 24h)
    plt.ylim(0, tank_capacity)  # podziałka (osi y) na dolnym wykresie
    plt.ylabel('Liczba litrów wody w zbiorniku')  # opis osi y dolnego wykresu
    plt.grid(True)  # "szachownica" na dolnym wykresie
    plt.legend(loc='upper right', fontsize='small')  # legenda na dolnym wykresie w prawym górnym rogu

    plane_ani = animation.FuncAnimation(figure, update_plot, frames=frame_amount, interval=0, repeat=False, blit=True)  # interval - prędkość wykresu
    plt.show()


# Create new window butoon
new_window = Button(root, text="Uruchom", command=new_window)
new_window.grid(row=13, column=1, pady=2)

root.mainloop()
