from calendar import c
import configparser
import toml
from loguru import logger

class Config:
    config = {}

    def __init__(self):
        self.config_parsor = configparser.ConfigParser()
        with open(f"./config.ini","r") as file_object:
            self.config_parsor.read_file(file_object)
            Config.config["data_path"] = self.config_parsor.get("DEFAULT","data_path")
            Config.config["raw_data_path"] = self.config_parsor.get("DEFAULT","raw_data_path")
            Config.config["predict_data_path"] = self.config_parsor.get("DEFAULT","predict_data_path")
            Config.config["log_path"] = self.config_parsor.get("DEFAULT","log_path")
            Config.config["token"] = self.config_parsor.get("token","token")
            Config.config["window_size"] = int(self.config_parsor.get("VAR","window_size"))
            Config.config["predict_size"] = int(self.config_parsor.get("VAR","predict_size"))
            Config.config["step_size"] = int(self.config_parsor.get("VAR","step_size"))
        Config.get_token()

    @staticmethod
    def get_config():
        if ( len(Config.config) < 1 ):
            Config()
        return Config.config

    @staticmethod
    def set_size(window_size, step_size, predict_size):
        Config.config["window_size"] = window_size
        Config.config["step_size"] = step_size
        Config.config["predict_size"] = predict_size

    @staticmethod
    def get_token():
        try:
            with open(r'.streamlit/config.toml', 'r') as f:
                config = toml.load(f)
                Config.config["token"] = config["token"]
        finally:
            logger.info("Token: {}".format(Config.config["token"]))
            
