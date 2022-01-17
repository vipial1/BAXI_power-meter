from datetime import datetime


def convert_datetime_to_timestamp(moment):
    return int(round(datetime.timestamp(moment)))


def create_sensor_name(device_name, period):
    if not period:
        return f"{device_name} energy consumption"

    return f"{device_name} {period} energy consumption"
