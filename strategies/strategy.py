from plotly import graph_objects as go
import pandas as pd
from abc import abstractmethod
import streamlit


class Strategy:
    def __init__(self, name, data: pd.DataFrame):
        self.name = name
        self.data = data

    @abstractmethod
    def execute(self):
        pass
