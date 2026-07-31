import configparser
import os
from typing import Dict, Any

    
# Get the absolute path to the current file
current_file_path = os.path.abspath(__file__)

# Get the base directory of the project
base_directory = os.path.dirname(os.path.dirname(current_file_path))

configuration = configparser.RawConfigParser()
configuration.read(os.path.join(base_directory, 'Configuration', 'config.ini'))


# Consists of Methods to get the configuration details
class Read_Configurations:
    configuration = configuration
    _env_mapping = {
        #"uat": "Catalyst application details UAT",
        "qa": "Catalyst application details QA",
        #"prod": "Catalyst application details PROD",
    }
    _env_section = None

    @classmethod
    def initialize(cls, env: str):
        cls._env_section = cls._env_mapping.get(env.lower())
        if not cls._env_section:
            raise ValueError(f"Unknown environment: {env}")
    
    @classmethod
    def get_value(cls, key: str, env: str = None) -> str:
        if cls._env_section is None:
            raise RuntimeError("Environment not initialized. Call initialize(env) first.")
        env_section = cls._env_section
        if env:
            env_section = cls._env_mapping.get(env.lower(), cls._env_section)
        return cls.configuration.get(env_section, key)
    
    # This method will return the application url
    @staticmethod
    def get_app_url():
        url = configuration.get('orangehrm application details', 'baseURL')
        return url
 
    # This method will return the username
    @staticmethod
    def get_user_name():
        user_name = configuration.get('orangehrm application details', 'userName')
        return user_name
 
    # This method will return the password
    @staticmethod
    def get_password():
        password = configuration.get('orangehrm application details', 'password')
        return password
 
    # This method will return the browser
    @staticmethod
    def get_browser():
        browser = configuration.get('orangehrm application details', 'browser')
        return browser
 
    # This method will return the channel
    @staticmethod
    def get_channel():
        channel = configuration.get('orangehrm application details', 'channel')
        return channel
 
    # This method will return the headless
    @staticmethod
    def get_headless():
        headless = configuration.getboolean('orangehrm application details', 'headless')
        return headless
 
    # This method will return the slowMotion
    @staticmethod
    def get_slow_motion():
        slow_motion = configuration.getint('orangehrm application details', 'slowMotion')
        return slow_motion
 
    @staticmethod
    def get_browser_configurations() -> dict[str, bool | str | int | Any]:
        browser_configurations = {
            "headless": Read_Configurations.get_headless(),
            "channel": Read_Configurations.get_channel(),
            "slow_mo": Read_Configurations.get_slow_motion()
        }
        return browser_configurations
 
    @classmethod
    def get_containername(cls):
        conn = configuration.get('Catalyst application details', 'container_name')
        return conn
 
    @classmethod
    def get_blobpath(cls):
        conn = configuration.get('Catalyst application details', 'path')
        return conn
 
    @classmethod
    def get_connectionstring(cls):
        conn = configuration.get('Catalyst application details', 'connection_string')
        return conn
 
    @classmethod
    def get_BaseUri(cls):
        conn = configuration.get('Catalyst application details', 'base_uri')
        return conn
 
    @staticmethod
    def get_CatalsytBrowser():
        browser = configuration.get('Catalyst application details', 'browser')
        return browser
    @staticmethod
    def get_CatalystChannel():
        channel = configuration.get('Catalyst application details', 'channel')
        return channel
    @staticmethod
    def get_TestAPIURL1():
        value = configuration.get('Catalyst application details', 'TestAPIURL1')
        return value
 
    @staticmethod
    def get_TestApplicationUserName2():
        value = configuration.get('Catalyst application details', 'TestApplicationUserName2')
        return value
 
    @staticmethod
    def get_TestApplicationPassword2():
        value = configuration.get('Catalyst application details', 'TestApplicationPassword2')
        return value
 
    @staticmethod
    def get_TokenBaseAPI():
        value = configuration.get('Catalyst application details', 'TokenBaseAPI')
        return value
 
    @staticmethod
    def get_baseUrl_UAT():
        value = configuration.get('Catalyst application details', 'baseUrl_UAT')
        return value
 
    @staticmethod
    def get_UploadPDF():
        value = configuration.get('Catalyst application details', 'UploadPDF')
        return value
 
    @staticmethod
    def get_TestDataRepository():
        value = configuration.get('Catalyst application details', 'TestDataRepository')
        return value