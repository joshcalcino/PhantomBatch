import os
import shutil
import logging as log
import subprocess
from phantombatch import setuphandler, jobscripthandler, dirhandler, jobhandler, splashhandler, util
import time
import atexit


__all__ = ["PhantomBatch"]


class PhantomBatch(object):

    def __init__(self, config_filename, verbose=False, terminate_at_exit=True, run_dir=None, fresh_start=False):
        #  Set up the level of verbosity
        if verbose:
            log.basicConfig(level=log.DEBUG)
        else:
            log.basicConfig(level=log.INFO)

        #  Terminate jobs if PhantomBatch is interrupted
        if terminate_at_exit:
            log.info('PhantomBatch will cancel all jobs on exiting')
            atexit.register(self.terminate_jobs_at_exit)

        #  Load in config file
        self.config = util.load_init_config(config_filename)

        self.pconf = self.config['phantom_setup']
        self.pbconf = self.config['phantom_batch_setup']

        if fresh_start:
            log.info('Removing previous run directory..')
            if os.path.exists(self.pbconf['name']):
                shutil.rmtree(self.pbconf['name'])

        # check if a saved phantombatch configuration file already exists, overwrite current if it does
        if os.path.isfile(os.path.join(self.pbconf['name'], self.pbconf['name'] + '_pbconf.pkl')):
            pbconf_tmp = util.load_config(self.pbconf)
            for key in self.pbconf:
                if key in pbconf_tmp and (self.pbconf[key] != pbconf_tmp[key]):
                    pbconf_tmp[key] = self.pbconf[key]
                    log.warning('key ' + key + ' has changed since your last run of PhantomBatch.')
                elif key not in pbconf_tmp:
                    pbconf_tmp[key] = self.pbconf[key]

            self.pbconf = pbconf_tmp

        self.run_splash = False

        # Set up splashbatch if it is going to be used
        if 'splash_batch_setup' in self.config:
            self.run_splash = True
            self.sbconf = splashhandler.get_full_splash_config(self.pbconf, self.config['splash_batch_setup'])

            if 'no_splash' in self.sbconf and self.sbconf['no_splash'] is True:
                # Add this in so it is easier to control splash usage without having to remove lines from config file
                self.run_splash = False
        print(self.run_splash)
        # Get running directory, use current directory if run_dir not specified
        if run_dir is not None:
            self.run_dir = run_dir
        else:
            self.run_dir = os.environ['PWD']

        # Save run_dir in the PhantomBatch config dict
        self.pbconf['run_dir'] = self.run_dir

    def terminate_jobs_at_exit(self):
        jobhandler.cancel_all_submitted_jobs(self.pbconf)

    def initialise(self):
        log.info('Initialising ' + self.pbconf['name'] + '..')

        suite_directory = os.path.join(self.run_dir, self.pbconf['name'])

        #  Check if the directory already exists
        if not os.path.exists(suite_directory):
            os.mkdir(suite_directory)

        sims_dir = os.path.join(suite_directory, 'simulations')

        if not os.path.exists(sims_dir):
            os.mkdir(sims_dir)

        self.initiliase_phantom()
        dirhandler.create_dirs(self.pconf, self.pbconf, 'simulations')

        for tmp_dir in self.pbconf['dirs']:
            output = subprocess.check_output('cp ' + os.path.join(self.run_dir, self.pbconf['name'],
                                                                  'phantom_' + self.pbconf['setup']) + '/* ' +
                                             os.path.join(sims_dir, tmp_dir), stderr=subprocess.STDOUT,
                                             universal_newlines=True, shell=True)

            util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

    def initiliase_phantom(self):
        """ This function will initialise phantom in a special directory called phantom_pbconfg['setup']. We do this so
        that we do not need to compile phantom for each simulation directory. """

        log.info('Checking if Phantom has been compiled for ' + self.pbconf['name'] + '..')

        if isinstance(self.pbconf['setup'], list):
            """ Imagining that we can have an array of setups which would be consecutively executed.. Say if we wanted to
            run some gas and then moddump with dust grains.."""
            log.error('You added a list for setup options. This functionality has not been implemented yet.')
            raise NotImplementedError

        else:
            setup_dir = os.path.join(self.run_dir, self.pbconf['name'], 'phantom_' + self.pbconf['setup'])

            if not os.path.exists(setup_dir):
                os.mkdir(setup_dir)

            if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
                log.info('Setting up Phantom.. This may take a few moments.')

                output = subprocess.check_output(os.path.join(os.environ['PHANTOM_DIR'], 'scripts', 'writemake.sh') +
                                                 ' ' + self.pbconf['setup'] + ' > ' +
                                                 os.path.join(setup_dir, 'Makefile'),
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                os.chdir(setup_dir)

                if 'make_options' in self.pbconf and (len(self.pbconf['make_options']) is not 0):
                    log.debug('Compiling with pbconf[\'make_setup\']')
                    output = subprocess.check_output('make ' + self.pbconf['make_options'],
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                else:
                    output = subprocess.check_output('make',
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                if 'make_setup_options' in self.pbconf and (len(self.pbconf['make_setup_options']) is not 0):
                    log.debug('Compiling with pbconf[\'make_setup_options\']')

                    output = subprocess.check_output('make setup ' + self.pbconf['make_setup_options'],
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                else:
                    output = subprocess.check_output('make setup',
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                log.debug('Writing jobscript template.')

                try:
                    sys_environ = os.environ['SYSTEM']
                    output = subprocess.check_output('make qscript INFILE=' + self.pbconf['setup'] + '.in ' +
                                                     'SYSTEM=' + sys_environ + ' > '
                                                     + self.pbconf['setup'] + '.jobscript',
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                    util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                except KeyError:
                    log.warning('SYSTEM environment variable is not set, jobscript may not be created.')
                    log.info('You should make sure that your SYSTEM variable is defined in the Phantom Makefile.')
                    log.info('This will make sure that the correct Fortran compiler and system job scheduler '
                             'is selected by make qscript.')

                    output = subprocess.check_output('make qscript INFILE=' + self.pbconf['setup']+'.in ' +
                                                     self.pbconf['make_options'] + ' > ' +
                                                     self.pbconf['setup'] + '.jobscript',
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                    util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                if 'make_moddump_options' in self.pbconf:
                    output = subprocess.check_output('make moddump ' + self.pbconf['make_moddump_options'],
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                    util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                os.chdir(self.run_dir)

    def create_setups(self):
        """ This function will create all of the setup files for the simulation parameters specified in the phantom config
        dictionary, pconf. It does not matter if this is adding in a messy fashion, as phantomsetup solves it for us."""

        log.info('Creating the Phantom setup files for ' + self.pbconf['name'] + '..')
        setup_filename = os.path.join(self.pbconf['setup'] + '.setup')
        setup_dirs = [os.path.join(self.run_dir, self.pbconf['name'], 'simulations', tmp_dir)
                      for tmp_dir in self.pbconf['dirs']]

        self.pbconf['sim_dirs'] = setup_dirs
        setup_strings = setuphandler.get_setup_strings(self.pconf, self.pbconf)

        #  index keeps track setup_strings go into correct setup file
        index = 0
        for tmp_dir in setup_dirs:
            #  This is where all of the different setups will be defined
            filename = os.path.join(tmp_dir, setup_filename)

            if self.pbconf['setup'] == 'disc':
                if 'binary' in self.pbconf and self.pbconf['binary']:
                    setuphandler.set_up_binary(filename, setup_strings[index], self.pconf)
                else:
                    setuphandler.set_up_disc(filename, setup_strings[index], self.pconf)

            if 'setplanets' in self.pconf and (self.pconf['setplanets'] == 1):
                setuphandler.add_planets(filename, setup_strings[index], self.pconf)

            if 'add_dust' in self.pbconf and self.pbconf['add_dust']:
                setuphandler.add_dust(filename, setup_strings[index], self.pconf)

            index += 1

        log.info('Completed.')

    def run_phantom_setup(self):
        """ This function will execute phantomsetup in each directory in pbconf['sim_dirs'] to produce pbconf['name'].in,
         which is the file that is read in by phantom. """

        log.info('Running phantomsetup for each setup file in each simulation for ' + self.pbconf['name'] + '..')

        setup_dirs = self.pbconf['sim_dirs']

        for tmp_dir in setup_dirs:
            log.debug('Changing directory to ' + tmp_dir)
            os.chdir(tmp_dir)
            output = subprocess.check_output('./phantomsetup ' + self.pbconf['setup'], stderr=subprocess.STDOUT,
                                             universal_newlines=True, shell=True)

            util.check_for_phantom_warnings(output.rstrip())
            util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

        os.chdir(self.run_dir)
        log.info('Completed.')

    def check_phantombatch_complete(self):
        """ Check if all the desired phantombatch jobs have been completed. """

        log.info('Checking if PhantomBatch has completed all requested jobs.')

        current_jobs = jobhandler.check_running_jobs(self.pbconf)
        jobhandler.check_completed_jobs(self.pbconf)

        log.debug('Printing \'job_names\'')
        log.debug(self.pbconf['job_names'])
        log.debug('\'submitted_job_names\'')
        log.debug(self.pbconf['submitted_job_names'])
        log.debug('\'completed_jobs\'')
        log.debug(self.pbconf['completed_jobs'])

        if len(self.pbconf['job_names']) == len(self.pbconf['completed_jobs']):

            if len(current_jobs) > 0:
                log.info('There are still jobs to be submitted.')
                return False

            elif len(current_jobs) == 0:
                log.info('All jobs complete.')
                return True

        else:
            log.info('There are still jobs to be completed.')
            return False

    def phantombatch_monitor(self):
        """ The default monitor for PhantomBatch. This monitor will set up Phantom and PhantomBatch, create simulations,
        submit and monitor jobs until completion. """

        self.initialise()
        self.create_setups()
        self.run_phantom_setup()
        jobscripthandler.create_jobscripts(self.pconf, self.pbconf)
        jobhandler.check_running_jobs(self.pbconf)
        jobhandler.run_batch_jobs(self.pbconf)

        if self.run_splash:
            splashhandler.initialise_splash_handler(self.pconf, self.pbconf, self.sbconf)

        completed = False

        while not completed:

            log.info('PhantomBatch will now sleep for ' + str(self.pbconf['sleep_time']) + ' minutes.')
            time.sleep(self.pbconf['sleep_time']*60)

            jobhandler.run_batch_jobs(self.pbconf)
            completed = self.check_phantombatch_complete()

            if self.run_splash and completed:
                splashhandler.splash_handler(self.pconf, self.pbconf, self.sbconf)
