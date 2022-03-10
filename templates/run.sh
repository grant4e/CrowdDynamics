#!/bin/bash

#-------------SLURM OPTIONS---------------
#SBATCH -N 1			# One task
#SBATCH -n 1			# One node
#SBATCH -p volta-gpu		# to be run on the Volta GPU partition
#SBATCH --mem=8G		# 8GB of memory
#SBATCH -t 02-00:00:00		# 2 day time limit
#SBATCH --qos gpu_access	# Using GPU quality of service access
#SBATCH --gres=gpu:1		# Requesting the use of 1 GPU device

#--------------ENVIRONMENT----------------
#Replace USERNAME with your onyen, or modify if your python 
# environment is located elsewhere
source /nas/longleaf/home/USERNAME/virtual_envs/HOOMD/bin/activate

#-------------EXECUTABLE------------------
# Name of python script
# Running unbuffered (-u) so outputs are immediately written to file
python -u EXAMPLE.py
