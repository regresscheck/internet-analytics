import logging


def setup_logging():
    logging.basicConfig(filename='app.log', filemode='w', level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
