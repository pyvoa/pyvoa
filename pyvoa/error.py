# -*- coding: utf-8 -*-
""" 
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.error

About :
-------

Main class definitions for error management within the PYVOA.framework.
All Pyvoa exceptions should derive from the main PyvoaError class.
"""
import os
import sys
import time
from time import sleep
from IPython import get_ipython


def blinking_centered_text(typemsg, message, blinking=False, text_color="white", bg_color="red"):
    """
    Display a centered message with optional blinking and color formatting.
    
    This function is intended for terminal use. Blinking will not work in Jupyter
    or Google Colab environments, but the message will still be displayed with colors.
    
    Parameters:
        typemsg (str): The header or type of message to display.
        message (str): The main message to display.
        blinking (bool): If True, enables blinking text (terminal only). Default is False.
        text_color (str): Name of the text color (e.g., 'red', 'green', 'white'). Default is 'white'.
        bg_color (str): Name of the background color. Default is 'red'.
    """
    color_codes = {
        'black': '30', 'red': '31', 'green': '32', 'yellow': '33',
        'blue': '34', 'magenta': '35', 'cyan': '36', 'white': '37',
        'default': '39',
    }
    # Background codes are text color codes + 10
    bg_codes = {name: str(int(code) + 10) for name, code in color_codes.items()}

    text_code = color_codes.get(text_color.lower(), '37')
    bg_code = bg_codes.get(bg_color.lower(), '41')

    # ANSI escape sequence for styling
    ansi_start = f"\033[5;{text_code};{bg_code}m" if blinking else f"\033[{text_code};{bg_code}m"
    ansi_reset = "\033[0m"

    # Detect environment (Jupyter or Colab)
    try:
        import google.colab
        in_colab = True
    except ImportError:
        in_colab = False

    env_name = get_ipython().__class__.__name__ if 'get_ipython' in globals() else ""
    is_jupyter = env_name == 'ZMQInteractiveShell'

    # Get terminal size
    if in_colab:
        rows, columns = 24, 80  # fallback default
    elif is_jupyter:
        try:
            rows, columns = shutil.get_terminal_size()
        except:
            rows, columns = 24, 80
    else:
        try:
            rows, columns = os.popen('stty size', 'r').read().split()
            rows, columns = int(rows), int(columns)
        except:
            rows, columns = shutil.get_terminal_size()

    # Center and display the messages
    typemsg_centered = typemsg.center(columns)
    message_centered = message.center(columns)

    sys.stdout.write(f'{ansi_start}{typemsg_centered}{ansi_reset}\n')
    sys.stdout.write(f'{ansi_start}{message_centered}{ansi_reset}\n')
    """
    center blinking color output message
    """
    color_codes = {
        'black': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'magenta': '35',
        'cyan': '36',
        'white': '37',
        'default': '39',
    }

    bg_codes = {name: str(int(code) + 10) for name, code in color_codes.items()}
    text_code = color_codes.get(text_color.lower(), color_codes["white"])
    bg_code = bg_codes.get(bg_color.lower(), bg_codes["red"])

    if blinking:
        ansi_start = f"\033[5;{text_code};{bg_code}m"
    else:
        ansi_start = f"\033[;{text_code};{bg_code}m"
    ansi_reset = "\033[0m"
    
    try:
        import google.colab
        IN_COLAB = True
    except ImportError:
        IN_COLAB = False

    env = get_ipython().__class__.__name__
    if env != 'ZMQInteractiveShell' and not IN_COLAB:
        rows, columns = os.popen('stty size', 'r').read().split()
    elif IN_COLAB:
        rows, columns = 24, 80  # standard valuess
    else:
        import shutil
        rows, columns = shutil.get_terminal_size()

        typemsg = typemsg.center(columns)
        message = message.center(columns)
        rows, columns = int(rows), int(columns)

        typemsg = typemsg.center(columns)
        message = message.center(columns)

        sys.stdout.write(f'{ansi_start}{typemsg}{ansi_reset}\n')
        sys.stdout.write(f'{ansi_start}{message}{ansi_reset}\n')
        #print(f'{ansi_start}{typemsg}{ansi_reset}\n')
        #print(f'{ansi_start}{message}{ansi_reset}\n')

class PyvoaInfo(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Info !',message, blinking=0,text_color='black', bg_color='blue')
        Exception(message)

class PyvoaDBInfo(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Info !',message, blinking=0,text_color='white', bg_color='blue')
        Exception(message)

class PyvoaWarning(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Warning !',message, blinking=0,text_color='black', bg_color='orange')
        Exception(message)

class PyvoaError(Exception):
    """Base class for exceptions in PYVOA."""
    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        #Exception(message)

class PyvoaNoData(PyvoaError, IndexError):
    """Exception raised when there is no data to plot or to manage (invalid cut)"""

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        IndexError(message)
        PyvoaError(message)

class PyvoaWhereError(PyvoaError, IndexError):
    """Exception raised for location errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        IndexError(message)
        PyvoaError(message)


class PyvoaTypeError(PyvoaError, TypeError):
    """Exception raised for type mismatch errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        TypeError(message)
        PyvoaError(message)


class PyvoaLookupError(PyvoaError, LookupError):
    """Exception raised for type lookup errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        LookupError(message)
        PyvoaError(message)


class PyvoaNotManagedError(PyvoaError):
    """Exception raised when the error is unknown and not managed.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        PyvoaError(message)


class PyvoaDbError(PyvoaError):
    """Exception raised for database errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        PyvoaError(message)


class PyvoaConnectionError(PyvoaError, ConnectionError):
    """Exception raised for connection errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        ConnectionError(message)
        PyvoaError(message)
