#!/usr/bin/env python3

"""Module to generate Snakemake's rule-command dict and feed it to Shellcheck"""

import re
import tempfile
from subprocess import Popen
from os import remove

def run_snakemake_detailed_summary(out_file):
    try:
        with open(out_file, "w") as f_out:
            Popen(
                args=["snakemake", "--detailed-summary", "--dryrun"],
                stdout=f_out
            )
    except Exception as e:
        print("An exception occured: ", e)


def _merge_commands_by_tab(command_list):
    '''Join arguments splited when parsing because contained a tab'''
    return '\t'.join(command_list)


def _remove_multiple_whitespace(command_str):
    '''Remove unnecesary whitespace'''
    return re.sub(' +',' ', command_str)


def parse_rules_and_commands(detailed_summary_file):
    """Get dict {rule: command} properly parsed

    multiple spaces into one, tabs as tabs
    """
    with open(detailed_summary_file, "r") as f_in:

        # Initialize
        rule_dict = {}

        # skip lines 1 (message) and 2 (header)
        _ = f_in.readline()
        _ = f_in.readline()

        # Parse the main chunk
        for line in f_in:

            output_file, date, rule, version, log_files, input_files, *shellcmd, status, plan = line.split("\t")

            if rule == '-':
                continue

            shellcmd = _merge_commands_by_tab(shellcmd)
            shellcmd = _remove_multiple_whitespace(shellcmd)

            rule_dict[rule] = shellcmd

    return rule_dict


def compose_functions(rule_dict, file_out):
    """Compose file to be read by shellcheck

    Format is
    command  # rule_name
    """
    with open(file_out, "w") as f_out:
        f_out.write("#!/usr/bin/env bash \n\n")
        for rule, command in rule_dict.items():
            f_out.write(f"{command}\t# {rule}\n\n")


def run_shellcheck(file):
    """Run shellcheck over file"""
    with open(file, "r") as f_in:
        Popen(["shellcheck", file])



def snakelint(snakefile="Snakefile"):
    """Lint snakefile"""

    temp_summary = tempfile.mkstemp()
    temp_commands = tempfile.mkstemp()

    run_snakemake_detailed_summary(temp_file)
    rule_to_command = parse_rules_and_commands(temp_file)
    compose_functions(rule_to_command, temp_commands)
    run_shellcheck(temp_commands)

    remove(temp_summary)
    remove(temp_commands)
