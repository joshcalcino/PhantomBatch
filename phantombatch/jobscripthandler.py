import os
import shutil
import logging as log
import fileinput
from phantombatch import dirhandler


def create_jobscripts(pbconf, jobscript_filename=None, jobscript_name=None):
    """ This function edits the job script file in each pbconf['dirs'], so that the requested resources are
    allocated for each job, and so each job has a sensible name that reflects the parameter choice of each particular
    simulation. I need to rewrite this so it contains fewer weird optional variables.."""

    log.info('Creating job scripts for ' + pbconf['name'] + '..')

    if jobscript_filename is not None:
        print("I will not be editing anything in the jobscript file except the name")
        job_names = get_jobscript_names(pbconf)
        for i, tmp_dir in enumerate(pbconf['sim_dirs']):
            new_filename = os.path.join(tmp_dir, jobscript_filename)
            shutil.copy(jobscript_filename, new_filename)
            log.debug('Jobscript filename..')
            log.debug(new_filename)
            log.debug('Current directory..')
            log.debug(os.environ['PWD'])
            if pbconf['job_scheduler'] == 'slurm':
                edit_slurm_jobscript_name(pbconf, new_filename, job_names[i])

            elif pbconf['job_scheduler'] == 'pbs':
                edit_pbs_jobscript_name(pbconf, new_filename, job_names[i])
        return job_names
    else:
        jobscript_filename = pbconf['setup']
        jobscript_filename = os.path.join(jobscript_filename + '.jobscript')

    jobscript_names = get_jobscript_names(pbconf, jobscript_name=jobscript_name)

    for i, tmp_dir in enumerate(pbconf['sim_dirs']):
        filename = os.path.join(tmp_dir, jobscript_filename)
        log.debug('Jobscript filename..')
        log.debug(filename)
        log.debug('Current directory..')
        log.debug(os.environ['PWD'])
        if pbconf['job_scheduler'] == 'slurm':
            edit_slurm_jobscript(pbconf, filename, jobscript_names[i])

        elif pbconf['job_scheduler'] == 'pbs':
            edit_pbs_jobscript(pbconf, filename, jobscript_names[i])

    log.info('Completed.')

    return job_names

def edit_slurm_jobscript_name(pbconf, jobscript_filename, jobscript_names):
    for line in fileinput.input(jobscript_filename, inplace=True):
        if '#SBATCH --job-name' in line:
            print(('#SBATCH --job-name=' + jobscript_names).strip())
        else:
            print(line.strip())

def edit_pbs_jobscript_name(pbconf, jobscript_filename, jobscript_names):
    for line in fileinput.input(jobscript_filename, inplace=True):
        if '#PBS -N' in line:
            print(('#PBS -N ' + jobscript_names).strip())
        else:
            print(line.strip())


def edit_slurm_jobscript(pbconf, jobscript_filename, jobscript_name):
    for line in fileinput.input(jobscript_filename, inplace=True):
        if '#SBATCH --nodes' in line and ('ncpus' in pbconf):
            print(('#SBATCH --nodes=1 --ntasks=' + str(pbconf['ncpus'])).strip())

        elif '#SBATCH --job-name' in line:
            print(('#SBATCH --job-name=' + jobscript_name).strip())

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


def edit_pbs_jobscript(pbconf, jobscript_filename, jobscript_name):
    account_added = False
    for line in fileinput.input(jobscript_filename, inplace=True):
        if '#PBS -l nodes' in line and ('ncpus' in pbconf):
            print(('#PBS -l nodes=1:ppn=' + str(pbconf['ncpus'])).strip())

        elif '#PBS -N' in line:
            print(('#PBS -N ' + jobscript_name).strip())

        elif ('#PBS -A' in line) and not account_added:
            account_added = True
            print(('#PBS -A ' + pbconf['account']).strip())

        elif ('account' in pbconf) and not account_added:
            account_added = True
            print(('#PBS -A ' + pbconf['account']).strip())  # Adding this here since my PBS cluster needs an account specified..

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


def get_jobscript_names(pbconf, jobscript_name=None):
    """ This function generates a list of job script names given the suite of parameters being used in pconf. """

    jobscript_names = pbconf['setup_names']

    if jobscript_name is not None:
        jobscript_names = [jobscript_name + '_' + name for name in jobscript_names]
        return jobscript_names

    if 'short_name' in pbconf and pbconf['short_name'] is not None:
        jobscript_names = [pbconf['short_name'] + '_' + name for name in jobscript_names]

    else:
        jobscript_names = [pbconf['name'] + '_' + name for name in jobscript_names]

    log.debug('Printing joscript_names from get_jobscript_names')
    log.debug(jobscript_names)

    if len(jobscript_names[0]) > 40:
        log.warning('Job names are too long. Consider adding in a \'short_name\' to PhantomBatch config.')

    return jobscript_names
