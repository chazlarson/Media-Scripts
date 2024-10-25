""" This module contains functions for setting up and using loggers. """
import logging

def setup_logger(logger_name, log_file, level=logging.INFO):
    """docstring placeholder"""
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(file_handler)

def setup_dual_logger(logger_name, log_file, level=logging.INFO):
    """docstring placeholder"""
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(file_handler)
    log_setup.addHandler(stream_handler)

def logger(msg, level, logfile):
    """docstring placeholder"""
    log = logging.getLogger('activity_log') if logfile == 'a' else logging.getLogger('download_log')
    if level == 'info':
        log.info(msg)
    if level == 'warning':
        log.warning(msg)
    if level == 'error':
        log.error(msg)

def plogger(msg, level, logfile):
    """Log and print a message to the console."""
    logger(msg, level, logfile)
    print(msg)

def blogger(msg, level, logfile, p_bar):
    """Log and print a message to the console and a progress bar."""
    logger(msg, level, logfile)
    p_bar.text(msg)
