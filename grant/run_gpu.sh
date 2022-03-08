#!/bin/bash
#SBATCH --qos gpu_access                    # quality of service
#SBATCH --gres=gpu:1                        # I want one gpus
#SBATCH --partition=gpu                     # partition to run on
#SBATCH --time=11-00:00                     # time (D-HH:MM)

# setopt shwordsplit # make zsh behave like bash
# setopt KSH_ARRAYS # make zsh behave like bash; array index starts at 0

echo $1
echo $2
echo $3
echo $4
echo $5
echo $6
echo $7
echo $8
echo $9
echo ${10}
echo ${11}
echo ${12}
echo ${13}
echo ${14}
echo ${15}

inFile=$1  #Python template file 
hoomdPath=$2  #Path to HOOMD (I hard-coded this into python file)
gsdPath=$3  #Path you want to save the file (I manipulate this manually in python file)
pa=$4 #Particle A activity
pb=$5 #Particle B activity
xa=$6 #Particle fraction of type A
ep=$7 #Softness of both particles
seed1=$8 #Random seed 1
seed2=$9 #Random seed 2
seed3=${10} #Random seed 3
seed4=${11} #Random seed 4
seed5=${12} #Random seed 5
myFrame=${13} #current frame

python $inFile $hoomdPath $gsdPath $pa $pb $xa $ep $phi $seed1 $seed2 $seed3 $seed4 $seed5 $myFrame