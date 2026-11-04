import sounddevice as sd

class AudioDevice():

    @staticmethod
    def list_devices():
        return sd.query_devices

    @staticmethod
    def default_input():

        device = sd.default.device[0]

        return sd.query_devices(device)

        
