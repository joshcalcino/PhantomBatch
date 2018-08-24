import argparse
import os
import logging as log
import subprocess
import jobhandler
import jobscripthandler
import dirhandler
import setuphandler
import util
import time


def initialise(pconf, pbconf):
    log.info('Initialising ' + pbconf['name'] + '..')

    suite_directory = os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'])

    if not os.path.exists(suite_directory):
        os.mkdir(suite_directory)

    sims_dir = os.path.join(suite_directory, 'simulations')

    if not os.path.exists(sims_dir):
        os.mkdir(sims_dir)

    initiliase_phantom(pbconf)
    dirhandler.create_dirs(pconf, pbconf)

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


def add_planet_to_setup(new_setup, planet_number, setup_strings, pconf, index):
    """ Add in the several lines that specify planet parameters into new_setup with the user defined values written.
     Certainly a better way to do this.
     """

    with open('setup/planet.setup', 'r') as planet_setup:
        for line in planet_setup:
            setuphandler.edit_setup_file(new_setup, line.replace('%', str(planet_number)), setup_strings, pconf, index)


def add_planets(new_setup, setup_strings, pconf, index):
    """ Add planets into the setup file. """

    if 'nplanets' in pconf:
        new_setup.write('\n nplanets = ' + str(pconf['nplanets']) + ' ! number of planets \n')
        for planet_number in range(1, int(pconf['nplanets'])+1):
            log.debug("Trying to add in planet " + str(planet_number))
            add_planet_to_setup(new_setup, planet_number, setup_strings, pconf, index)
    else:
        log.debug("Trying to add in planet")
        new_setup.write('\n nplanets = 1 ! number of planets \n')
        add_planet_to_setup(new_setup, 1, setup_strings, pconf, index)


def create_setups(pconf, pbconf):
    """ This function will create all of the setup files for the simulation parameters specified in the phantom config
    dictionary, pconf. It does not matter if this is adding in a messy fashion, as phantomsetup solves it for us. """

    log.info('Creating the Phantom setup files for ' + pbconf['name'] + '..')
    setup_filename = os.path.join(pbconf['setup'] + '.setup')
    setup_dirs = [os.path.join(os.environ['PHANTOM_DATA'], pbconf['name'], 'simulations', dir) for dir in pbconf['dirs']]
    pbconf['sim_dirs'] = setup_dirs
    setup_strings = setuphandler.get_setup_strings(pconf)

    index = 0
    for dir in setup_dirs:
        filename = os.path.join(dir, setup_filename)
        with open(filename, 'w') as new_setup:
            log.debug('Entering ' + filename + '..')
            """ This is where all of the different set ups will need to be defined. """

            if 'binary' in pbconf and pbconf['binary']:
                with open('setup/binary.setup', 'r') as binary_setup:
                    setuphandler.write_to_setup(new_setup, binary_setup, setup_strings, pconf, index)

            if 'setplanets' in pconf and pconf['setplanets']:
                add_planets(new_setup, setup_strings, pconf, index)

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
    run_phantom_setup(pbconf)
    jobscripthandler.create_job_scripts(pconf, pbconf)
    jobhandler.run_batch_jobs(pbconf)

    completed = False

    while not completed:
        jobhandler.run_batch_jobs(pbconf)

        log.info('PhantomBatch will now sleep for ' + str(pbconf['sleep_time']) + ' minutes.')
        time.sleep(pbconf['sleep_time']*60)

        jobhandler.check_completed_jobs(pbconf)

        completed = check_phantombatch_complete(pbconf)


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

