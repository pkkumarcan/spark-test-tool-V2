#!/bin/bash
# Script to run the Agent Visual Feedback Loop GUI using miniconda3 python

# Resolve the absolute path to the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Launch the PyQt6 application using the environment's python interpreter
/home/pkkumar/miniconda3/bin/python agent_gui.py
