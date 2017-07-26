import logging
from lulu_pcol_sim import sim
import sys # for argv
import time # for strftime()
import natsort # for natural sorting of alphabet (needed because the order of objects has to be B_0, B_1, B_2, B_10, B_11 and not B_0, B_1, B_10, B_11, ...)

def writeMultisetObj(objSet, capacity):
    """Write agent multiset structure (multiset_obj_t) initialization from a collections.Counter object

    :objSet: collections.Counter object
    :capacity: P colony capacity
    :returns: String representation (in C) of the agent multiset"""

    result = """
        .items = (uint8_t[%d]) {""" % capacity
    for obj, nr in objSet.items():
        for i in range(nr):
            result += "OBJECT_ID_%s, " % obj.upper()
    result +="""},
        .size = %d,""" % capacity

    return result
# end writeMultisetObj()

# TODO initialize entire multiset with NO_OBJECT, except for objects that are in envSet
def writeMultisetEnv(envSet, nr_A):
    """Write environment multiset structure (multiset_env_t) initialization from a collections.Counter object

    :envSet: collections.Counter object
    :nr_A: P colony alphabet size
    :returns: String representation (in C) of the environment multiset"""

    result = """
    .items = (multiset_env_item_t[%d]) {""" % nr_A
    #for obj, nr in envSet.items():
    for obj in pcol.A:
        if (envSet[obj] > 0):
            result += """
        {.id = OBJECT_ID_%s, .nr = %d},""" % (obj.upper(), envSet[obj])
        else:
            result += """
        {.id = NO_OBJECT, .nr = 0},"""
    result +="""
    },
    .size = %d,""" % nr_A

    return result
# end writeMultisetObj()

def writeRule(rule):
    """Write rule structure (Rule_t) from Rule object

    :rule: Rule object
    :returns: String representation (in C) of the rule"""


    if (rule.main_type != sim.RuleType.conditional):
        result = """
            .type = %s,
            .lhs = OBJECT_ID_%s,
            .rhs = OBJECT_ID_%s,
            .alt_lhs = NO_OBJECT,
            .alt_rhs = NO_OBJECT,""" % (
            "RULE_TYPE_%s" % rule.type.name.upper(),
            rule.lhs.upper(),
            rule.rhs.upper(),
        )
    else:
        result = """
            .type = %s,
            .lhs = OBJECT_ID_%s,
            .rhs = OBJECT_ID_%s,
            .alt_lhs = OBJECT_ID_%s,
            .alt_rhs = OBJECT_ID_%s,""" % (
            "RULE_TYPE_CONDITIONAL_%s_%s" % (rule.type.name.upper(), rule.alt_type.name.upper()),
            rule.lhs.upper(),
            rule.rhs.upper(),
            rule.alt_lhs.upper(),
            rule.alt_rhs.upper()
        )

    return result
# end writeRule()

def writeProgram(program):
    """Write program structure (Program_t) from Program object

    :program: Program object
    :returns: String representation (in C) of the program"""

    result = """
    /* %s */
    .nr_rules = %d,
    .exec_rule_numbers = (rule_exec_option_t [%d]) {
    """ % (program.print(), len(program), len(program))
    for i in range(len(program)):
        result +="""
        RULE_EXEC_OPTION_NONE,
        """

    result += """
    },
    .rules = (const Rule_t[%d]) {
    """ % len(program)

    for rule in program:
        result +="""
        {%s
        },""" % writeRule(rule)

    result +="""
    }"""

    return result
# end writeProgram()

def writeAgent(agent, capacity):
    """Write agent structure (Agent_t) from Agent object

    :agent: Agent object
    :capacity: P colony capacity
    :returns: String representation (in C) of the agent"""

    result = """
    .nr_programs = %d,
    .chosenProgramNr = -1,
    .init_program_nr = 0,
    .pcolony = &pcol,
    .obj = {%s
    },
    .programs = (Program_t[%d]) {
    """ % (
        len(agent.programs),
        writeMultisetObj(agent.obj, capacity),
        len(agent.programs)
    )

    for program in agent.programs:
        result +="""
        {
        %s
        },""" % ("\n" + " " * 8).join(writeProgram(program).split("\n")) # indents programs by 8 spaces

    result +="""
    }"""

    return result
# end writeAgent()

def writePcolony(pcol):
    """Write P colony structure (Pcolony_t) from Pcolony object

    :pcol: P colony object
    :returns: String representation (in C) of the P colony"""

    result = """
Pcolony_t pcol = {
    .nr_A = %d,
    .nr_agents = %d,
    .n = %d,
    .env = {%s
    },
    """ % (
        len(pcol.A),
        len(pcol.agents),
        pcol.n,
        # env
        ("\n" + " " * 4).join(writeMultisetEnv(pcol.env, len(pcol.A)).split("\n")),
    )

    if (pcol.parentSwarm == None):
        result +="""
    .pswarm = 0,
    """
    else:
        result +="""
    .pswarm = {
        .global_env = {%s
        },
        .in_global_env = {%s
        },
        .out_global_env = {%s
        },
    },

        """ % (
            # global_env
            ("\n" + " " * 8).join(writeMultisetEnv(pcol.parentSwarm.global_env, len(pcol.A)).split("\n")),
            # in_global_env
            ("\n" + " " * 8).join(writeMultisetEnv(pcol.parentSwarm.in_global_env, len(pcol.A)).split("\n")),
            # out_global_env
            ("\n" + " " * 8).join(writeMultisetEnv(pcol.parentSwarm.out_global_env, len(pcol.A)).split("\n")),
        )
    result += """.agents = (Agent_t[%d]) {
    """ % len(pcol.agents)
    for agentName, agent in pcol.agents.items():
        result += """
        [AGENT_%s] = {""" % agentName.upper()
        result += ("\n" + " " * 8).join(writeAgent(agent, pcol.n).split("\n"))
        result += """
        },"""

    result +="""
    }"""
    result +="""
};"""

    return result
# end writePcolony()

def createInstanceHeader(pcol, path, originalFilename, nr_robots):
    """Create an instance of the passed P colony that is written as a header in C at the given path

    :pcol: The pcolony object that was read by lulu_pcol_sim
    :path: The path to the instance.h that will be written"""

    needsWildcardExpansion = False

    with open(path, "w") as fout:
        fout.write("""// vim:filetype=c
/**
 * @file lulu_instance.h
 * @brief Lulu P colony simulator internal structure corresponding to the P colony defined in '%s'.
 * In this header we define the structure of the Pcolony that will power the simulated robot
 * This file was generated automatically by lulu_c.py on %s
 * @author Andrei G. Florea
 * @author Catalin Buiu
 * @date 2016-02-29
 */
#ifndef LULU_INSTANCE_H
#define LULU_INSTANCE_H

#include "lulu.h" """ % (originalFilename, time.strftime("%d %h %Y at %H:%M")))

        fout.write("\nenum objects {")
        # extend wildcard objects to _0, _1, ... _n where n = nr_robots
        for a in pcol.A[:]:
            # both $ and $id wildcards need extended objects
            if ("_W_ALL" in a or "_W_ID" in a):
                needsWildcardExpansion = True
                logging.debug("Extending %s wildcarded object" % a)
                # construct extended object list
                extension = [a.replace("W_ID", "%d" % i).replace("W_ALL", "%d" % i) for i in range(nr_robots)]
                # if this extension has not been previously added
                if (not set(extension).issubset(set(pcol.A))):
                    #add the extetendet object list to the alphabet
                    pcol.A.extend(extension)

        # sort objects naturally
        pcol.A = natsort.natsorted(pcol.A, key=lambda x: x.replace('_W_ID', '/').replace('_W_ALL', '.'))
        repr(pcol.A)
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

        if (needsWildcardExpansion):
            fout.write("""\n#define NEEDING_WILDCARD_EXPANSION //this ensures that the wildcard expansion code is included""")

        if ("motion" in pcol.B):
            fout.write("\n#define USING_AGENT_MOTION //this ensures that the code associated with the MOTION agent is included in Lulu_kilobot")
        if ("led_rgb" in pcol.B):
            fout.write("\n#define USING_AGENT_LED_RGB //this ensures that the code associated with the LED_RGB agent is included in Lulu_kilobot")
        if ("msg_distance" in pcol.B):
            fout.write("\n#define USING_AGENT_MSG_DISTANCE //this ensures that the code associated with the MSG_DISTANCE agent is included in Lulu_kilobot")
        if ("timer" in pcol.B):
            fout.write("\n#define USING_AGENT_TIMER //this ensures that the code associated with the TIMER agent is included in Lulu_kilobot")

        fout.write("\n")
        if ("d_all" in pcol.A):
            fout.write("""\n#define USING_OBJECT_D_ALL //this ensures that the code associated with processing D_ALL objects is included in Lulu_kilobot""")
        if ("d_next" in pcol.A):
            fout.write("""\n#define USING_OBJECT_D_NEXT //this ensures that the code associated with processing D_NEXT objects is included in Lulu_kilobot""")

        # check if using {IN,OUT}_EXTEROCEPTIVE rules (<I=> or <=O>)
        using_in_out_exteroceptive_rules = False
        for agent in pcol.agents.values():
            for program in agent.programs:
                for rule in program:
                    if (rule.type == sim.RuleType.in_exteroceptive or rule.type == sim.RuleType.out_exteroceptive or
                            rule.alt_type == sim.RuleType.in_exteroceptive or rule.alt_type == sim.RuleType.out_exteroceptive):
                        using_in_out_exteroceptive_rules = True
                        break;
        if (using_in_out_exteroceptive_rules):
            fout.write("""\n#define USING_IN_OUT_EXTEROCEPTIVE_RULES //this ensures that the code associated with processing IN_EXTEROCEPTIVE (<I=>) or OUT_EXTEROCEPTIVE (<=O>) rules is included in Lulu_kilobot""")

        fout.write("""\n\n//if building Pcolony simulator for PC
#ifdef PCOL_SIM
    //define array of names for objects and agents for debug
    extern char* objectNames[];
    extern char* agentNames[];
#endif

extern Pcolony_t pcol;

/**
 * @brief The smallest kilo_uid from the swarm (is set in instance.c by lulu_c.py)
 */
extern const uint16_t smallest_robot_uid;

/**
 * @brief The number of robots that make up the swarm (is set in instance.c by lulu_c.py)
 */
extern const uint16_t nr_swarm_robots;""");

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

#ifdef NEEDING_WILDCARD_EXPANSION
    /**
     * @brief Expands and replaces wildcarded objects with the appropriate objects
     * Objects that end with _W_ID are replaced with _i where i is the the id of the robot, provided with my_id parameter
     *
     * @param pcol The pcolony where the replacements will take place
     * @param my_id The kilo_uid of the robot
     * @return The symbolic id that corresponds to this robot (my_id - smallest_robot_uid)
     */
    uint16_t expand_pcolony(Pcolony_t *pcol, uint16_t my_id);
#endif
#endif""")
# end createInstanceHeader()

def createInstanceSource(pcol, path, nr_robots, smallest_robot_id):
    """Create an instance of the passed P colony that is written as a source file in C at the given path

    :pcol: The pcolony object that was read by lulu_pcol_sim
    :path: The path to the instance.c that will be written"""

    # prevent alphabet related bugs by including e and f objects in alphabet
    if ("e" not in pcol.A):
        pcol.A.append("e")
    if ("f" not in pcol.A):
        pcol.A.append("f")

    with open(path + ".c", "w") as fout:
        fout.write("""#include "%s.h"

#ifdef NEEDING_WILDCARD_EXPANSION
    #include "wild_expand.h"
#endif

#ifdef PCOL_SIM""" % path.split("/")[-1]) #only filename

        fout.write("""\n    char* objectNames[] = {[NO_OBJECT] = "no_object", """)
        for obj in pcol.A:
            fout.write("""[OBJECT_ID_%s] = "%s", """ % (obj.upper(), obj))

        fout.write("""};
    char* agentNames[] = {""")
        for ag_name in pcol.B:
            fout.write("""[AGENT_%s] = "%s", """ % (ag_name.upper(), ag_name))
        fout.write("""};
#endif

//the smallest kilo_uid from the swarm
const uint16_t smallest_robot_uid = %d;
//the number of robots that make up the swarm
const uint16_t nr_swarm_robots = %d;

void lulu_init(Pcolony_t *pcol) {""" % (smallest_robot_id, nr_robots) )

        ## call initPcolony()
        #fout.write("""\n    //init Pcolony with alphabet size = %d, nr of agents = %d, capacity = %d
    #initPcolony(pcol, %d, %d, %d);""" % (len(pcol.A), len(pcol.B), pcol.n,  len(pcol.A), len(pcol.B), pcol.n))
        #fout.write("""\n    //Pcolony.alphabet = %s""" % pcol.A)

        ## init environment
        #fout.write("""\n\n    //init environment""")
        #counter = 0;
        #for obj, nr in pcol.env.items():
            ##replace %id and * with $id and $ respectively

            #fout.write("""\n        pcol->env.items[%d].id = OBJECT_ID_%s;""" % (counter, obj.upper()))
            #fout.write("""\n        pcol->env.items[%d].nr = %d;\n""" % (counter, nr))
            #counter += 1
        #fout.write("""\n    //end init environment""")

        #fout.write("""\n\n    //init global pswarm environment""")
        #if (pcol.parentSwarm == None or len(pcol.parentSwarm.global_env) == 0):
            #fout.write("""\n        pcol->pswarm.global_env.items[0].id = OBJECT_ID_E;""")
            #fout.write("""\n        pcol->pswarm.global_env.items[0].nr = 1;""")
        #else:
            #counter = 0
            #for obj, nr in pcol.parentSwarm.global_env.items():
                ##replace %id and * with $id and $ respectively

                #fout.write("""\n        pcol->pswarm.global_env.items[%d].id = OBJECT_ID_%s;""" % (counter, obj.upper()))
                #fout.write("""\n        pcol->pswarm.global_env.items[%d].nr = %d;""" % (counter, nr))
                #counter += 1
        #fout.write("""\n    //end init global pswarm environment""")

        #fout.write("""\n\n    //init INPUT global pswarm environment""")
        #if (pcol.parentSwarm == None or len(pcol.parentSwarm.in_global_env) == 0):
            #fout.write("""\n        pcol->pswarm.in_global_env.items[0].id = OBJECT_ID_E;""")
            #fout.write("""\n        pcol->pswarm.in_global_env.items[0].nr = 1;""")
        #else:
            #counter = 0
            #for obj, nr in pcol.parentSwarm.in_global_env.items():
                ##replace %id and * with $id and $ respectively

                #fout.write("""\n        pcol->pswarm.in_global_env.items[%d].id = OBJECT_ID_%s;""" % (counter, obj.upper()))
                #fout.write("""\n        pcol->pswarm.in_global_env.items[%d].nr = %d;""" % (counter, nr))
                #counter += 1
        #fout.write("""\n    //end init INPUT global pswarm environment""")

        #fout.write("""\n\n    //init OUTPUT global pswarm environment""")
        #if (pcol.parentSwarm == None or len(pcol.parentSwarm.out_global_env) == 0):
            #fout.write("""\n        pcol->pswarm.out_global_env.items[0].id = OBJECT_ID_E;""")
            #fout.write("""\n        pcol->pswarm.out_global_env.items[0].nr = 1;""")
        #else:
            #counter = 0
            #for obj, nr in pcol.parentSwarm.out_global_env.items():
                ##replace %id and * with $id and $ respectively

                #fout.write("""\n        pcol->pswarm.out_global_env.items[%d].id = OBJECT_ID_%s;""" % (counter, obj.upper()))
                #fout.write("""\n        pcol->pswarm.out_global_env.items[%d].nr = %d;""" % (counter, nr))
                #counter += 1
        #fout.write("""\n    //end init OUTPUT global pswarm environment""")

        #for ag_name in pcol.B:
            #fout.write("""\n\n    //init agent %s""" % ag_name)
            ##fout.write("""\n\n    initAgent(&pcol->agents[AGENT_%s], pcol, %d);""" % (ag_name.upper(), len(pcol.agents[ag_name].programs)))
            #fout.write("""\n\n    initAgent(&pcol->agents[AGENT_%s], pcol, %d);""" % (ag_name.upper(), getNrOfProgramsAfterExpansion(pcol.agents[ag_name], nr_robots- 1)))

            #fout.write("""\n        //init obj multiset""")
            #counter = 0;
            #for obj, nr in pcol.agents[ag_name].obj.items():
                ##replace %id and * with $id and $ respectively

                #for i in range(nr):
                    #fout.write("""\n        pcol->agents[AGENT_%s].obj.items[%d] = OBJECT_ID_%s;""" % (ag_name.upper(), counter, obj.upper()))
                    #counter += 1

            #fout.write("""\n\n        //init programs""")
            #for prg_nr, prg in enumerate(pcol.agents[ag_name].programs):
                #fout.write("""\n\n            initProgram(&pcol->agents[AGENT_%s].programs[%d], %d);""" % (ag_name.upper(), prg_nr, getNrOfRulesWithoutRepetitions(prg)))
                #fout.write("""\n            //init program %d: < %s >""" % (prg_nr, prg.print()))

                #rule_index = 0
                #for rule_nr, rule in enumerate(prg):
                    ## skip rules that contain identical operands and thus have no effect
                    #if (rule.lhs == rule.rhs and rule.lhs == 'e' and rule.main_type != sim.RuleType.conditional):
                        #continue

                    #fout.write("""\n                //init rule %d: %s""" % (rule_nr, rule.print(toString=True)) )
                    #if (rule.main_type != sim.RuleType.conditional):
                        #fout.write("""\n                initRule(&pcol->agents[AGENT_%s].programs[%d].rules[%d], RULE_TYPE_%s, OBJECT_ID_%s, OBJECT_ID_%s, NO_OBJECT, NO_OBJECT);""" % (ag_name.upper(), prg_nr, rule_index, rule.type.name.upper(), rule.lhs.upper(), rule.rhs.upper()))
                    #else:
                        #fout.write("""\n                initRule(&pcol->agents[AGENT_%s].programs[%d].rules[%d], RULE_TYPE_CONDITIONAL_%s_%s, OBJECT_ID_%s, OBJECT_ID_%s, OBJECT_ID_%s, OBJECT_ID_%s);""" % (ag_name.upper(), prg_nr, rule_index, rule.type.name.upper(), rule.alt_type.name.upper(), rule.lhs.upper(), rule.rhs.upper(), rule.alt_lhs.upper(), rule.alt_rhs.upper()))

                    ##increase rule_index
                    #rule_index += 1
                #fout.write("""\n            //end init program %d
            #pcol->agents[AGENT_%s].init_program_nr++;""" % (prg_nr, ag_name.upper()))
            #fout.write("""\n        //end init programs""")

            #fout.write("""\n    //end init agent %s""" % ag_name)

        fout.write("""\n}""")

        fout.write(writePcolony(pcol))

        fout.write("""\n\nvoid lulu_destroy(Pcolony_t *pcol) {
    //destroys all of the subcomponents
    destroyPcolony(pcol);
}""")
        fout.write("""\n
#ifdef NEEDING_WILDCARD_EXPANSION
uint16_t expand_pcolony(Pcolony_t *pcol, uint16_t my_id) {
    //used for a cleaner iteration through the P colony
    //instead of using agents[i] all of the time, we use just agent
    Agent_t *agent;
""")

        fout.write("""\n    uint8_t obj_with_id[] = {""")
        obj_with_id_size = 0
        for obj in pcol.A:
            if ("_W_ID" in obj):
                fout.write("OBJECT_ID_%s, " % obj.upper())
                obj_with_id_size += 1
        fout.write("""};
    uint8_t obj_with_id_size = %d;""" % (obj_with_id_size))

        fout.write("""\n    uint8_t obj_with_any[] = {""")
        obj_with_any_size = 0
        is_obj_with_any_followed_by_id = []
        for i, obj in enumerate(pcol.A):
            if (obj.endswith("_W_ALL")):
                fout.write("OBJECT_ID_%s, " % obj.upper())
                # if we are at least 2 objects before the end of the list
                if (i < len(pcol.A) - 1):
                    # check if this _$ wildcarded object is followed by a _$id object
                    if ("_W_ID" in pcol.A[i+1]):
                        is_obj_with_any_followed_by_id.append(1)
                    else:
                        is_obj_with_any_followed_by_id.append(0)
                else:
                    # this (_$) object is the last one in the list
                    is_obj_with_any_followed_by_id.append(0)
                obj_with_any_size += 1
        fout.write("""};
    uint8_t obj_with_any_size = %d;
    uint8_t is_obj_with_any_followed_by_id[] = {%s};""" % (obj_with_any_size,
        str(is_obj_with_any_followed_by_id).replace("[", "").replace("]", "")))

        fout.write("""\n\n    uint16_t my_symbolic_id = my_id - smallest_robot_uid;

    //replace W_ID wildcarded objects with the object corresponding to the symbolic id
    //  e.g.: B_W_ID -> B_0 for my_symbolic_id = 0
    replacePcolonyWildID(pcol, obj_with_id, obj_with_id_size, my_symbolic_id);

    //expand each obj_with_any[] element into nr_swarm_robots objects except my_symbolic id.
    //  e.g.: B_W_ALL -> B_0, B_2 for nr_swarm_robots = 3 and my_symbolic_id = 1
    expandPcolonyWildAny(pcol, obj_with_any, is_obj_with_any_followed_by_id, obj_with_any_size, my_symbolic_id, nr_swarm_robots);

    return my_symbolic_id;
}
#endif""")

# end createInstanceHeader()

def getNrOfProgramsAfterExpansion(agent, suffixListSize):
    """Returns the final number of programs that will result after all programs (within this agent)
    with * wildcard objects have been expanded

    :agent: The agent whose programs will checked
    :suffixListSize: The number of programs that result after expanding a program such as < X_* -> e, e->X_* >
    if suffixListSize = 2 then we obtain 2 new programs, < X_0 - > e ... > and < X_1 -> e ...> that replace the original one
    :returns: The final number of programs that will result after expansion """

    check_for_any_wild = [x.endswith("_W_ALL") for x in agent.colony.A]
    any_wild_objects = []
    for i, val in enumerate(check_for_any_wild):
        if (val):
            any_wild_objects.append(agent.colony.A[i])

    counter = 0

    logging.info("wild_ANY objects = %s" % any_wild_objects)

    for program in agent.programs:
        wild_exists_in_program = False
        for rule in program:
            for obj in any_wild_objects:
                if (obj == rule.lhs or obj == rule.rhs or obj == rule.alt_lhs or obj == rule.alt_rhs):
                    wild_exists_in_program = True
                    logging.warning("wild_ANY object %s exists in program %s rule %s" % (obj, program.print(), rule.print(toString=True)))
                    break;
        # end for rule in program
        if (wild_exists_in_program):
                counter += suffixListSize

    return counter + len(agent.programs)
# end getNrOfProgramsAfterExpansion()

def getNrOfRulesWithoutRepetitions(prg):
    """Returns the number of rules from this program that do not consist of operand repetitions such as e->e
    Note: conditional rules are included without checking because it is assumed that they were introduce to check a condition
    :returns: Number of rules that have lhs different from rhs"""

    nr_rules = len(prg)
    for rule in prg:
        if (rule.main_type != sim.RuleType.conditional):
            if (rule.lhs == rule.rhs and rule.lhs == "e"):
                nr_rules -= 1

    return nr_rules
# end getNrOfRulesWithoutRepetitions()

#   MAIN
if (__name__ == "__main__"):
    logLevel = logging.INFO

    if ('--debug' in sys.argv):
        logLevel = logging.DEBUG

    try:
        import colorlog # colors log output

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

        colorlog.basicConfig(stream = sys.stdout, level = logLevel)
        stream = colorlog.root.handlers[0]
        stream.setFormatter(formatter);

    # colorlog not available
    except ImportError:
        logging.basicConfig(format='%(levelname)s:%(message)s', level = logLevel)
    if (len(sys.argv) < 2):
        logging.error("Expected input file path as parameter")
        exit(1)

    if (len(sys.argv) < 3):
        logging.error("Expected the path to the file (without extensions) that will be generated")
        exit(1)

    if (len(sys.argv) < 4):
        logging.error("Expected the number of robots that make up the swarm")
        exit(1)

    if (len(sys.argv) < 5):
        logging.error("Expected the minimum robot id (kilo_uid) as the last parameter")
        exit(1)



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
        nr_robots = int(sys.argv[3])
        min_robot_id = int(sys.argv[4])
        path = sys.argv[5]

    else:
        pcol = pObj

        nr_robots = int(sys.argv[2])
        min_robot_id = int(sys.argv[3])
        path = sys.argv[4]

    #replacing wildcarded marks * and %id with $ and $id respectively
    #in alphabet, all multisets and programs
    for i, val in enumerate(pcol.A):
        pcol.A[i] = val.replace("%id", "W_ID").replace("*", "W_ALL")

    for key in pcol.env:
        # if key contains wildcards
        if ("*" in key or "%id" in key):
            #copy value at wildcarded key at new $ key
            pcol.env[key.replace("%id", "W_ID").replace("*", "W_ALL")] = pcol.env[key];
            #delete the * key
            del pcol.env[key]

    #if this pcolony is part of swarm
    if (pcol.parentSwarm != None):
        for key in pcol.parentSwarm.global_env:
            # if key contains wildcards
            if ("*" in key or "%id" in key):
                #copy value at wildcarded key at new $ key
                pcol.parentSwarm.global_env[key.replace("%id", "W_ID").replace("*", "W_ALL")] = pcol.parentSwarm.global_env[key];
                #delete the * key
                del pcol.parentSwarm.global_env[key]

    for ag_name in pcol.B:
        for key in pcol.agents[ag_name].obj:
            # if key contains wildcards
            if ("*" in key or "%id" in key):
                #copy value at wildcarded key at new $ key
                pcol.agents[ag_name].obj[key.replace("%id", "W_ID").replace("*", "W_ALL")] = pcol.agents[ag_name].obj[key];
                #delete the * key
                del pcol.agents[ag_name].obj[key]
        # end for key in obj
        for prg_nr, prg in enumerate(pcol.agents[ag_name].programs):
            for rule_nr, rule in enumerate(prg):
                rule.lhs = rule.lhs.replace("%id", "W_ID").replace("*", "W_ALL")
                rule.rhs = rule.rhs.replace("%id", "W_ID").replace("*", "W_ALL")
                rule.alt_lhs = rule.alt_lhs.replace("%id", "W_ID").replace("*", "W_ALL")
                rule.alt_rhs = rule.alt_rhs.replace("%id", "W_ID").replace("*", "W_ALL")

    logging.info("Generating the instance header (%s)" % (path + ".h"))
    createInstanceHeader(pcol, path + ".h", sys.argv[1].split("/")[-1], nr_robots)
    logging.info("Generating the instance source (%s)" % (path + ".c"))
    createInstanceSource(pcol, path, nr_robots, min_robot_id)

    pcol.print_colony_components()
