#!/bin/bash
#SBATCH -n 1                    # Number of cores
#SBATCH -N 1                    # Ensure that all cores are on one machine
#SBATCH -t 0-48:00              # Runtime in D-HH:MM
#SBATCH -p serial_requeue       # Partition to submit to
#SBATCH --mem=32000             # Memory pool for all cores (see also --mem-per-cpu)
#SBATCH -o hostname_%j.out      # File to which STDOUT will be written
#SBATCH -e hostname_%j.err      # File to which STDERR will be written
#SBATCH --mail-type=ALL         # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=wxue@college.harvard.edu # Email to which notifications will be sent
 
# Load python
module load python/2.7.11-fasrc01

# Activate conda env
source activate ody

# Run script
python dim.py
