import os
import shutil
import logging as log
import subprocess
from phantombatch import setuphandler, inhandler, jobscripthandler, dirhandler, jobhandler, splashhandler, util
import time
import atexit
import glob

__all__ = ["PhantomBatch"]


class PhantomBatch(object):

    def __init__(self, config_filename, verbose=False, terminate_at_exit=True,
                 run_dir=None, fresh_start=False, do_not_recompile=False):
        # Set class variables
        self.terminate_at_exit = terminate_at_exit
        self.fresh_start = fresh_start
        self.do_not_recompile = do_not_recompile

        # Get running directory, use current directory if run_dir not specified
        if run_dir is not None:
            self.run_dir = run_dir
        else:
            self.run_dir = os.environ['PWD']

        #  Set up the level of verbosity
        if verbose:
            log.basicConfig(level=log.DEBUG)
        else:
            log.basicConfig(level=log.INFO)

        #  Terminate jobs if PhantomBatch is interrupted
        if terminate_at_exit:
            log.info('PhantomBatch will cancel all jobs on exiting')
            atexit.register(self.terminate_jobs_at_exit)

        # Load in config file
        self.config = util.load_init_config(config_filename)
        self.pconf = self.config['phantom_setup']
        self.pbconf = self.config['phantom_batch_setup']

        self.piconf = None
        if 'phantom_in' in self.config:
            self.piconf = self.config['phantom_in']

        # Set up any  class variables that depend on config files

        # Get the setup directory for Phantom
        self.setup_dir = os.path.join(self.run_dir, self.pbconf['name'], 'phantom_' + self.pbconf['setup'])

        # Get the suite_directory
        self.suite_directory = os.path.join(self.run_dir, self.pbconf['name'])

        # Get the simulations directory
        self.sims_dir = os.path.join(self.suite_directory, 'simulations')

        if self.fresh_start:
            if self.do_not_recompile:
                log.info('Removing previous simulation directory but keeping the compiled copy of Phantom.')
                if os.path.exists(self.pbconf['name']):
                    print(self.suite_directory)
                    contents = glob.glob(self.suite_directory + '/*')
                    for content in contents:
                        if 'phantom_' not in content:
                            shutil.rmtree(content)

            else:
                log.info('Removing previous run directory..')
                if os.path.exists(self.pbconf['name']):
                    shutil.rmtree(self.pbconf['name'])

        # self.initialise_phantom decides whether or not we reinitilise everything
        self.initialise_phantombatch = True

        # check if a saved PhantomBatch configuration file already exists, overwrite current if it does
        if os.path.isfile(os.path.join(self.pbconf['name'], self.pbconf['name'] + '_pbconf.pkl')):
            self.initialise_phantombatch = False
            pbconf_tmp = util.load_config(self.pbconf)

            for key in self.pbconf:
                if key in pbconf_tmp and (self.pbconf[key] != pbconf_tmp[key]):
                    pbconf_tmp[key] = self.pbconf[key]
                    log.warning(
                        'key ' + key + ' has changed since your last run of PhantomBatch.')
                elif key not in pbconf_tmp:
                    pbconf_tmp[key] = self.pbconf[key]
            self.pbconf = pbconf_tmp

        self.run_splash = False
        # Set up splash if it is going to be used
        if 'splash_setup' in self.config:
            self.run_splash = True
            self.sconf = splashhandler.get_full_splash_config(
                self.pbconf, self.config['splash_batch_setup'])

            if 'no_splash' in self.sconf and self.sconf['no_splash'] == 1 is True:
                # Add this in so it is easier to control splash usage without having to remove lines from config file
                self.run_splash = False

        # Save run_dir in the PhantomBatch config dict
        self.pbconf['run_dir'] = self.run_dir

        # Confirm that the PHANTOM_DIR environment variable has been set
        self.phantom_dir = None
        try:
            self.phantom_dir = os.environ['PHANTOM_DIR']

        except KeyError:
            log.warning(
                'PHANTOM_DIR system variable not defined. If no Phantom directory is defined, I wil use '
                '\'PHANTOM_DIR=~/phantom\'.')

        if "phantom_dir" in self.pbconf:
            self.phantom_dir = self.pbconf['phantom_dir']

            log.warning('Found phantom_dir in the PhantomBatch config file. I will use this directory to find phantom.')

        if self.phantom_dir is None:
            self.phantom_dir = '~/phantom'

        # Try to find a SYSTEM variable
        self.system_in_make_options = False
        self.system_string = None

        try:
            sys_environ = os.environ['SYSTEM']
            self.system_string = 'SYSTEM=' + str(sys_environ)

        except KeyError:
            log.warning(
                'SYSTEM environment variable is not set, this is required to run Phantom.')
            log.info(
                'You should make sure that your SYSTEM variable is defined in the Phantom Makefile.')
            log.info('This will make sure that the correct Fortran compiler and system job scheduler '
                     'is selected when you make Phantom.')
            log.info('Checking if \"system\" is defined in the phantombatch config file..')

        if "system" in self.pbconf:
            sys_environ = self.pbconf['system']

            if self.system_string is not None:
                log.warning('You have an environment variable for SYSTEM set, but have also specified \"system\" in '
                            'the PhantomBatch config file, which will be used to run Phantom.')

            self.system_string = 'SYSTEM=' + str(sys_environ)
            log.info('System found, setting ' + self.system_string)

        if "make_options" in self.pbconf and ("SYSTEM=" in self.pbconf["make_options"]):
            self.system_in_make_options = True
            log.info('SYSTEM variable found in \"make_options\".')

            if self.system_string is not None:
                log.warning('You have an environment variable for SYSTEM set, but have also specified a SYSTEM in '
                            '\"make_options\", which will be used to run Phantom.')
                make_options_components = self.pbconf["make_options"].split(' ')

                for string in make_options_components:
                    if "SYSTEM=" in string:
                        self.system_string = string

        if self.system_string is None and self.system_in_make_options is False:
            log.error('No system setting found. Add onto into the phantombatch config (either ifort or gfortran), or '
                      'add one into the Phantom Makefile (preferred).')
            util.call_exit()

    def exit_phantombatch(self):
        os.chdir(self.run_dir)

    def terminate_jobs_at_exit(self):
        """ Cancel all jobs running when PhantomBatch exits. Mainly useful for debugging purposes. """

        log.info('Attempting to terminate all jobs as PhantomBatch is exiting..')

        if 'job_names' in self.pbconf:
            jobhandler.cancel_all_jobs_by_name(self.pbconf)

        # Cancel all splash jobs if splash has been invoked
        if self.run_splash:
            if 'job_names' in self.sconf:
                jobhandler.cancel_all_jobs_by_name(self.sconf)

    def initialise(self):
        log.info('Initialising ' + self.pbconf['name'] + '..')

        #  Check if the directory already exists
        if not os.path.exists(self.suite_directory):
            os.mkdir(self.suite_directory)

        if not os.path.exists(self.sims_dir):
            os.mkdir(self.sims_dir)

        self.initiliase_phantom()
        dirhandler.create_dirs(self.pconf, self.pbconf, 'simulations')

        for tmp_dir in self.pbconf['dirs']:
            output = subprocess.check_output('cp ' + os.path.join(self.run_dir, self.pbconf['name'],
                                                                  'phantom_' + self.pbconf['setup']) + '/* ' +
                                             os.path.join(self.sims_dir, tmp_dir), stderr=subprocess.STDOUT,
                                             universal_newlines=True, shell=True)

            util.save_phantom_output(
                output.rstrip(), self.pbconf, self.run_dir)

    def initiliase_phantom(self):
        """ This function will initialise phantom in a special directory called phantom_pbconfg['setup']. We do this so
        that we do not need to compile phantom for each simulation directory. """

        log.info('Checking if Phantom has been compiled for ' + self.pbconf['name'] + '..')

        if isinstance(self.pbconf['setup'], list):
            """ Imagining that we can have an array of setups which would be consecutively executed.. 
            Say if we wanted to run some gas and then moddump with dust grains.."""
            log.error(
                'You added a list for setup options. This functionality has not been implemented yet.')
            raise NotImplementedError

        else:
            setup_dir = os.path.join(
                self.run_dir, self.pbconf['name'], 'phantom_' + self.pbconf['setup'])

            if not os.path.exists(setup_dir):
                os.mkdir(setup_dir)

            if not os.path.exists(os.path.join(setup_dir, 'Makefile')):
                log.info('Setting up Phantom.. This may take a few moments.')

                output = subprocess.check_output(os.path.join(self.phantom_dir, 'scripts', 'writemake.sh') +
                                                 ' ' + self.pbconf['setup'] + ' > ' +
                                                 os.path.join(setup_dir, 'Makefile'),
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                util.save_phantom_output(
                    output.rstrip(), self.pbconf, self.run_dir)

                os.chdir(setup_dir)

                make_settings = ''

                if self.system_in_make_options:
                    make_settings = str(self.pbconf['make_options'])

                elif self.system_string is not None:
                    make_settings = self.system_string

                    if 'make_options' in self.pbconf:
                        make_settings = make_settings + ' ' + str(self.pbconf['make_options'])

                log.info('Compiling Phantom with ' + make_settings)

                # Compile the Phantom code with make_settings
                output = subprocess.check_output('make ' + make_settings,
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                # Check for warnings and errors, then save output
                util.check_for_phantom_warnings(output, exit_at_error=True)
                util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                # Compile phantomsetup with make_settings
                output = subprocess.check_output('make setup ' + make_settings,
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                util.check_for_phantom_warnings(output, exit_at_error=True)
                util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

                log.debug('Writing jobscript template.')

                try:
                    # Use the job scheduler provided in pbconf if one has been defined
                    if "job_scheduler" in self.pbconf:
                        log.info('Creating jobscripts using the job_scheduler provided in the '
                                 'PhantomBatch config file..')

                        qsys = self.pbconf['job_scheduler']
                        qsys_string = 'QSYS=' + str(qsys)#.upper()

                    else:
                        qsys_string = ''

                    jobname_string = 'JOBNAME=' + 'phantombatch'

                    log.debug('Attempting to create jobscript files using ' + self.system_string + '.')

                    execution_string = 'make qscript INFILE=' + self.pbconf['setup'] + '.in ' + self.system_string + \
                                       ' ' + qsys_string + ' ' + jobname_string

                    log.debug('Running ' + execution_string)

                    output = subprocess.check_output(execution_string,
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                    with open(self.pbconf['setup'] + '.jobscript', 'w+') as f:
                        f.write(output)

                except subprocess.CalledProcessError:
                    if 'Error: qscript needs known SYSTEM variables set' in output:
                        log.error('Error attempting to create jobscript file. SYSTEM variable is not defined or not '
                                  'recognised. If SYSTEM is not ifort or gfortran, please define it in the Phantom '
                                  'Makefile before continuing to use PhantomBatch.')
                    else:
                        log.info(output)
                        log.error('Error attempting to create jobscript file. '
                                  'Please check the \'phantom_output\' file.')

                    util.save_phantom_output(
                        output.rstrip(), self.pbconf, self.run_dir)

                    util.call_exit()

                if 'make_moddump_options' in self.pbconf:
                    output = subprocess.check_output('make moddump ' + self.pbconf['make_moddump_options'],
                                                     stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                    util.save_phantom_output(
                        output.rstrip(), self.pbconf, self.run_dir)

                os.chdir(self.run_dir)

    def create_setups(self):
        """ This function will create all of the setup files for the simulation parameters
        specified in the phantom config dictionary, pconf.
        It does not matter if this is adding in a messy fashion, as phantomsetup solves it for us."""

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
                    setuphandler.set_up_binary(
                        filename, setup_strings[index], self.pconf)
                else:
                    setuphandler.set_up_disc(
                        filename, setup_strings[index], self.pconf)

            if 'setplanets' in self.pconf and (self.pconf['setplanets'] == 1):
                setuphandler.add_planets(
                    filename, setup_strings[index], self.pconf)

            if 'add_dust' in self.pbconf and self.pbconf['add_dust']:
                setuphandler.add_dust(
                    filename, setup_strings[index], self.pconf)

            index += 1

        log.info('Completed.')

    def run_phantom_setup(self):
        """ This function will execute phantomsetup in each directory in pbconf['sim_dirs']
         to produce pbconf['name'].in, which is the file that is read in by phantom. """

        log.info('Running phantomsetup for each setup file in each simulation for ' +
                 self.pbconf['name'] + '..')

        setup_dirs = self.pbconf['sim_dirs']

        for tmp_dir in setup_dirs:
            log.debug('Changing directory to ' + tmp_dir)
            os.chdir(tmp_dir)
            output = subprocess.check_output('./phantomsetup ' + self.pbconf['setup'], stderr=subprocess.STDOUT,
                                             universal_newlines=True, shell=True)

            if 'writing setup options file' in output:
                # Rerun phantomsetup because there might be some annoying
                output = subprocess.check_output('./phantomsetup ' + self.pbconf['setup'], stderr=subprocess.STDOUT,
                                                 universal_newlines=True, shell=True)

            util.check_for_phantom_warnings(output.rstrip())
            util.save_phantom_output(
                output.rstrip(), self.pbconf, self.run_dir)

        os.chdir(self.run_dir)
        log.info('Completed.')

    def check_phantombatch_complete(self):
        """ Check if all the desired phantombatch jobs have been completed. """

        log.debug('Checking if PhantomBatch has completed all requested jobs.')

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

        if self.initialise_phantombatch:
            self.initialise()
            self.create_setups()
            self.run_phantom_setup()

        self.pbconf['job_names'] = jobscripthandler.create_jobscripts(
            self.pconf, self.pbconf)
        jobhandler.check_running_jobs(self.pbconf)
        jobhandler.run_batch_jobs(self.pbconf)

        if self.run_splash:
            splashhandler.initialise_splash_handler(
                self.pconf, self.pbconf, self.sconf)

        completed = False

        while not completed:

            log.info('PhantomBatch will now sleep for ' +
                     str(self.pbconf['sleep_time']) + ' minutes.')
            time.sleep(self.pbconf['sleep_time'] * 60)

            completed = self.check_phantombatch_complete()

            if self.run_splash:
                splashhandler.splash_handler(self.pbconf, self.sconf)
