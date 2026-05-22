# -*- coding: utf-8 -*-
"""
Project : Pyvoa
Date :    april 2020 - december 2025
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
import pyvoa.tools as pt

import sys
import shutil

def blinking_centered_text(typemsg, message, blinking=False, text_color="white", bg_color="red"):

    # Détecter l'environnement
    try:
        import google.colab
        in_colab = True
    except ImportError:
        in_colab = False

    try:
        env_name = get_ipython().__class__.__name__
        is_jupyter = env_name == 'ZMQInteractiveShell'
    except NameError:
        is_jupyter = False

    # --- Jupyter / Colab : affichage HTML ---
    if is_jupyter or in_colab:
        from IPython.display import display, HTML

        color_map = {
            'yellow':  '#B8860B',
            'red':     '#C0392B',
            'green':   '#27AE60',
            'blue':    '#2980B9',
            'white':   '#FFFFFF',
            'black':   '#000000',
            'cyan':    '#17A589',
            'magenta': '#8E44AD',
            'default': '#FFFFFF',
        }

        bg_color_html   = color_map.get(bg_color.lower(),   bg_color)
        text_color_html = color_map.get(text_color.lower(), text_color)
        anim = "animation: blink 1s step-start infinite;" if blinking else ""

        style = f"""
        <style>
            @keyframes blink {{ 50% {{ opacity: 0; }} }}
        </style>
        <div style="text-align:center; background-color:{bg_color_html};
                    color:{text_color_html}; padding:10px; border-radius:5px;
                    font-weight:bold; {anim}">
            <div>{typemsg}</div>
            <div>{message}</div>
        </div>
        """
        display(HTML(style))

    # --- Terminal : affichage ANSI ---
    else:
        color_codes = {
            'black':   '30', 'red':     '31', 'green': '32', 'yellow': '33',
            'blue':    '34', 'magenta': '35', 'cyan':  '36', 'white':  '37',
            'default': '39',
        }
        bg_codes   = {name: str(int(code) + 10) for name, code in color_codes.items()}
        text_code  = color_codes.get(text_color.lower(), '37')
        bg_code    = bg_codes.get(bg_color.lower(), '41')

        ansi_start = f"\033[5;{text_code};{bg_code}m" if blinking else f"\033[{text_code};{bg_code}m"
        ansi_reset = "\033[0m"

        try:
            _, columns = shutil.get_terminal_size()
        except:
            columns = 80

        sys.stdout.write(f'{ansi_start}{typemsg.center(columns)}{ansi_reset}\n')
        sys.stdout.write(f'{ansi_start}{message.center(columns)}{ansi_reset}\n')



class PyvoaInfo(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        if pt.get_verbose_mode()>1:
            blinking_centered_text('PYVOA Info !',message, blinking=0,text_color='black', bg_color='blue')
        Exception(message)

class PyvoaDBInfo(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        if pt.get_verbose_mode()>1:
            blinking_centered_text('PYVOA Info !',message, blinking=0,text_color='white', bg_color='blue')
        Exception(message)

class PyvoaWarning(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Warning !',message, blinking=0,text_color='black', bg_color='yellow')
        Exception(message)

class PyvoaError(Exception):
    """Base class for exceptions in PYVOA."""
    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        #Exception(message)

class PyvoaKeyError(PyvoaError, KeyError):
    """Exception raised for errors in used key option.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        KeyError(message)
        PyvoaError(message)

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
