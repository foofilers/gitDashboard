#!/usr/bin/env python
from os import environ, listdir
from os.path import join, dirname, abspath, exists
import sys

if __name__ == "__main__":
	environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
	from django.core.management import execute_from_command_line
	execute_from_command_line(sys.argv)