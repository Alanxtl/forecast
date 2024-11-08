import configparser

class Config:
    config = {}

    def __init__(self):
        self.config_parsor = configparser.ConfigParser()
        with open(f"./config.ini","r") as file_object:
            self.config_parsor.read_file(file_object)
            Config.config["raw_data_path"] = self.config_parsor.get("DEFAULT","data_path_raw")
            Config.config["predict_data_path"] = self.config_parsor.get("DEFAULT","data_path_predict")
            Config.config["log_path"] = self.config_parsor.get("DEFAULT","log_path")
            Config.config["token"] = self.config_parsor.get("token","token")
            Config.config["window_size"] = self.config_parsor.get("VAR","window_size")
            Config.config["predict_size"] = self.config_parsor.get("VAR","predict_size")
            Config.config["step_size"] = self.config_parsor.get("VAR","step_size")

    @staticmethod
    def get_config():
        if ( len(Config.config) < 1 ):
            Config()
        return Config.config

if __name__ == "__main__":
    print(1)
