from abc import ABC, abstractmethod

# Base class for all screens in the application. Each screen must implement the draw and handle_event methods
class Screen(ABC):
    def __init__(self, manager):
        self.manager = manager
    
    @abstractmethod
    def draw(self): 
        """ must be implemented by the subclass to handle rendering"""
        pass
    

    @abstractmethod
    def handle_event(self, event): 
        """ must be implemented by the subclass to handle user inputs"""
        pass     