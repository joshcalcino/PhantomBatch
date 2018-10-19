import os
import logging as log
import fileinput
from phantombatch import dirhandler


def create_jobscripts(pconf, pbconf, jobscript_filename=None, jobscript_name=None):
    """ This function edits the job script file in each pbconf['dirs'], so that the requested resources are
    allocated for each job, and so each job has a sensible name that reflects the parameter choice of each particular
    simulation. I need to rewrite this so it contains fewer weird optional variables.."""

    if jobscript_filename is None:
        jobscript_filename = pbconf['setup']

    log.info('Creating job scripts for ' + pbconf['name'] + '..')

    jobscript_filename = os.path.join(jobscript_filename + '.jobscript')

    # sim_dirs = [os.path.join(run_dir, pbconf['name'], 'simulations', tmp_dir)
    #             for tmp_dir in pbconf['dirs']]

    jobscript_names = get_jobscript_names(pconf, pbconf, jobscript_name=jobscript_name)
    pbconf['job_names'] = jobscript_names

    index = 0

    for tmp_dir in pbconf['dirs']:
        filename = os.path.join(tmp_dir, jobscript_filename)
        if pbconf['job_scheduler'] == 'slurm':
            edit_slurm_jobscript(pbconf, filename, jobscript_names[index])

        elif pbconf['job_scheduler'] == 'pbs':
            edit_pbs_jobscript(pbconf, filename, jobscript_names[index])

        index += 1

    log.info('Completed.')


def edit_slurm_jobscript(pbconf, jobscript_filename, jobscript_names):
    for line in fileinput.input(jobscript_filename, inplace=True):
        if '#SBATCH --nodes' in line and ('ncpus' in pbconf):
            print(('#SBATCH --nodes=1 --ntasks=' + str(pbconf['ncpus'])).strip())

        elif '#SBATCH --job-name' in line:
            print(('#SBATCH --job-name=' + jobscript_names).strip())

        elif '#SBATCH --mail' in line and 'no_email' in pbconf and pbconf['no_email']:
            print(''.strip())

        elif '#SBATCH --output' in line:
            print(('#SBATCH --output=' + pbconf['setup'] + '.out').strip())

        elif '#SBATCH --time' in line and ('walltime' in pbconf):
            print(('#SBATCH --time=' + pbconf['walltime']).strip())

        elif '#SBATCH --mem' in line and ('memory' in pbconf):
            print(('#SBATCH --mem=' + pbconf['memory']).strip())

        elif 'export OMP_NUM_THREADS' in line and ('ncpus' in pbconf or 'omp_threads' in pbconf):
            if 'omp_threads' in pbconf:
                print(('export OMP_NUM_THREADS=' + str(pbconf['omp_threads'])).strip())
            else:
                print(('export OMP_NUM_THREADS=' + str(pbconf['ncpus'])).strip())

        else:
            print(line.strip())


def edit_pbs_jobscript(pbconf, jobscript_filename, jobscript_names):
    for line in fileinput.input(jobscript_filename, inplace=True):
        if '#PBS -l nodes' in line and ('ncpus' in pbconf):
            print(('#PBS -l nodes=1:ppn=' + str(pbconf['ncpus'])).strip())
            # print('#PBS -A name'.strip())  # Adding this here since my PBS cluster needs an account specified..

        elif '#PBS -N' in line:
            print(('#PBS -N ' + jobscript_names).strip())

        elif '#PBS -A' in line:
            print(('#PBS -A ' + pbconf['user']).strip())

        elif '#PBS -M' in line and ('no_email' in pbconf) and (pbconf['no_email']):
            print('##PBS -M'.strip())

        elif '#PBS -o' in line:
            print(('#PBS -o ' + pbconf['setup'] + '.out').strip())

        elif '#PBS -l walltime' in line and ('walltime' in pbconf):
            print(('#PBS -l walltime=' + pbconf['walltime']).strip())

        elif '#PBS -l mem' in line and ('memory' in pbconf):
            print(('#PBS -l mem=' + pbconf['memory']).strip())

        elif 'export OMP_NUM_THREADS' in line and ('ncpus' in pbconf or 'omp_threads' in pbconf):
            if 'omp_threads' in pbconf:
                print(('export OMP_NUM_THREADS=' + pbconf['omp_threads']).strip())
            else:
                print(('export OMP_NUM_THREADS=' + str(pbconf['ncpus'])).strip())

        else:
            print(line.strip())


def get_jobscript_names(pconf, pbconf, jobscript_name=None):
    """ This function generates a list of job script names given the suite of parameters being used in pconf. """

    jobscript_names = dirhandler.loop_keys_dir(pconf, pbconf)

    if jobscript_name is not None:
        jobscript_names = [jobscript_name + '_' + name for name in jobscript_names]
        return jobscript_names

    if 'short_name' in pbconf and pbconf['short_name'] is not None:
        jobscript_names = [pbconf['short_name'] + '_' + name for name in jobscript_names]

    else:
        jobscript_names = [pbconf['name'] + '_' + name for name in jobscript_names]

    if len(jobscript_names[0]) > 40:
        log.warning('Job names are too long. Consider adding in a \'short_name\' to PhantomBatch config.')

    return jobscript_names
