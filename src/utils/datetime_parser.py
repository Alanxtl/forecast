from datetime import datetime

def parse_datetime(time_string: str) -> datetime:
    time_string = str(time_string)
    try:
        parsed_time = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S%z")
        return parsed_time
    except ValueError:
        try:
            parsed_time = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S%z")
            return parsed_time
        except ValueError:
            try:
                parsed_time = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
                return parsed_time
            except ValueError:
                raise ValueError(f"Incorrect time format {time_string}")
    
if __name__ == "__main__":
    print(parse_datetime("2024-11-11 23:19:15+09:00"))
