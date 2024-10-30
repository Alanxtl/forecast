import configparser

class Config:
    config = {}

    def __init__(self):
        self.config_parsor = configparser.ConfigParser()
        with open(f"./config.ini","r") as file_object:
            self.config_parsor.read_file(file_object)
            Config.config["token"] = self.config_parsor.get("DEFAULT","token")

    @staticmethod
    def get_config():
        if ( len(Config.config) < 1 ):
            Config()
        return Config.config

if __name__ == "__main__":
    print(Config.get_config())
