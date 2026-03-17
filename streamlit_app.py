import streamlit as st
import json
import pandas as pd
from datetime import datetime
from collections import Counter


st.title("Probability: Luck Vs Statistics")
st.markdown("Analiză statistică exploratorie asupra extragerilor.")

st.sidebar.header("🔎 Filtrare date")

@st.cache_data
def load_data():
    """
        LOAD DATA-NUMBERS from the defined file
    """
    with open("./data/loto_numbers.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------------- #

def parse_date(date_str):
    return datetime.strptime(date_str, "%d.%m.%Y")

def filter_data(year = None, month = None):
    """
        FILTER the DATA extracted based on year and/or month, and return result
    """
    result = {}
    for date, draws in data.items():
        dt = parse_date(date)
        if (year is None or dt.year == year) and \
           (month is None or dt.month == month):
            result[date] = draws
    return result

def calculate_frequency(filtered_data):
    """
        Determine the FREQUENCY of the filtered data
    """
    counter = Counter()
    for draws in filtered_data.values():
        for row in draws:
            counter.update(row)
    return counter

def total_draws(filtered_data):
    return sum(len(draws) for draws in filtered_data.values())

def filter_on_month_year(year, month):
    """
        Filter the data to find the extractions of the selected year and month
    """
    filtered = []

    for date_str, numbers in data.items():
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")

        if year and date_obj.year != year:
            continue

        if month and date_obj.month != month:
            continue

        filtered.append((date_str, numbers))

    return filtered

def check_extraction_duplicate(user_numbers):
    """
        Check if the provided extraction has already been extracted in the past
    """
    found_dates = []

    for date_str, numbers in data.items():
        if isinstance(numbers[0], list):
            draws = numbers
        else:
            draws = [numbers]

        for draw in draws:
            if sorted(map(int, draw)) == user_numbers:
                found_dates.append(date_str)

    if found_dates:
        st.warning("Extragerea a fost găsită!")
        st.write("Date găsite:")
        st.table(pd.DataFrame(found_dates, columns=["Data"]))
    else:
        st.success("Extragerea nu a fost găsită în istoric.")

def build_draw_table(data):
    """
        Create table with the extractions based on search metrics
    """
    rows = []

    for date_str, numbers in data.items():

        draws = numbers if isinstance(numbers[0], list) else [numbers]
        for draw in draws:
            row = {"Data": date_str, "Nr1": int(draw[0]), "Nr2": int(draw[1]), "Nr3": int(draw[2]), "Nr4": int(draw[3]), "Nr5": int(draw[4]), "Nr6": int(draw[5])}
            rows.append(row)
    
    if not rows:
        return
    
    df = pd.DataFrame(rows)
    draw_index = st.selectbox("Selectează extragerea (index)", ["Toate"] + list(range(1, len(df)+1)))

    if draw_index != "Toate":
        df = df.iloc[[draw_index-1]]

    return df

def frecventa_numere(data):
    """
        Create a table with the frequency of each number from 1 to 49 based on search metrics
    """
    # initializam frecventa numerelor 1-49
    freq = {i: 0 for i in range(1, 50)}

    for date_str, numbers in data.items():
        # cazul cand intr-o zi sunt mai multe extrageri
        if isinstance(numbers[0], list):

            for draw in numbers:
                for num in draw:
                    num = int(num)
                    if 1 <= num <= 49:
                        freq[num] += 1

        # cazul unei singure extrageri
        else:

            for num in numbers:
                num = int(num)
                if 1 <= num <= 49:
                    freq[num] += 1

    # transformare in tabel
    tabel = pd.DataFrame([freq])
    return tabel

def analiza_intervale_pozitii(data):
    """
        Check the frequency of the numbers on the different ranges
    """
    intervale = {"1-10": (1,10), "11-20": (11,20), "21-30": (21,30), "31-40": (31,40), "41-49": (41,49)}
    pozitii = [1,2,3,4,5,6]

    rezultat = {interval:{p:0 for p in pozitii} for interval in intervale}

    for date_str, numbers in data.items():
        # mai multe extrageri
        if isinstance(numbers[0], list):
            draws = numbers
        else:
            draws = [numbers]

        for draw in draws:
            for i, num in enumerate(draw):
                num = int(num)

                for interval,(start,end) in intervale.items():
                    if start <= num <= end:
                        rezultat[interval][i+1] += 1

    df = pd.DataFrame(rezultat).T
    df.columns = ["Pos1","Pos2","Pos3","Pos4","Pos5","Pos6"]

    return df

# ----------------------------------------------------------------------------------- #


data = load_data()

# Extract and sort all the years from results
all_years = sorted({parse_date(d).year for d in data})

# SIDEBAR filter
selected_year = st.sidebar.selectbox("An", ["Toți"] + all_years)
selected_month = st.sidebar.selectbox("Lună", ["Toate"] + list(range(1, 13)))

# Set default values on select year & month
year_filter = None if selected_year == "Toți" else selected_year
month_filter = None if selected_month == "Toate" else selected_month

# ----------------------------------------------------------------------------------- #
#
#
#
# --------- METRICS --------- #
filtered = filter_data(year_filter, month_filter)
freq = calculate_frequency(filtered)

col1, col2 = st.columns(2)
col1.metric("📅 Total extrageri", total_draws(filtered))
col2.metric("🔢 Numere distincte", len(freq))

st.divider()

# --------- QUERY SECTION --------- #
st.subheader("🔍 Interogare număr specific")

number_query = st.text_input("Introdu număr")

if number_query:
    appearances = freq.get(number_query, 0)
    st.write(f"Numărul {number_query} apare de {appearances} ori în filtrul curent.")

st.divider()

# ---------- YEAR-MONTH EXTRACTIONS ---------- #
extractions = filter_on_month_year(selected_year, selected_month)

# SIDEBAR FILTER - extraction number
#nr_extractions = len(extractions)
#extraction_number = st.sidebar.selectbox("Număr extragere", ["Toate"] + list(range(0, nr_extractions)))

t = build_draw_table(filtered)

st.subheader("Extrageri")
st.dataframe(t, hide_index=True, use_container_width=True)

st.divider()

# ----------- ALL NUMBERS FREQUENCY HISTORIC ------------
tabel_frecventa = frecventa_numere(filtered)
st.subheader("Frecventa numerelor (1-49)")
st.dataframe(tabel_frecventa, use_container_width=True, hide_index=True)


tabel_intervale = analiza_intervale_pozitii(filtered)
st.subheader("Distributia intervalelor per pozitii")
st.dataframe(tabel_intervale, use_container_width=True)

# --------- CHECK DUPLICATE --------- #
st.subheader("Verificare extragere existentă")
st.text("Introdu 6 numere diferite cuprinse între 1 și 49")

cols=st.columns(6)
with cols[0]:
    a = st.number_input("1°:", 1, 49, key="a")
with cols[1]:
    b = st.number_input("2°:", 1, 49, key="b")
with cols[2]:
    c = st.number_input("3°:", 1, 49, key="c")
with cols[3]:
    d = st.number_input("4°:", 1, 49, key="d")
with cols[4]:
    e = st.number_input("5°:", 1, 49, key="e")
with cols[5]:
    f = st.number_input("6°:", 1, 49, key="f")

# input numbers to check if already extracted
user_input_numbers = sorted([a, b, c, d, e, f])
if st.button("Verifică extragerea"):
    check_extraction_duplicate(user_input_numbers)

st.divider()
