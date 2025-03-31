import logging


def getLogger(name):
    if name == "__main__" or name == "bos_dag.main":
        return logging.getLogger()
    else:
        return logging.getLogger(name)
