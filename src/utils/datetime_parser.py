from datetime import datetime

def parse_datetime(time_string) -> datetime:
    try:
        parsed_time = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S%z")
        return parsed_time
    except ValueError:
        raise ValueError("Incorrect time format, should be YYYY-MM-DD HH:MM:SS+08:00")

if __name__ == "__main__":
    print(parse_datetime("2024-11-11 23:19:15+09:00"))
