from dataclasses import dataclass

@dataclass
class ClockStructure():
    name: str
    dept: str
    salary: str
    """Helper structure to pack a signal info
    """
    def __init__(self):
        """Default init
        """
        self.delay = "20"
        self.period = "20"
        self.width = "20"
    
    def __init__(self, delay, period, width):
        """Init with parameters

        Parameters
        ----------
        delay : str representing a num
            Delay of the signal
        period : str representing a num
            Period of the signal
        width : str representing a num
            Width of the signal
        """
        self.delay = delay
        self.period = period
        self.width = width