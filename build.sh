#!/bin/bash

COPYFILE_DISABLE=1 tar --exclude-vcs --exclude="__pycache__" --exclude="log" --format ustar -cvzf tools.tar.gz tools-app
