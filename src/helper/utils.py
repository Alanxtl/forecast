def parse_datetime(time_string):
    from datetime import datetime
    try:
        parsed_time = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
        return parsed_time
    except ValueError:
        raise ValueError("Incorrect time format, should be YYYY-MM-DDTHH:MM:SSZ")

if __name__ == "__main__":
    print(parse_datetime("2024-03-28T06:23:13Z"))
