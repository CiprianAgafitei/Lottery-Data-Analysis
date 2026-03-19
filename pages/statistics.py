import streamlit as st
from datetime import datetime
import pandas as pd

from streamlit_app import data, parse_date, filter_data, calculate_frequency


# ----------------------------------------------------------------------------------- #

# Extract and sort all the years from results
all_years = sorted({parse_date(d).year for d in data})

# SIDEBAR filter
selected_year = st.sidebar.selectbox("An", ["Toți"] + all_years)
selected_month = st.sidebar.selectbox("Lună", ["Toate"] + list(range(1, 13)))

# Set default values on select year & month
year_filter = None if selected_year == "Toți" else selected_year
month_filter = None if selected_month == "Toate" else selected_month


filtered = filter_data(year_filter, month_filter)
freq = calculate_frequency(filtered)
# ----------------------------------------------------------------------------------- #


def check_number_position_frequency(number_to_search):
    """
        Check the frequency of each number for each position from 1 to 6, if at least month or year selected

        Args:
            number_to_search (int):  the number for which to count the frequency for each position from 1 to 6

        Return:
            nothing:  if not selected at least 1 between month or year
            void:  show the table with the frequencies of the number for each position from 1 to 6
    """
    if not (selected_year or selected_month):
        st.info("Selectează cel puțin anul sau luna.")
        return

    position_counter = {i: 0 for i in range(1, 7)}

    for date_str, numbers in data.items():
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")

        if selected_year and date_obj.year != selected_year:
            continue
        if selected_month and date_obj.month != selected_month:
            continue

        if isinstance(numbers[0], list):
            draws = numbers
        else:
            draws = [numbers]

        for draw in draws:
            for i, num in enumerate(draw):
                if int(num) == number_to_search:
                    position_counter[i+1] += 1

    df = pd.DataFrame(
        list(position_counter.items()),
        columns=["Pozitie", "Frecventa"]
    )
    st.dataframe(df, hide_index=True, use_container_width=True)


def analyze_next_number(data, number, position):
    """
        Check the frequency in the past for the situation when the number has been followed
        by a greater ore a lower one, in the specified position (from 1 to 5)

        Args:
            data (list):  the list with all the extractions
            number (int): the actual number taken in consideration
            position (int): the current position of the provided number

        Return:
            nothing:  if the number has not been found on the selected position
            void:  show the table with all the frequencies of when a greater or lower number
                    followed the current number in the current position
    """
    freq_greater = 0
    freq_lower = 0
    total_cases = 0

    intervals = {"1-10":0, "11-20":0, "21-30":0, "31-40":0, "41-49":0}

    for date_str, numbers in data.items():
        draws = numbers if isinstance(numbers[0], list) else [numbers]

        for draw in draws:
            draw = list(map(int, draw))
                
            if position >= len(draw):
                continue

            current = draw[position-1]

            if current == number:
                next_number = draw[position]
                total_cases += 1

                if next_number > number:
                    freq_greater += 1
                elif next_number < number:
                    freq_lower += 1

                # RANGES
                if 1 <= next_number <= 10:
                    intervals["1-10"] += 1
                elif 11 <= next_number <= 20:
                    intervals["11-20"] += 1
                elif 21 <= next_number <= 30:
                    intervals["21-30"] += 1
                elif 31 <= next_number <= 40:
                    intervals["31-40"] += 1
                else:
                    intervals["41-49"] += 1

    if total_cases == 0:
        st.warning("Numărul nu a fost găsit pe poziția selectată.")
        return
    
    # ----- TABEL 1 -----
    df_main = pd.DataFrame({
        "Număr ales": [number],
        "Frecvență >": [freq_greater],
        "Frecvență <": [freq_lower]
    })
    st.subheader("Mai mare / Mai mic")
    st.dataframe(df_main, hide_index=True, use_container_width=True)

    # ----- TABEL 2 -----
    df_intervals = pd.DataFrame([intervals])

    st.subheader("Distribuție pe intervale")
    st.dataframe(df_intervals, hide_index=True, use_container_width=True)


# --------- FREQUENCY SECTION --------- #
st.subheader("Frecvență Numere")

if freq:
    st.bar_chart(freq)

    st.write("### Top 6 cele mai frecvente:")
    for number, count in freq.most_common(6):
        st.write(f"🔢 {number} → {count}")
else:
    st.warning("Nu există date pentru filtrul selectat.")

st.divider()

# ---------- CHECK FREQUENCY OF NEXT NUMBER ----------- #
st.subheader("Analiză număr următor")

row_cols = st.columns(2)
with row_cols[0]:
    selected_number = st.number_input("Număr selectat", 1, 49)
with row_cols[1]:
    selected_position = st.selectbox("Poziția numărului", [1,2,3,4,5])
    
if st.button("Generează analiză"):
    analyze_next_number(filtered, selected_number, selected_position)
