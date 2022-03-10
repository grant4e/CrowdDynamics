#!/bin/bash

#SBATCH -N 1
#SBATCH -n 1
#SBATCH -p volta-gpu
#SBATCH --mem=8G
#SBATCH -t 02-00:00:00
#SBATCH --qos gpu_access
#SBATCH --gres=gpu:1

# Replace USERNAME below with your onyen, and potentially modify 
# this path if your HOOMD env is located/named differently

source /nas/longleaf/home/grant4e/virtual_envs/HOOMD/bin/activate
which python
python -u epsilonKBT_wall.py
