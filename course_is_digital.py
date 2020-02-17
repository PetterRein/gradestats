import sys
from typing import Optional, List, Dict
import time
import random

import requests
import bs4

URL_FORMAT_STRING = "https://www.ntnu.no/studier/emner/{}#tab=omEksamen"
URL_COURSE_YEAR_FORMAT_STRING = "https://www.ntnu.no/studier/emner/{}/{}#tab=omEksamen"
HTML_PARSER = "html5lib"  # "html5lib" is external dependency, "html.parser" is python built-in


def retrieve_exam_years(course_code: str) -> List[str]:
    course_url = URL_FORMAT_STRING.format(course_code)
    response = requests.get(course_url)
    if response.status_code != 200:
        warn(f"WARN: Response was not 200! For course {course_code}, was {response.status_code}")
    soup = bs4.BeautifulSoup(response.text, HTML_PARSER)
    select_tag_exam_year: Optional[bs4.element.Tag] = soup.find(attrs={"id": "selectedYear"})
    if select_tag_exam_year is None:
        raise Exception(f"Couldn't find the exam year select element, fagkode={course_code}")
    
    exam_years: List[str] = []
    for option in select_tag_exam_year.find_all("option"):
        exam_years.append(option["value"])
    
    return exam_years


def retrieve_exam_type_of_years(
        course_code: str,
        years: List[str],
        sleep_time_mean_ms=0.1) -> Dict[str, Dict[str, bool]]:
    with requests.Session() as session:
        session = requests.Session()
        result = dict()
        
        for year in years:
            url = URL_COURSE_YEAR_FORMAT_STRING.format(course_code, year)
            response = session.get(url)
            soup = bs4.BeautifulSoup(response.text, HTML_PARSER)
            omEksamen: Optional[bs4.element.Tag] = soup.find(attrs={"id": "omEksamen"})
            if omEksamen is None:
                warn(f"Couldn't find omEksamen for {course_code} year {year}")
                continue
            dl: Optional[bs4.element.Tag] = omEksamen.find("dl")
            if dl is None:
                raise Exception(f"omEksamen tag for {course_code} year {year} had no dl tag")
            term_is_digital_dict: Dict[str, bool] = dict()
            for dt in dl.find_all("dt"):
                term: Optional[bs4.element.Tag] = dt.find(class_="exam-term")
                if term is None:
                    continue
                
                system: Optional[bs4.element.Tag] = dt.find(class_="exam-system")
                exam_status: Optional[bs4.element.Tag] = dt.find(class_="exam-code")
                
                # skip continuation exam
                is_ordinary = exam_status.find("abbr").text.strip() == "ORD"
                if not is_ordinary:
                    continue
                
                term_std = ""
                term_txt = term.text.strip()
                if term_txt == "Vår":
                    term_std = "Spring"
                elif term_txt == "Høst":
                    term_std = "Fall"
                else:
                    continue
                term_is_digital_dict[term_std] = system.text.strip() == "INSPERA"
            result[year] = term_is_digital_dict
            # sleep a little bit to avoid hammering the website
            # from 0.5 to 1.5 of mean time
            time_to_sleep = random.random() * sleep_time_mean_ms / 2 + sleep_time_mean_ms
            time.sleep(time_to_sleep)
        return result


def warn(text: str):
    print(text, file=sys.stderr)


def _test_functions():
    course_code = "TDT4127" # "TDT4100" TDT4117 IT3010 TDT4127 (itgk)
    years = retrieve_exam_years(course_code)
    print(retrieve_exam_type_of_years(course_code, years))
    # exam_is_digital("IT3010")


if __name__ == '__main__':
    _test_functions()

