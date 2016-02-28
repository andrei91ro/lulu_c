import logging
import colorlog # colors log output
from lulu_pcol_sim import sim
import sys # for argv

def createInstanceHeader(pcol, path):
    """Create an instance of the passed P colony that is written as a header in C at the given path

    :pcol: The pcolony object that was read by lulu_pcol_sim
    :path: The path to the instance.h that will be written

    """
    pass
# end createInstanceHeader()

#   MAIN
if (__name__ == "__main__"):

    formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s %(message)s %(reset)s",
            datefmt=None,
            reset=True,
            log_colors={
                    'DEBUG':    'cyan',
                    'INFO':     'green',
                    'WARNING':  'yellow',
                    'ERROR':    'red',
                    'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
    )
    if ('--debug' in sys.argv):
        colorlog.basicConfig(stream = sys.stdout, level = logging.DEBUG)
    else:
        colorlog.basicConfig(stream = sys.stdout, level = logging.INFO) # default log level
    stream = colorlog.root.handlers[0]
    stream.setFormatter(formatter);

    if (len(sys.argv) < 2):
        logging.error("Expected input file path as parameter")
        exit(1)

    if (len(sys.argv) < 3):
        logging.error("Expected the path to the header (that will be generated) as the last parameter")
        exit(1)

    path = sys.argv[2]

    # read Pcolony from file
    pObj = sim.readInputFile(sys.argv[1])
    pcol = None
    # if the p object read from the input file is a Pswarm
    if (type(pObj) == sim.Pswarm):
        if (len(sys.argv) < 3):
            logging.error("Expected the name of a Pcolony as parameter")
            exit(1)
        if (sys.argv[2] not in pObj.C):
            logging.error("Expected the name of a Pcolony as parameter")
            logging.info("Valid Pcolony names for this file are: %s" % pObj.C)
            exit(1)

        if (len(sys.argv) < 4):
            logging.error("Expected the path to the header (that will be generated) as the last parameter")
            exit(1)

        pcol = pObj.colonies[sys.argv[2]]
        path = sys.argv[3]

    else:
        pcol = pObj

    createInstanceHeader(pcol, path)
