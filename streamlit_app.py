from playwright.sync_api import sync_playwright, TimeoutError
import os
import json
import time
from datetime import datetime

import openpyxl

# 
# Script to read the elements from loto website and extract the numbers from the list
# 

URL = "https://www.loto.ro/loto-new/newLotoSiteNexioFinalVersion/web/app2.php/jocuri/649_si_noroc/rezultate_extragere.html"
URL_joker = "https://www.loto.ro/loto-new/newLotoSiteNexioFinalVersion/web/app2.php/jocuri/joker_si_noroc_plus/rezultate_extrageri.html"

path_to_file = "data/loto_numbers.json"
joker_file = "data/joker_numbers.json"

FIND_BUTTON = "#submitButton"
RESULTS_CONTAINER = "div.numere-extrase"
YEAR_ITEMS_SELECTOR = "div.select-an ul.dropdown-menu.inner li span.text"
MONTH_ITEMS_SELECTOR = "div.select-luna ul.dropdown-menu.inner li span.text"
EXTRACTIONS_DATES = "div.button-open-details p span"
SPAN_PARAGRAPHS = "div.button-open-details p"


months_language = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]
months_number = [1,2,3,4,5,6,7,8,9,10,11,12]

def month_name_to_number(months):
    i = 0
    months
    numbered_months = []
    for m in months:
        for n in months_language:
            if m == n:
                numbered_months.append(months_number[i])
                i += 1
                break
    
    return numbered_months

#
#  Extract the dropdown elements from the html code of the URL website
#       Provide:
#           - the reference to the web-page
#           - the reference of "dropdown_button" which allows to see the list of items of the dropdown
#           - the reference of the "dropdown" which contains the effective items
#           - the type of the dropdown, that describes the type of the elements (year/month)
#
def read_dropdown_elements(page, dropdown_button, dropdown, dropdown_type):
    page.locator(dropdown_button).click()
    page.wait_for_timeout(200)

    # select the current year in JS
    page.evaluate(f"""
    () => {{
        const items = document.querySelectorAll("{dropdown}");
        for (let i=0; i<items.length; i++) {{
            if (items[i].innerText.trim() === "{dropdown_type}") {{
                items[i].click();
                break;
            }}
        }}
    }}
    """)
    time.sleep(0.1)  # scurt delay ca să aplice site-ul

#
#   Write the data to the json file
#
def write_to_json_file(file_path, data):
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

#
#   Checks and counts how many times the element is present inside the list
#
def count_occurencies(list, element):
    occurencies = 0
    for i in list:
        if i == element:
            occurencies += 1
    return occurencies

#
#   SITUATION: as the page contains two type of number extractions for almost each extraction day
#                we want to extract only the first time of this extraction, so we need to not add
#                the extraction dates twice, with an exception for SPECIAL EXTRACTIONS
#
#   Checks if the current_date was used also for an extra extraction
#    - extracted_dates > is the list with all the dates from specific year and month
#    - dates > is the list with the current dates extracted
#    - current_date > is the current date to check if the case to be added
#    - special_extr > tells if the current date is from an extra extraction
#
def check_extra_extraction(extracted_dates, dates:list, current_date, special_extr):
    extr_dates_nr = count_occurencies(extracted_dates, current_date)
    cur_dates_list_nr = count_occurencies(dates, current_date)

    # Check if special extraction or no date added in proportion of 1:2 for dates:extracted_dates
    if special_extr or cur_dates_list_nr < extr_dates_nr / 2:
        dates.append(current_date)


def json_to_excel_file(objects_list):
    # creează workbook Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rezultate"

    # Header
    ws.append(["Data", "N1", "N2", "N3", "N4", "N5", "N6"])

    # populate rows
    for date, values in objects_list.items():
        buffer = []

        for item in values:
            if isinstance(item, list):
                # scrie direct lista (rând complet)
                ws.append([date] + item)
            else:
                buffer.append(item)

                if len(buffer) == 6:
                    ws.append([date] + buffer)
                    buffer = []

    # salvează
    wb.save("rezultate.xlsx")


def update_number_extraction(filePath, url):
    with sync_playwright() as p:
        # Check file content and load it if not empy
        if os.path.exists(filePath):
            with open(filePath, "r", encoding="utf-8") as f:
                month_results = json.load(f)
        else:
            month_results = {}

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        now = datetime.now()

        # ======== EXTRACT THE YEARS ========
        years = page.locator(YEAR_ITEMS_SELECTOR).all_inner_texts()
        years.sort()                        # Order cronologically
        years.remove("Selectati anul")      # Remove default option from lists

        # ======== EXTRACT THE MONTHS ========
        months = page.locator(MONTH_ITEMS_SELECTOR).all_inner_texts()
        months.remove("Selectati luna")    # Remove default option from list

        for year in years:
            # Extract year dropdown elements
            read_dropdown_elements(page, "div.select-an button", YEAR_ITEMS_SELECTOR, year)

            # dacă e anul curent, limităm lunile
            if int(year) == now.year:

                months = [m for m in month_name_to_number(months) if int(m) <= now.month]

            for month in months:
                # Selecte the current "checking-month" from dropdown
                read_dropdown_elements(page, "div.select-luna button", MONTH_ITEMS_SELECTOR, month)
                
                # click on Find
                page.click(FIND_BUTTON)

                # Wait for results
                try:
                    page.wait_for_selector(RESULTS_CONTAINER, timeout=10000)
                    time.sleep(0.5)
                except TimeoutError:
                    continue

                # Extract the numbers images
                images = page.locator(f"{RESULTS_CONTAINER} img").all()
                numbers = []
                for img in images:
                    src = img.get_attribute("src")
                    if src:
                        numbers.append(os.path.splitext(os.path.basename(src))[0])

                # Extract the exact dates of number-extraction
                span_paragraph = page.locator(SPAN_PARAGRAPHS).all()
                dates_span = page.locator(EXTRACTIONS_DATES).all()
                dates_extracted = []        # all the dates from span
                dates = []      # Checked dates
                for date, paragraph in zip(reversed(dates_span), reversed(span_paragraph)):     # Teke dates cronologically
                    text = paragraph.text_content()     # Extract the text of the paragraph
                    span = date.text_content()      # Extract the date text from the span
                    dates_extracted.append(span)

                    # ALLOW DUPLICATE ONLY IF EXTRA-EXTRACTION
                    check_extra_extraction(dates_extracted, dates, span, "SPECIALE" in text)

                # Make 6 numbers in a row
                rows = [numbers[i:i+6] for i in range(0, len(numbers), 6)]
                rows.reverse()

                #print(f"\n📅 {year}-{month}")
                # SAVE TO FILE current month's extractions
                for i, row in enumerate(rows, 1):
                    if dates[i-1] not in month_results:     # if not yet added, create a list
                        month_results[dates[i-1]] = []
                    month_results[dates[i-1]].append(row)

                # SAVE UPDATED RESULT TO FILE
                write_to_json_file(filePath, month_results)

        browser.close()



if __name__ == "__main__":

    file = joker_file     # change to joker for joker numbers

    update_number_extraction(file, URL_joker)

    with open(file, "r", encoding="utf-8") as f:
        month_results = json.load(f)

    #json_to_excel_file(month_results)

# TO DO:
#   - Continue the app with queries about numbers
#
#   QUERIES:
#    > How many times a number is chosen as first one in a year/all times
#    > How many times a number < than N is chosen in a serie
#    > How many times a number is chosen in a year
