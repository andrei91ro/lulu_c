# Lulu input file to C code conversion script (PROGMEM initialization branch), written in Python3

This script is used to generate compilable C code representations of [Lulu](https://github.com/andrei91ro/lulu_pcol_sim) input files, that can be used to run the [C version of Lulu/initialize\_progmem](https://github.com/andrei91ro/lulu_pcol_sim_c/tree/initialize_progmem).

# Requirements
* [Lulu P/XP colony simulator](https://github.com/andrei91ro/lulu_pcol_sim)
* Optionally [colorlog](https://pypi.python.org/pypi/colorlog), that if installed will print messages in colours according to the level of importance.


# Command line usage
`python3 lulu_c.py INPUT_FILE.lulu  OUTPUT_FILE_NAME  NR_ROBOTS  MIN_ROBOT_ID  [OPTIONS]`

where:

* `INPUT_FILE.lulu`: path to the Lulu input file
* `OUTPUT_FILE_NAME`: path to the C language output file. Note that the file name must be specified without extensions. The .c and .h extensions will be added automatically
* `NR_ROBOTS`: Total number of robots. Can be safely specified as `0` because this value is no longer in use
* `MIN_ROBOT_ID`: The minimum `kilo_uid` value from the swarm of Kilobots. In simulation, this value is typically `0`. Also, if the intended target is not a Kilobot, then this value can also be `0`
* `[OPTIONS]` can be:
    * `--debug`: increase verbosity by showing DEBUG messages

# Authors
Andrei George Florea, [Cătălin Buiu](http://catalin.buiu.net)

[Department of Automatic Control And Systems Engineering](http://acse.pub.ro),

Politehnica University of Bucharest

Bucharest, Romania.
