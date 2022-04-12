import os
import shutil
import logging as log
import subprocess
from phantombatch import jobscripthandler, dirhandler, jobhandler, util
import time
import atexit
import glob
import phantomconfig as pc
from copy import deepcopy

__all__ = ["PhantomBatch"]


class PhantomBatch(object):

    def __init__(self, config_filename, setup_filename, jobscript_filename=None,
                 in_file=None, verbose=False, terminate_at_exit=True, run_dir=None,
                 fresh_start=False, do_not_recompile=False, submit_jobs=False):
        # Set class variables
        self.terminate_at_exit = terminate_at_exit
        self.fresh_start = fresh_start
        self.do_not_recompile = do_not_recompile
        self.submit_jobs = submit_jobs
        self.jobscript_filename = jobscript_filename
        self.initialise_jobscripts = True
        if self.jobscript_filename != None:
            self.initialise_jobscripts = False

        self.in_file = in_file
        self.complete_in_file = True
        if in_file != None:
            self.in_file, self.complete_in_file = util.read_in_file(in_file)

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
        self.pbconf = util.load_init_config(config_filename)

        self.setup = pc.read_config(setup_filename)
        if verbose:
            print("Input setup file:")
            print(self.setup.summary())
        self.loop_variables = {}
        for key in self.setup.config.keys():
            # phantomconfig saves lists as strings...
            if isinstance(self.setup.config[key].value, list):
                print(key, self.setup.config[key].value)
                self.loop_variables[key] = deepcopy(self.setup.config[key].value)

        # Set up any  class variables that depend on config files
        # Get the setup directory for Phantom
        self.setup_dir = os.path.join(self.run_dir, self.pbconf['name'], 'phantom')

        # Get the suite_directory
        self.suite_directory = os.path.join(self.run_dir, self.pbconf['name'])

        # Get the simulations directory
        self.sims_dir = os.path.join(self.suite_directory, 'simulations')

        # Save directories to the config file
        self.pbconf['run_dir'] = self.run_dir
        self.pbconf['setup_dir'] = self.setup_dir
        self.pbconf['suite_dir'] = self.suite_directory
        self.pbconf['sims_dir'] = self.sims_dir

        if self.fresh_start:
            if self.do_not_recompile:
                log.info('Removing previous simulation directory but keeping the compiled copy of Phantom.')
                if os.path.exists(self.pbconf['name']):
                    log.debug(self.suite_directory)
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

        # pbconf_tmp, pconf_tmp = util.load_config(self.pbconf)
        # key_change = False
        #
        # # check if a saved PhantomBatch configuration file already exists, overwrite current if it does
        # if pbconf_tmp is not None:
        #     self.initialise_phantombatch = False
        #     self.pbconf, key_change = util.check_config_key_change(self.pbconf, pbconf_tmp, key_change)
        #
        # # check if a saved Phantom configuration file already exists, overwrite current if it does
        # if pconf_tmp is not None:
        #     self.initialise_phantombatch = False
        #     self.pconf, key_change = util.check_config_key_change(self.pconf, pconf_tmp, key_change)
        #
        # if key_change:
        #     self.initialise_phantombatch = True
        #     log.debug('I will be reinitialising PhantomBatch.')

        # Save a copy of the pconf file so we know if any changes are made to it
        # util.save_pcongif(self.pbconf, self.pconf)

        # Save run_dir in the PhantomBatch config dict
        self.pbconf['run_dir'] = self.run_dir

        # Confirm that the PHANTOM_DIR environment variable has been set
        self.phantom_dir = None
        try:
            self.phantom_dir = os.environ['PHANTOM_DIR']

        except KeyError:
            if "phantom_dir" in self.pbconf:
                self.phantom_dir = self.pbconf['phantom_dir']

                log.warning('Found phantom_dir in the PhantomBatch config file. I will use this directory to find phantom.')

            if self.phantom_dir is None:
                self.phantom_dir = '~/phantom'
                log.warning('Could not find the phantom directory, assuming PHANTOM_DIR=~/phantom.')

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

    def initialise(self):
        log.info('Initialising ' + self.pbconf['name'] + '..')

        #  Check if the directory already exists
        if not os.path.exists(self.suite_directory):
            os.mkdir(self.suite_directory)

        if not os.path.exists(self.sims_dir):
            os.mkdir(self.sims_dir)

        self.initiliase_phantom()
        dirhandler.create_dirs_and_setup(self.loop_variables, self.setup, self.pbconf)

        for tmp_dir in self.pbconf['sim_dirs']:
            tmp_dir = os.path.join(self.sims_dir, tmp_dir)

            if not os.path.isfile(os.path.join(tmp_dir, 'phantom')):
                # If phantom is not already in the current directory, copy it there
                output = subprocess.check_output('cp ' + self.pbconf['setup_dir'] + '/* ' + tmp_dir,
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

                util.save_phantom_output(output.rstrip(), self.pbconf, self.run_dir)

    def initiliase_phantom(self):
        """ This function will initialise phantom in a special directory called phantom_pbconfg['setup']. We do this so
        that we do not need to compile phantom for each simulation directory. """

        log.info('Checking if Phantom has been compiled for ' + self.pbconf['name'] + '..')

        setup_dir = self.pbconf['setup_dir']
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

            log.debug('Adding jobscripts.')
            if self.jobscript_filename == None:
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

    def run_phantom_setup(self):
        """ This function will execute phantomsetup in each directory in pbconf['sim_dirs']
         to produce pbconf['name'].in, which is the file that is read in by phantom. """

        log.info('Running phantomsetup for each setup file in each simulation for ' +
                 self.pbconf['name'] + '..')

        setup_dirs = self.pbconf['sim_dirs']

        for tmp_dir in setup_dirs:
            if not os.path.isfile(os.path.join(tmp_dir, 'disc.in')):
                # Do not run phantomsetup if disc.in already exists, since it means phantomsetup has already run
                log.debug('Changing directory to ' + tmp_dir)
                os.chdir(tmp_dir)
                output = subprocess.check_output('./phantomsetup ' + self.pbconf['setup'], stderr=subprocess.STDOUT,
                                                 universal_newlines=True, shell=True)

                if 'writing setup options file' in output:
                    # Rerun phantomsetup because there might be some annoying missing parameter
                    output = subprocess.check_output('./phantomsetup ' + self.pbconf['setup'], stderr=subprocess.STDOUT,
                                                     universal_newlines=True, shell=True)

                util.check_for_phantom_warnings(output.rstrip())
                util.save_phantom_output(
                    output.rstrip(), self.pbconf, self.run_dir)

                if self.in_file != None:
                    # We will overwrite values in the .in file
                    current_in_file = pc.read_config(self.pbconf['setup'] + '.in')
                    for key in self.in_file.config:
                        current_in_file.change_value(key, self.in_file.config[key].value)
                    current_in_file.write_phantom(self.pbconf['setup'] + '.in')

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
        print("initialise is ", self.initialise_phantombatch)

        if self.initialise_phantombatch:
            self.initialise()
            self.run_phantom_setup()
            self.pbconf['job_names'] = jobscripthandler.create_jobscripts(self.pbconf, jobscript_filename=self.jobscript_filename)

        if self.submit_jobs:
            jobhandler.check_running_jobs(self.pbconf)
            jobhandler.run_batch_jobs(self.pbconf)
            completed = False
        else:
            completed = True

        if not completed:
            self.check_phantombatch_complete()
