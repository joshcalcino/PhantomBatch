import argparse
import os
import json
import logging as log
import subprocess
import fileinput


def load_config(filename):
    with open(filename) as f:
        d = json.load(f)
    f.close()
    return d


def decipher_slurm_output(slurm_output, pbconf):
    tally = 0
    tally_arr = []
    found_dash = False

    for char in slurm_output:
        if char == '-':
            tally += 1
            found_dash = True
        elif char == ' ' and found_dash:
            tally += 1
            tally_arr.append(tally)
            tally = 0
        elif char == '_' and found_dash:
            tally += 1
            tally_arr.append(tally)
            tally = 0
        elif char.isdigit():
            tally += 1
            tally_arr.append(tally)
            break

    job_id_len, name_len, username_len = tally_arr[0], tally_arr[1], tally_arr[2]
    time_len, status_len, queue_len = tally_arr[3], tally_arr[4], tally_arr[5]

    line_length = job_id_len + name_len + username_len + time_len + status_len + queue_len
    slurm_lines = []

    for i in range(0, int(len(slurm_output)/line_length)):
        slurm_lines.append(slurm_output[i*line_length:(i+1)*line_length])

    my_jobs = []
    for line in slurm_lines:
        if pbconf['user'] in line:
            job_id = line[0:job_id_len].rstrip()
            job_name = line[job_id_len:job_id_len+name_len].rstrip()
            username = line[job_id_len+name_len:job_id_len+name_len+username_len].rstrip()
            time = line[job_id_len+name_len+username_len:
                        job_id_len+name_len+username_len+time_len].rstrip()
            status = line[job_id_len+name_len+username_len+time_len:
                          job_id_len+name_len+username_len+time_len+status_len].rstrip()
            queue = line[job_id_len+name_len+username_len+time_len+status_len:line_length].rstrip()
            line_array = [job_id, job_name, username, time, status, queue]
            my_jobs.append(line_array)

    return slurm_lines


def decipher_pbs_output(pbs_output, pbconf):
    return NotImplementedError


def check_running_jobs(pbconf):
    verboseprint('Checking jobs currently running..')

    my_jobs = None
    if pbconf['job_scheduler'] == 'slurm':
        jobs = subprocess.check_output('qstat', stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
        my_jobs = decipher_slurm_output(jobs, pbconf)

    elif pbconf['job_scheduler'] == 'pbs':
        jobs = subprocess.check_output('qstat', stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
        my_jobs = decipher_pbs_output(jobs, pbconf)

    else:
        log.warning('Job scheduler not recognised!')
    return my_jobs
 

def submit_job(pbconf, jobscript):
    verboseprint('Submitting job ')

    if pbconf['job_scheduler'] == 'slurm':
        subprocess.check_output('sbatch ' + jobscript)

    elif pbconf['job_scheduler'] == 'pbs':
        subprocess.check_output('qsub ' + jobscript)

    else:
        log.error('Job scheduler not recognised, cannot submit jobs!')
        log.info('Please use a known job scheduler, or add in your own.')
        exit()


def dir_func(dirs, string, dict_arr):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]
        dirs *= len(dict_arr)

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs


def loop_keys_dir(pconf):
    dirs = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                dirs = dir_func(dirs, 'e', pconf[key])

            if key == 'binary_a':
                dirs = dir_func(dirs, 'a', pconf[key])

            if key == 'm2':
                dirs = dir_func(dirs, 'br', pconf[key])

            if key == 'alphaSS':
                dirs = dir_func(dirs, 'aSS', pconf[key])

            if key == 'binary_i':
                dirs = dir_func(dirs, 'i', pconf[key])

    return dirs


def create_dirs(pconf, pbconf):
    verboseprint('Checking if simulation directories exist..')

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    dirs = loop_keys_dir(pconf)

    for dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', dir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)

    pbconf['dirs'] = dirs
    verboseprint('Completed.')


def initialise(pconf, pbconf):
    verboseprint('Initialising ' + pbconf['name'] + '..')
    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    if not os.path.exists(suite_directory):
        os.mkdir(suite_directory)

    sims_dir = os.path.join(suite_directory, 'simulations')

    if not os.path.exists(sims_dir):
        os.mkdir(sims_dir)

    initiliase_phantom(pbconf)
    create_dirs(pconf, pbconf)

    for dir in pbconf['dirs']:
        os.system('cp ' + os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_'+pbconf['setup']) + '/* '
                  + os.path.join(sims_dir, dir))


def initiliase_phantom(pbconf):
    verboseprint('Checking if Phantom has been compiled for ' + pbconf['name'] + '..')
    if isinstance(pbconf['setup'], list):
        for setup in pbconf['setup']:
            setup_dir = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_'+setup)

            if not os.path.exists(setup_dir):
                os.mkdir(setup_dir)

            if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
                os.system(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh')+' ' +
                          setup + ' > ' + os.path.join(setup_dir, 'Makefile'))
                os.chdir(setup_dir)
                os.system('make '+pbconf['make_options'])
                os.system('make setup '+pbconf['make_setup_options'])

                if pbconf['make_setup_options'] is not None:
                    os.system('make moddump ' + pbconf['make_moddump_options'])

                os.chdir(os.environ['PHANTOM_DATA'])

    else:
        setup_dir = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_' + pbconf['setup'])

        if not os.path.exists(setup_dir):
            os.mkdir(setup_dir)

        if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
            verboseprint('Setting up Phantom.. This may take a few moments.')
            os.system(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh') + ' ' +
                      pbconf['setup'] + ' > ' + os.path.join(setup_dir, 'Makefile'))

            os.chdir(setup_dir)
            os.system('make ' + pbconf['make_options'])
            os.system('make setup ' + pbconf['make_setup_options'])
            verboseprint('Writing jobscript template. '
                         'You should make sure that your SYSTEM variable is defined in Phantom.')
            os.system('make qscript INFILE=' + pbconf['setup']+'.in' + ' > ' + pbconf['setup'] + '.jobscript')

            if 'make_moddump_options' in pbconf:
                os.system('make moddump ' + pbconf['make_moddump_options'])

            os.chdir(os.environ['PHANTOM_DATA'])


def setup_from_array(setup_strings, string, dict_arr):
    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    setup_strings = setup_strings * len(dict_arr)

    tmp_setup_strings = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])
    setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                     for j in range(0, len(tmp_setup_strings))]
    return setup_strings


def get_setup_strings(pconf):
    setup_strings = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_a':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'm2':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'alphaSS':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_i':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

    return setup_strings


def get_jobscript_names(pconf, pbconf):
    jobscript_names = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                jobscript_names = dir_func(jobscript_names, 'e', pconf[key])

            if key == 'binary_a':
                jobscript_names = dir_func(jobscript_names, 'a', pconf[key])

            if key == 'm2':
                jobscript_names = dir_func(jobscript_names, 'br', pconf[key])

            if key == 'alphaSS':
                jobscript_names = dir_func(jobscript_names, 'aSS', pconf[key])

            if key == 'binary_i':
                jobscript_names = dir_func(jobscript_names, 'i', pconf[key])

    if 'short_name' in pbconf and pbconf['short_name'] is not None:
        jobscript_names = [pbconf['short_name'] + '_' + name for name in jobscript_names]

    else:
        jobscript_names = [pbconf['name'] + '_' + name for name in jobscript_names]

    if len(jobscript_names[0]) > 16:
        log.warning('Job names are quite long. Consider adding in a \'short_name\' to phantombatch config.')

    return jobscript_names
    

def write_setup_comment(key):
    if key == 'np':
        return ' ! number of gas particles'
    if key == 'dist_unit':
        return ' ! distance unit (e.g. au,pc,kpc,0.1pc)'
    if key == 'primary_mass':
        return ' ! primary mass'
    if key == 'binary_a':
        return ' ! binary semi-major axis'
    if key == 'binary_e':
        return ' ! binary eccentricity'


def create_job_scripts(pconf, pbconf):
    verboseprint('Creating job scripts for ' + pbconf['name'] + '..')
    
    jobscript_filename = os.path.join(pbconf['setup'] + '.jobscript')
    sim_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', dir) for dir in pbconf['dirs']]

    jobscript_names = get_jobscript_names(pconf, pbconf)

    i = 0
    for dir in sim_dirs:
        filename = os.path.join(dir, jobscript_filename)
        for line in fileinput.input(filename, inplace=True):
            if pbconf['job_scheduler'] == 'slurm':
                if '#SBATCH --nodes' in line and 'ncpus' in pbconf:
                    print('#SBATCH --nodes=1 --ntasks=' + pbconf['ncpus'])

                if '#SBATCH --job-name' in line:
                    print('#SBATCH --job-name='+jobscript_names[i])

                if '#SBATCH --output' in line:
                    print('#SBATCH --output=' + pbconf['setup'] + '.out')

                if '#SBATCH --time' in line and 'walltime' in pbconf:
                    print('#SBATCH --time=' + pbconf['walltime'])

                if '#SBATCH --mem' in line and 'memory' in pbconf:
                    print('#SBATCH --mem=' + pbconf['memory'])

                if 'export OMP_NUM_THREADS' in line and ('ncpus' in pbconf or 'omp_threads' in pbconf):
                    if 'omp_threads' in pbconf:
                        print('export OMP_NUM_THREADS=' + pbconf['omp_threads'])
                    else:
                        print('export OMP_NUM_THREADS=' + pbconf['ncpus'])

            elif pbconf['job_scheduler'] == 'pbs':
                raise NotImplementedError

            i += 1

    verboseprint('Completed.')


def create_setups(pconf, pbconf):
    verboseprint('Creating the Phantom setup files for ' + pbconf['name'] + '..')
    setup_filename = os.path.join(pbconf['setup'] + '.setup')
    setup_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', dir) for dir in pbconf['dirs']]
    pbconf['sim_dirs'] = setup_dirs
    setup_strings = get_setup_strings(pconf)

    i = 0
    for dir in setup_dirs:
        filename = os.path.join(dir, setup_filename)
        with open(filename, 'w') as new_setup:
            verboseprint('Entering ' + filename + '..')
            if 'binary' in pbconf:
                if pbconf['binary']:
                    binary_setup = open('data/setup/binary.setup', 'r')
                    for line in binary_setup:
                        key_added = False
                        for key in pconf:
                            if isinstance(pconf[key], list):
                                for string in setup_strings[i]:
                                    if key in line and key in string:
                                        verboseprint('Writing to setup file..')
                                        new_setup.write(string + write_setup_comment(key) + '\n')
                                        key_added = True
                            else:
                                key_added = False
                                if key in line:
                                    new_setup.write(key + ' = ' + str(pconf[key]) + write_setup_comment(key) + '\n')
                                    key_added = True

                        if not key_added:
                            new_setup.write(line)

            new_setup.close()
            i += 1

    verboseprint('Completed.')


def run_phantom_setup(pbconf):
    verboseprint('Running phantomsetup for each setup file in each simulation for ' + pbconf['name'] + '..')
    setup_dirs = pbconf['sim_dirs']

    for dir in setup_dirs:
        os.chdir(dir)
        os.system('./phantomsetup ' + pbconf['setup'])

    os.chdir(os.environ['PHANTOM_DATA'])
    verboseprint('Completed.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Submit batches of Phantom simulations.')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('config', type=str)
    args = parser.parse_args()

    verboseprint = print if args.verbose else lambda *a, **k: None

    config = load_config(args.config)

    phantom_config = config['phantom_setup']
    phantombatch_config = config['phantombatch_setup']

    initialise(phantom_config, phantombatch_config)
    # create_setups(phantom_config, phantombatch_config)
    # run_phantom_setup(phantombatch_config)
    check_running_jobs(phantombatch_config)
