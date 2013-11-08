import pylast
import time

class EplpInterface():

    def __init__(self):
        self.api_key = "36d182e03ea45b7639ae7aa878c7da26"
        self.api_secret = "177f45b76cca0a31ea70965639d87ab2"


        self.lfm = pylast.LastFMNetwork(
                                    api_key = self.api_key,
                                    api_secret = self.api_secret,
                                    )
