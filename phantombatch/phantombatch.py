import os
import logging as log
import subprocess
from phantombatch import setuphandler, jobscripthandler, dirhandler, jobhandler, util
import time


__all__ = ["PhantomBatch"]


class PhantomBatch(object):

    def __init__(self, config_filename, verbose=False):

        #  Set up the level of verbosity
        if verbose:
            log.basicConfig(level=log.DEBUG)
        else:
            log.basicConfig(level=log.info)

        #  Load in config file
        config = util.load_init_config(config_filename)

        self.pconf = config['phantom_setup']
        self.pbconf = config['phantom_batch_setup']

    def initialise(self):
        log.info('Initialising ' + self.pbconf['name'] + '..')

        suite_directory = os.path.join(os.environ['PHANTOM_DATA'], self.pbconf['name'])

        if not os.path.exists(suite_directory):
            os.mkdir(suite_directory)

        sims_dir = os.path.join(suite_directory, 'simulations')

        if not os.path.exists(sims_dir):
            os.mkdir(sims_dir)

        self.initiliase_phantom()
        dirhandler.create_dirs(self.pconf, self.pbconf)

        for dir in self.pbconf['dirs']:
            output = subprocess.check_output('cp ' + os.path.join(os.environ['PHANTOM_DATA'], self.pbconf['name'], 'phantom_' +
                                                                  self.pbconf['setup']) + '/* ' + os.path.join(sims_dir, dir),
                                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            util.save_phantom_output(output.rstrip(), self.pbconf)

    def initiliase_phantom(self):
        """ This function will initialise phantom in a special directory called phantom_pbconfg['setup']. We do this so
        that we do not need to compile phantom for each simulation directory. """

        log.info('Checking if Phantom has been compiled for ' + self.pbconf['name'] + '..')

        if isinstance(self.pbconf['setup'], list):
            """ Imagining that we can have an array of setups which would be consecutively executed.. Say if we wanted to
            run some gas and then moddump with dust grains.."""

            raise NotImplementedError

        else:
            setup_dir = os.path.join(os.environ['PHANTOM_DATA'], self.pbconf['name'], 'phantom_' + self.pbconf['setup'])

            if not os.path.exists(setup_dir):
                os.mkdir(setup_dir)

            if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
                log.debug('Setting up Phantom.. This may take a few moments.')

                output = subprocess.check_output(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh') + ' ' +
                                                 self.pbconf['setup'] + ' > ' + os.path.join(setup_dir, 'Makefile'),
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                util.save_phantom_output(output.rstrip(), self.pbconf)

                os.chdir(setup_dir)

                output = subprocess.check_output('make ' + self.pbconf['make_options'],
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                util.save_phantom_output(output.rstrip(), self.pbconf)

                output = subprocess.check_output('make setup ' + self.pbconf['make_setup_options'],
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                util.save_phantom_output(output.rstrip(), self.pbconf)

                log.debug('Writing jobscript template.')

                try:
                    os.environ['SYSTEM']
                    output = subprocess.check_output('make qscript INFILE=' + self.pbconf['setup'] + '.in' + ' > '
                                                     + self.pbconf['setup'] + '.jobscript',
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                    util.save_phantom_output(output.rstrip(), self.pbconf)

                except KeyError:
                    log.warning('SYSTEM environment variable is not set, jobscript may not be created.')
                    log.debug('You should make sure that your SYSTEM variable is defined in the Phantom Makefile.')

                    output = subprocess.check_output('make qscript INFILE=' + self.pbconf['setup']+'.in' + self.pbconf['make_options']
                                                     + ' > ' + self.pbconf['setup'] + '.jobscript',
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                    util.save_phantom_output(output.rstrip(), self.pbconf)

                if 'make_moddump_options' in self.pbconf:
                    output = subprocess.check_output('make moddump ' + self.pbconf['make_moddump_options'],
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                    util.save_phantom_output(output.rstrip(), self.pbconf)

                os.chdir(os.environ['PHANTOM_DATA'])

    def add_planet_to_setup(self, new_setup, planet_number, setup_strings):
        """ Add in the several lines that specify planet parameters into new_setup with the user defined values written.
         Certainly a better way to do this.
         """

        with open('../setup/planet.setup', 'r') as planet_setup:
            for line in planet_setup:
                setuphandler.edit_setup_file(new_setup, line.replace('%', str(planet_number)),
                                             setup_strings, self.pconf)

    def add_planets(self, new_setup, setup_strings):
        """ Add planets into the setup file. """

        if 'nplanets' in self.pconf:
            new_setup.write('\n nplanets = ' + str(self.pconf['nplanets']) + ' ! number of planets \n')
            for planet_number in range(1, int(self.pconf['nplanets'])+1):
                log.debug("Trying to add in planet " + str(planet_number))
                self.add_planet_to_setup(new_setup, planet_number, setup_strings)

        else:
            log.debug("Trying to add in planet")
            new_setup.write('\n nplanets = 1 ! number of planets \n')
            self.add_planet_to_setup(new_setup, 1, setup_strings)

    def create_setups(self):
        """ This function will create all of the setup files for the simulation parameters specified in the phantom config
        dictionary, pconf. It does not matter if this is adding in a messy fashion, as phantomsetup solves it for us. """

        log.info('Creating the Phantom setup files for ' + self.pbconf['name'] + '..')
        setup_filename = os.path.join(self.pbconf['setup'] + '.setup')
        setup_dirs = [os.path.join(os.environ['PHANTOM_DATA'], self.pbconf['name'], 'simulations', tmp_dir)
                      for tmp_dir in self.pbconf['dirs']]

        self.pbconf['sim_dirs'] = setup_dirs
        setup_strings = setuphandler.get_setup_strings(self.pconf)

        index = 0
        for tmp_dir in setup_dirs:
            filename = os.path.join(tmp_dir, setup_filename)
            with open(filename, 'w') as new_setup:
                log.debug('Entering ' + filename + '..')
                """ This is where all of the different set ups will need to be defined. """

                if 'binary' in self.pbconf and self.pbconf['binary']:
                    with open('../setup/binary.setup', 'r') as binary_setup:
                        setuphandler.write_to_setup(new_setup, binary_setup, setup_strings[index], self.pconf)

                if 'setplanets' in self.pconf and self.pconf['setplanets']:
                    self.add_planets(new_setup, setup_strings[index])

            index += 1

        log.info('Completed.')

    def run_phantom_setup(self):
        """ This function will execute phantomsetup in each directory in pbconf['sim_dirs'] to produce pbconf['name'].in,
         which is the file that is read in by phantom. """

        log.info('Running phantomsetup for each setup file in each simulation for ' + self.pbconf['name'] + '..')

        setup_dirs = self.pbconf['sim_dirs']

        for dir in setup_dirs:
            log.debug('Changing directory to ' + dir)
            os.chdir(dir)
            output = subprocess.check_output('./phantomsetup ' + self.pbconf['setup'], stderr=subprocess.STDOUT,
                                             universal_newlines=True, shell=True)

            util.check_for_phantom_warnings(output.rstrip())
            util.save_phantom_output(output.rstrip(), self.pbconf)

        os.chdir(os.environ['PHANTOM_DATA'])
        log.info('Completed.')

    def check_phantombatch_complete(self):
        """ Check if all the desired phantombatch jobs have been completed. """

        log.info('Checking if PhantomBatch has completed all requested jobs.')

        current_jobs = jobhandler.check_running_jobs(self.pbconf)

        if len(self.pbconf['job_names']) == len(self.pbconf['submitted_job_names']):

            if len(current_jobs) > 0:
                log.info('There are still jobs to be submitted.')
                return False

            elif len(current_jobs) == 0:
                log.info('All jobs complete.')
                return True

        else:
            log.info('There are still jobs to be submitted.')
            return False

    def phantombatch_monitor(self):

        self.initialise()
        self.create_setups()
        self.run_phantom_setup()
        jobscripthandler.create_job_scripts(self.pconf, self.pbconf)
        jobhandler.run_batch_jobs(self.pbconf)

        completed = False

        while not completed:
            jobhandler.run_batch_jobs(self.pbconf)

            log.info('PhantomBatch will now sleep for ' + str(self.pbconf['sleep_time']) + ' minutes.')
            time.sleep(self.pbconf['sleep_time']*60)

            jobhandler.check_completed_jobs(self.pbconf)

            completed = self.check_phantombatch_complete()

