#!/bin/bash

# script kills all processes with Grazer in its name

ps aux | grep Grazer | grep -v grep | awk '{print$2}' | xargs kill
