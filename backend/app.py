from flask import Flask, render_template, json
import argparse
import redis, csv, sys, os
from typing import TypedDict, Tuple, Dict, Callable, List, Any, Optional
from enum import Enum
import requests
from bs4 import BeautifulSoup
from local_scraper import hospitalAvailability
from hospital_types import Hospital, HospitalID, AppointmentAvailability, ScrapedData

# Parsers
from Parsers.ntu_taipei import *
from Parsers.ntu_hsinchu import *
from Parsers.ntu_yunlin import *
from Parsers.tzuchi_taipei import *
from Parsers.mohw import *


redis_host: Optional[str] = os.environ.get("REDIS_HOST")
redis_port: Optional[str] = os.environ.get("REDIS_PORT")
redis_username: Optional[str] = os.environ.get("REDIS_USERNAME")
redis_password: Optional[str] = os.environ.get("REDIS_PASSWORD")


app = Flask(
    __name__,
    static_url_path="",
    static_folder="../dist",
    template_folder="../dist",
)


def get_availability_from_server() -> List[ScrapedData]:
    # The decode_repsonses flag here directs the client to convert the responses from Redis into Python strings
    # using the default encoding utf-8.  This is client specific.
    r: redis.StrictRedis = redis.StrictRedis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
        username=redis_username,
        ssl=True,
    )

    hospital_ids = list(range(1, 32))

    def get_availability(
        hospital_id: int,
    ) -> Optional[ScrapedData]:
        availability = r.get("hospital:" + str(hospital_id))
        if availability == "AppointmentAvailability.AVAILABLE":
            availability = AppointmentAvailability.AVAILABLE
        elif availability == "AppointmentAvailability.UNAVAILABLE":
            availability = AppointmentAvailability.UNAVAILABLE
        else:
            return None
        return (hospital_id, availability)

    availability = [get_availability(hospital_id) for hospital_id in hospital_ids]
    print(availability)
    return list(filter(None, availability))


def errorBoundary(
    f: Callable[[], ScrapedData]
) -> Callable[[], Optional[ScrapedData]]:
    def boundariedFunction() -> Optional[ScrapedData]:
        try:
            return f()
        except:
            return None

    return boundariedFunction


def hospitalData() -> List[Hospital]:
    availability = dict(get_availability_from_server())

    app.logger.warning(availability)
    with open("../data/hospitals.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        for row in reader:
            hospital_id = int(row["編號"])
            hospital_availability = (
                availability[hospital_id].value
                if hospital_id in availability
                else AppointmentAvailability.NO_DATA.value
            )
            hospital: Hospital = {
                "address": row["地址"],
                "availability": hospital_availability,
                "department": row["科別"],
                "hospitalId": int(row["編號"]),
                "location": row["縣市"],
                "name": row["醫院名稱"],
                "phone": row["電話"],
                "website": row["Website"],
            }
            rows.append(hospital)
        return rows


@app.route("/hospitals")
def hospitals() -> Any:
    data = hospitalData()
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype="application/json",
    )
    return response


@app.route("/")
def index() -> str:
    return render_template("./index.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Server to serve scraped vaccine availability data."
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="""Usually the Flask app will read from a Redis database. 
        This flag will scrape the data locally on machine. It's useful for testing.
        """,
    )
    flag_values = parser.parse_args()
    app.run(debug=True, host="0.0.0.0")
