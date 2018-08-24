import argparse
import os
import logging as log
import subprocess
import fileinput
import jobhandler
import util
import time


def dir_func(dirs, string, dict_arr):
    if len(dirs) is not 0:
        dirs = [i+'_' for i in dirs]

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
    """ Create the simulation directories. """

    log.info('Checking if simulation directories exist..')

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    dirs = loop_keys_dir(pconf)

    for dir in dirs:
        cdir = os.path.join(suite_directory, 'simulations', dir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)

    pbconf['dirs'] = dirs
    log.info('Completed.')


def initialise(pconf, pbconf):
    log.info('Initialising ' + pbconf['name'] + '..')

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    if not os.path.exists(suite_directory):
        os.mkdir(suite_directory)

    sims_dir = os.path.join(suite_directory, 'simulations')

    if not os.path.exists(sims_dir):
        os.mkdir(sims_dir)

    initiliase_phantom(pbconf)
    create_dirs(pconf, pbconf)

    for dir in pbconf['dirs']:
        output = subprocess.check_output('cp ' + os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_' +
                                                              pbconf['setup']) + '/* ' + os.path.join(sims_dir, dir),
                                         stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
        util.save_phantom_output(output.rstrip(), pbconf)


def initiliase_phantom(pbconf):
    """ This function will initialise phantom in a special directory called phantom_pbconfg['setup']. We do this so
    that we do not need to compile phantom for each simulation directory. """

    log.info('Checking if Phantom has been compiled for ' + pbconf['name'] + '..')

    if isinstance(pbconf['setup'], list):
        """ Imagining that we can have an array of setups which would be consecutively executed.. Say if we wanted to
        run some gas and then moddump with dust grains.."""

        raise NotImplementedError

    else:
        setup_dir = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'phantom_' + pbconf['setup'])

        if not os.path.exists(setup_dir):
            os.mkdir(setup_dir)

        if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
            log.debug('Setting up Phantom.. This may take a few moments.')

            output = subprocess.check_output(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh') + ' ' +
                                             pbconf['setup'] + ' > ' + os.path.join(setup_dir, 'Makefile'),
                                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            util.save_phantom_output(output.rstrip(), pbconf)

            os.chdir(setup_dir)

            output = subprocess.check_output('make ' + pbconf['make_options'],
                                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            util.save_phantom_output(output.rstrip(), pbconf)

            output = subprocess.check_output('make setup ' + pbconf['make_setup_options'],
                                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            util.save_phantom_output(output.rstrip(), pbconf)

            log.debug('Writing jobscript template.')

            try:
                os.environ['SYSTEM']
                output = subprocess.check_output('make qscript INFILE=' + pbconf['setup'] + '.in' + ' > '
                                                 + pbconf['setup'] + '.jobscript',
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                util.save_phantom_output(output.rstrip(), pbconf)

            except KeyError:
                log.warning('SYSTEM environment variable is not set, jobscript may not be created.')
                log.debug('You should make sure that your SYSTEM variable is defined in the Phantom Makefile.')

                output = subprocess.check_output('make qscript INFILE=' + pbconf['setup']+'.in' + pbconf['make_options']
                                                 + ' > ' + pbconf['setup'] + '.jobscript',
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                util.save_phantom_output(output.rstrip(), pbconf)

            if 'make_moddump_options' in pbconf:
                output = subprocess.check_output('make moddump ' + pbconf['make_moddump_options'],
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                util.save_phantom_output(output.rstrip(), pbconf)

            os.chdir(os.environ['PHANTOM_DATA'])


def setup_from_array(setup_strings, string, dict_arr):
    """ Create strings for the parameter arrays provided in pconf. """

    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    tmp_setup_strings = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])
    print(len(tmp_setup_strings))

    # if setup_strings[]
    #
    # setup_strings = [[setup_strings[i]] + tmp_setup_strings[j] for i in range(0, len(setup_strings))
    #                  for j in range(0, len(tmp_setup_strings))]

    if isinstance(setup_strings[0], list):
        setup_strings = setup_strings * len(dict_arr)
        setup_strings = [setup_strings[i] + [tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]

    else:
        setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]

    # if isinstance(setup_strings[0], list):
    #     setup_strings = setup_strings * len(dict_arr)
    #     [setup_strings[i].extend(tmp_setup_strings[j]) for i in range(0, len(setup_strings)) for j in range(0, len(tmp_setup_strings))]
    #
    # else:
    #     setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
    #                      for j in range(0, len(tmp_setup_strings))]
    print(setup_strings)
    return setup_strings


def get_setup_strings(pconf):
    """ This function creates the directory names for each simulation. """

    setup_strings = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_a':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'm2':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_i':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'alphaSS':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

    return setup_strings


def get_jobscript_names(pconf, pbconf):
    """ This function generates a list of job script names given the suite of parameters being used in pconf. """

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
        log.warning('Job names are too long. Consider adding in a \'short_name\' to phantombatch config.')

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
    if key == 'binary_i':
        return ' ! i, inclination (deg)'
    else:
        return ''


def create_job_scripts(pconf, pbconf):
    """ This function edits the job script file in each pbconf['sim_dir'], so that the requested resources are
    allocated for each job, and so each job has a sensible name that reflects the parameter choice of each particular
    simulation. """

    log.info('Creating job scripts for ' + pbconf['name'] + '..')
    
    jobscript_filename = os.path.join(pbconf['setup'] + '.jobscript')
    sim_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', dir) for dir in pbconf['dirs']]

    jobscript_names = get_jobscript_names(pconf, pbconf)
    pbconf['job_names'] = jobscript_names

    i = 0

    for dir in sim_dirs:
        filename = os.path.join(dir, jobscript_filename)
        for line in fileinput.input(filename, inplace=True):
            if pbconf['job_scheduler'] == 'slurm':
                if '#SBATCH --nodes' in line and ('ncpus' in pbconf):
                    print(('#SBATCH --nodes=1 --ntasks=' + str(pbconf['ncpus'])).rstrip())

                elif '#SBATCH --job-name' in line:
                    print(('#SBATCH --job-name='+jobscript_names[i]).rstrip())

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

            elif pbconf['job_scheduler'] == 'pbs':
                raise NotImplementedError

        i += 1

    log.info('Completed.')


def write_to_setup(new_setup, ref_setup, setup_strings, pconf, index):
    """ Write to the setup file. """

    for line in ref_setup:
        key_added = False
        if line.startswith('# '):
            new_setup.write(line)
        else:
            for key in pconf:
                if isinstance(pconf[key], list):
                    for string in setup_strings[index]:  # loop over the strings that need to be written into setup file
                        # print(string)
                        if (key in line) and (key in string):
                            log.debug('Writing to setup file..')
                            key_added = True
                            new_setup.write(string + write_setup_comment(key) + '\n')

                else:
                    if key in line:
                        new_setup.write(key + ' = ' + str(pconf[key]) + write_setup_comment(key) + '\n')
                        key_added = True

            if not key_added:
                # print(line)
                new_setup.write(line)


def edit_setup_file(new_setup, line, setup_strings, pconf, index):

    for key in pconf:
        if isinstance(pconf[key], list):
            for string in setup_strings[index]:  # loop over the strings that need to be written into setup file
                if (key in line) and (key in string):
                    log.debug('Editing setup file..')
                    new_setup.write(string + write_setup_comment(key) + '\n')

        else:
            print(key)
            if key in line:
                new_setup.write(key + ' = ' + str(pconf[key]) + write_setup_comment(key) + '\n')


def add_planet(new_setup, planet_number, setup_strings, pconf, index):
    """ Add in the several lines that specify planet parameters into new_setup with the user defined values written.
     Certainly a better way to do this.
     """

    with open('setup/planet.setup', 'r') as planet_setup:
        for line in planet_setup:
            line.replace('%', str(planet_number))
            edit_setup_file(new_setup, line, setup_strings, pconf, index)


def add_planets_to_setup(new_setup, setup_strings, pconf, index):
    """ Add planets into the setup file. """

    if 'nplanets' in pconf:
        new_setup.write('\n nplanets = ' + str(pconf['nplanets']) + ' ! number of planets \n')
        for planet_number in range(0 + 1, int(pconf['nplanets'])):
            log.debug("Trying to add in planet " + str(planet_number))
            add_planet(new_setup, planet_number, setup_strings, pconf, index)
    else:
        log.debug("Trying to add in planet")
        new_setup.write('\n nplanets = 1 ! number of planets \n')
        add_planet(new_setup, 1, setup_strings, pconf, index)


def create_setups(pconf, pbconf):
    """ This function will create all of the setup files for the simulation parameters specified in the phantom config
    dictionary, pconf. """

    log.info('Creating the Phantom setup files for ' + pbconf['name'] + '..')
    setup_filename = os.path.join(pbconf['setup'] + '.setup')
    setup_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', dir) for dir in pbconf['dirs']]
    pbconf['sim_dirs'] = setup_dirs
    setup_strings = get_setup_strings(pconf)

    index = 0
    for dir in setup_dirs:
        filename = os.path.join(dir, setup_filename)
        with open(filename, 'w') as new_setup:
            log.debug('Entering ' + filename + '..')
            """ This is where all of the different set ups will need to be defined. """

            if 'binary' in pbconf and pbconf['binary']:
                with open('setup/binary.setup', 'r') as binary_setup:
                    write_to_setup(new_setup, binary_setup, setup_strings, pconf, index)

            if 'setplanets' in pconf and pconf['setplanets']:
                add_planets_to_setup(new_setup, setup_strings, pconf, index)

        index += 1

    log.info('Completed.')


def run_phantom_setup(pbconf):
    """ This function will execute phantomsetup in each directory in pbconf['sim_dirs'] to produce pbconf['name'].in,
     which is the file that is read in by phantom. """

    log.info('Running phantomsetup for each setup file in each simulation for ' + pbconf['name'] + '..')

    setup_dirs = pbconf['sim_dirs']

    for dir in setup_dirs:
        log.debug('Changing directory to ' + dir)
        os.chdir(dir)
        output = subprocess.check_output('./phantomsetup ' + pbconf['setup'], stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True)

        util.check_for_phantom_warnings(output.rstrip())
        util.save_phantom_output(output.rstrip(), pbconf)

    os.chdir(os.environ['PHANTOM_DATA'])
    log.info('Completed.')


def check_phantombatch_complete(pbconf):
    """ Check if all the desired phantombatch jobs have been completed. """

    log.info('Checking if PhantomBatch has completed all requested jobs.')

    current_jobs = jobhandler.check_running_jobs(pbconf)

    if len(pbconf['job_names']) == len(pbconf['submitted_job_names']):

        if len(current_jobs) > 0:
            log.info('There are still jobs to be submitted.')
            return False

        elif len(current_jobs) == 0:
            log.info('All jobs complete.')
            return True

    else:
        log.info('There are still jobs to be submitted.')
        return False


def phantombatch_monitor(pconf, pbconf):

    initialise(pconf, pbconf)
    create_setups(pconf, pbconf)
    # run_phantom_setup(pbconf)
    # create_job_scripts(pconf, pbconf)
    # jobhandler.check_running_jobs(pbconf)
    # jobhandler.run_batch_jobs(pbconf)
    #
    # completed = False
    #
    # while not completed:
    #     jobhandler.run_batch_jobs(pbconf)
    #
    #     log.info('PhantomBatch will now sleep for ' + str(pbconf['sleep_time']) + ' minutes.')
    #     time.sleep(pbconf['sleep_time']*60)
    #
    #     jobhandler.check_completed_jobs(pbconf)
    #
    #     completed = check_phantombatch_complete(pbconf)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Submit batches of Phantom simulations.')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('config', type=str)
    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(level=log.DEBUG)

    else:
        log.basicConfig(level=log.INFO)

    config = util.load_init_config(args.config)

    phantom_config = config['phantom_setup']
    phantombatch_config = config['phantombatch_setup']

    phantombatch_monitor(phantom_config, phantombatch_config)

