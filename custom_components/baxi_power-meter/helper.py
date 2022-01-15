from datetime import datetime


def convert_datetime_to_timestamp(moment):
    return int(round(datetime.timestamp(moment)))
