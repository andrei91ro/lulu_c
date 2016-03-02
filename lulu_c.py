import logging
import colorlog # colors log output
from lulu_pcol_sim import sim
import sys # for argv
import time # for strftime()

def createInstanceHeader(pcol, path):
    """Create an instance of the passed P colony that is written as a header in C at the given path

    :pcol: The pcolony object that was read by lulu_pcol_sim
    :path: The path to the instance.h that will be written"""

    with open(path, "w") as fout:
        fout.write("""// vim:filetype=c
/**
 * @file lulu_instance.h
 * @brief Lulu P colony simulator internal structure.
 * In this header we define the structure of the Pcolony that will power the simulated robot
 * This file was generated automatically by lulu_c.py on %s
 * @author Andrei G. Florea
 * @author Catalin Buiu
 * @date 2016-02-29
 */
#ifndef LULU_INSTANCE_H
#define LULU_INSTANCE_H

#include "lulu.h" """ % time.strftime("%d %h %Y at %H:%M"))

        fout.write("\nenum objects {")
        for i, obj in enumerate(pcol.A):
            if (obj in ['e', 'f']):
                continue; # they are already defined in lulu.h
            if (i == 0):
                # NO_OBJECT = 0, OBJECT_ID_E = 1, OBJECT_ID_F = 2
                fout.write("\n    OBJECT_ID_%s = 3," % obj.upper());
            else:
                fout.write("\n    OBJECT_ID_%s," % obj.upper());

        fout.write("\n};")

        fout.write("\n\nenum agents {")
        for i, agent_name in enumerate(pcol.B):
            fout.write("\n    AGENT_%s," % agent_name.upper());

        fout.write("\n};")
        fout.write("""\n\n/**
 * @brief Initialises the pcol object and all of it's components
 *
 * @param pcol The P colony that will be initialized
 */
void lulu_init(Pcolony_t *pcol);

/**
 * @brief Destroys the pcol objects and all of it's components
 *
 * @param pcol The P colony that will be destroyed
 */
void lulu_destroy(Pcolony_t *pcol);

#endif""")
# end createInstanceHeader()

def createInstanceSource(pcol, path):
    """Create an instance of the passed P colony that is written as a source file in C at the given path

    :pcol: The pcolony object that was read by lulu_pcol_sim
    :path: The path to the instance.c that will be written"""

    with open(path + ".c", "w") as fout:
        fout.write("""#include "%s.h"
#include <malloc.h>

void lulu_init(Pcolony_t *pcol) {""" % path)

        # call initPcolony()
        fout.write("""\n    //init Pcolony with alphabet size = %d, nr of agents = %d, capacity = %d
    initPcolony(pcol, %d, %d, %d);""" % (len(pcol.A), len(pcol.B), pcol.n,  len(pcol.A), len(pcol.B), pcol.n))

        # init environment
        fout.write("""\n\n    //init environment""")
        counter = 0;
        for obj, nr in pcol.env.items():
            fout.write("""\n        pcol->env.items[%d].id = OBJECT_ID_%s;""" % (counter, obj.upper()))
            fout.write("""\n        pcol->env.items[%d].nr = %d;\n""" % (counter, nr))
            counter += 1
        fout.write("""\n    //end init environment""")

        fout.write("""\n\n    //init global pswarm environment""")
        if (pcol.parentSwarm == None or len(pcol.parentSwarm.global_env) == 0):
            fout.write("""\n        pcol->pswarm.global_env.items[0].id = OBJECT_ID_E;""")
            fout.write("""\n        pcol->pswarm.global_env.items[0].nr = 1;""")
        else:
            counter = 0
            for obj, nr in pcol.parentSwarm.global_env.items():
                fout.write("""\n        pcol->pswarm.global_env.items[%d].id = OBJECT_ID_%s;""" % (counter, obj.upper()))
                fout.write("""\n        pcol->pswarm.global_env.items[%d].nr = %d;""" % (counter, nr))
            counter += 1
        fout.write("""\n    //end init global pswarm environment""")

        for ag_name in pcol.B:
            fout.write("""\n\n    //init agent %s""" % ag_name)
            fout.write("""\n\n    initAgent(&pcol->agents[AGENT_%s], pcol, %d);""" % (ag_name.upper(), len(pcol.agents[ag_name].programs)))

            fout.write("""\n        //init obj multiset""")
            counter = 0;
            for obj, nr in pcol.agents[ag_name].obj.items():
                for i in range(nr):
                    fout.write("""\n        pcol->agents[AGENT_%s].obj.items[%d] = OBJECT_ID_%s;""" % (ag_name.upper(), counter, obj.upper()))
                    counter += 1

            fout.write("""\n\n        //init programs""")
            for prg_nr, prg in enumerate(pcol.agents[ag_name].programs):
                fout.write("""\n\n            initProgram(&pcol->agents[AGENT_%s].programs[%d], pcol->n);""" % (ag_name.upper(), prg_nr))
                fout.write("""\n            //init program %d: < %s >""" % (prg_nr, prg.print()))

                for rule_nr, rule in enumerate(prg):
                    fout.write("""\n                //init rule %d: %s""" % (rule_nr, rule.print(toString=True)) )
                    if (rule.main_type != sim.RuleType.conditional):
                        fout.write("""\n                initRule(&pcol->agents[AGENT_%s].programs[%d].rules[%d], RULE_TYPE_%s, OBJECT_ID_%s, OBJECT_ID_%s, NO_OBJECT, NO_OBJECT);""" % (ag_name.upper(), prg_nr, rule_nr, rule.type.name.upper(), rule.lhs.upper(), rule.rhs.upper()))
                    else:
                        fout.write("""\n                initRule(&pcol->agents[AGENT_%s].programs[%d].rules[%d], RULE_TYPE_CONDITIONAL_%s_%s, OBJECT_ID_%s, OBJECT_ID_%s, OBJECT_ID_%s, OBJECT_ID_%s);""" % (ag_name.upper(), prg_nr, rule_nr, rule.type.name.upper(), rule.alt_type.name.upper(), rule.lhs.upper(), rule.rhs.upper(), rule.alt_lhs.upper(), rule.alt_rhs.upper()))
                fout.write("""\n            //end init program %d""" % prg_nr)
            fout.write("""\n        //end init programs""")

            fout.write("""\n    //end init agent %s""" % ag_name)

        fout.write("""\n}""")
        fout.write("""\n\nvoid lulu_destroy(Pcolony_t *pcol) {
    //destroys all of the subcomponents
    destroyPcolony(pcol);
}""")
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

    logging.info("Generating the instance header (%s)" % (path + ".h"))
    createInstanceHeader(pcol, path + ".h")
    logging.info("Generating the instance source (%s)" % (path + ".c"))
    createInstanceSource(pcol, path)
