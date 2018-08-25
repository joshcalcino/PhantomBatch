import os
import logging as log
import fileinput
from phantombatch import dirhandler


def create_job_scripts(pconf, pbconf):
    """ This function edits the job script file in each pbconf['sim_dir'], so that the requested resources are
    allocated for each job, and so each job has a sensible name that reflects the parameter choice of each particular
    simulation. """

    log.info('Creating job scripts for ' + pbconf['name'] + '..')

    job_script_filename = os.path.join(pbconf['setup'] + '.jobscript')
    sim_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', tmp_dir)
                for tmp_dir in pbconf['dirs']]

    job_script_names = get_job_script_names(pconf, pbconf)
    pbconf['job_names'] = job_script_names

    index = 0

    for tmp_dir in sim_dirs:
        filename = os.path.join(tmp_dir, job_script_filename)
        if pbconf['job_scheduler'] == 'slurm':
            edit_slurm_jobscript(pbconf, filename, job_script_names[index])

        elif pbconf['job_scheduler'] == 'pbs':
            edit_pbs_jobscript(pbconf, filename, job_script_names[index])

        index += 1

    log.info('Completed.')


def edit_slurm_jobscript(pbconf, job_script_filename, job_script_names):
    for line in fileinput.input(job_script_filename, inplace=True):
        if '#SBATCH --nodes' in line and ('ncpus' in pbconf):
            print(('#SBATCH --nodes=1 --ntasks=' + str(pbconf['ncpus'])).rstrip())

        elif '#SBATCH --job-name' in line:
            print(('#SBATCH --job-name=' + job_script_names).rstrip())

        elif '#SBATCH --mail' in line and 'no_email' in pbconf and pbconf['no_email']:
            print(''.rstrip())

        elif '#SBATCH --output' in line:
            print(('#SBATCH --output=' + pbconf['setup'] + '.out').rstrip())

        elif '#SBATCH --time' in line and ('walltime' in pbconf):
            print(('#SBATCH --time=' + pbconf['walltime']).rstrip())

        elif '#SBATCH --mem' in line and ('memory' in pbconf):
            print(('#SBATCH --mem=' + pbconf['memory']).rstrip())

        elif 'export OMP_NUM_THREADS' in line and ('ncpus' in pbconf or 'omp_threads' in pbconf):
            if 'omp_threads' in pbconf:
                print(('export OMP_NUM_THREADS=' + pbconf['omp_threads']).rstrip())
            else:
                print(('export OMP_NUM_THREADS=' + pbconf['ncpus']).rstrip())

        else:
            print(line.rstrip())


def edit_pbs_jobscript(pbconf, job_script_filename, job_script_names):
    for line in fileinput.input(job_script_filename, inplace=True):
        if '#PBS -l nodes' in line and ('ncpus' in pbconf):
            print(('#PBS -l nodes=1:ppn=' + str(pbconf['ncpus'])).rstrip())

        elif '#PBS -N' in line:
            print(('#PBS -N ' + job_script_names).rstrip())

        elif '#PBS -M' in line and ('no_email' in pbconf) and (pbconf['no_email']):
            print('##PBS -M'.rstrip())

        elif '#PBS -o' in line:
            print(('#PBS -o ' + pbconf['setup'] + '.out').rstrip())

        elif '#PBS -l walltime' in line and ('walltime' in pbconf):
            print(('#PBS -l walltime=' + pbconf['walltime']).rstrip())

        elif '#PBS -l mem' in line and ('memory' in pbconf):
            print(('#PBS -l mem=' + pbconf['memory']).rstrip())

        elif 'export OMP_NUM_THREADS' in line and ('ncpus' in pbconf or 'omp_threads' in pbconf):
            if 'omp_threads' in pbconf:
                print(('export OMP_NUM_THREADS=' + pbconf['omp_threads']).rstrip())
            else:
                print(('export OMP_NUM_THREADS=' + pbconf['ncpus']).rstrip())

        else:
            print(line.rstrip())


def get_job_script_names(pconf, pbconf):
    """ This function generates a list of job script names given the suite of parameters being used in pconf. """

    job_script_names = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                job_script_names = dirhandler.dir_func(job_script_names, 'e', pconf[key])

            if key == 'binary_a':
                job_script_names = dirhandler.dir_func(job_script_names, 'a', pconf[key])

            if key == 'm2':
                job_script_names = dirhandler.dir_func(job_script_names, 'br', pconf[key])

            if key == 'alphaSS':
                job_script_names = dirhandler.dir_func(job_script_names, 'aSS', pconf[key])

            if key == 'binary_i':
                job_script_names = dirhandler.dir_func(job_script_names, 'i', pconf[key])

    if 'short_name' in pbconf and pbconf['short_name'] is not None:
        job_script_names = [pbconf['short_name'] + '_' + name for name in job_script_names]

    else:
        job_script_names = [pbconf['name'] + '_' + name for name in job_script_names]

    if len(job_script_names[0]) > 16:
        log.warning('Job names are too long. Consider adding in a \'short_name\' to phantombatch config.')

    return job_script_names
