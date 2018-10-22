import os
import shutil
import logging as log
import glob
from phantombatch import jobscripthandler, dirhandler

# try:
#     splash_dir = os.environ('SPLASH_DIR')
# except KeyError:
#     log.warning('SPLASH_DIR environment variable not set!')


def make_splash_defaults_dir(pconf, pbconf, sbconf):

    dirhandler.create_dirs(pconf, sbconf, 'splash')
    splash_directory = os.path.join(pbconf['run_dir'], pbconf['name'], 'splash')

    splash_defaults_dir = os.path.join(splash_directory, 'splash_defaults')

    if not os.path.exists(splash_defaults_dir):
        os.mkdir(splash_defaults_dir)

    sbconf['splash_defaults_dir'] = splash_defaults_dir


def copy_splash_defaults(pconf, pbconf, sbconf, names=None):
    """ Copy any splash files that have been saved into the splash_defaults directory. """

    log.info('Attempting to copy splash default files into new directories..')

    if 'splash_defaults_dir' not in sbconf:
        make_splash_defaults_dir(pconf, pbconf, sbconf)

    splash_defaults_files = glob.glob(sbconf['splash_defaults_dir'])

    if len(splash_defaults_files) == 0:
        log.warning('No splash default files saved in ' + sbconf['splash_defaults_dir'])
        return None

    default_file_names = ['splash.defaults', 'splash.limits']

    # Allow the user to define their own splash file names
    if names is not None:
        splash_file_names = names
    else:
        splash_file_names = default_file_names

    for name in splash_file_names:
        if name in splash_defaults_files:
            # We want to copy into the PhantomBatch simulation directories
            for tmp_dir in pbconf['dirs']:
                shutil.copyfile(os.path.join(sbconf['splash_defaults_dir'], name), tmp_dir)

    log.info('Splash default files copied.')


def get_full_splash_config(pbconf, sbconf):
    """ Insert needed information into sbconf that is contained in pbconf. """

    defaults = {'job_scheduler': None, 'user': None, 'no_email': False, 'run_dir': os.environ['PWD'], 'name': None}
    for key in defaults:
        if key in pbconf and key not in sbconf:
            sbconf[key] = pbconf[key]
        elif key not in pbconf:
            log.warning('Attempting to set key ' + key + ' in splash batch config file, but ' + key + ' is not defined'
                        'in your PhantomBatch config. Setting ' + key + ' as ' + str(defaults[key]))
            sbconf[key] = defaults[key]

    fixed_settings = {'short_name': 'splash'}
    for key in fixed_settings:
        sbconf[key] = fixed_settings[key]

    return sbconf


def get_splash_command(pbconf, sbconf):
    """ Add in a splash command if one is not defined in sbconf. """

    if 'splash_command' not in sbconf:
        log.warning('No Splash command entered in splash config, add one in using \"splash_command\". Setting default'
                    'as \'ssplash -x 1 -y 2 -r 6 -dev ')
        sbconf['splash_command'] = 'ssplash -x 1 -y 2 -r 6 -dev ' + 'Sname.png ' + pbconf['setup'] + '_*'


def append_splash_jobscript(sbconf, jobscript_path):
    """ Append the splash jobscript file with the execution command. """

    with open(jobscript_path, 'a') as f:
        if 'jobscript_lines' in sbconf:
            if isinstance(sbconf['jobscript_lines'], list):
                for line in sbconf['jobscript_lines']:
                    line = line.append('\n')
                    f.write(line)
            else:
                f.write(sbconf['jobscript_lines'].append('\n'))

        #  Replace the name of the png file
        path = os.path.normpath(jobscript_path)
        path = path.split(os.sep)

        # Get the second last part of the directory, this is the folder we are currently looking at
        image_string = path[:-2]
        print(image_string)
        if 'image_string' in sbconf:
            image_string += sbconf['image_string']
        f.write(sbconf['splash_command'].replace('Sname', image_string))


def create_jobscripts_for_splash(pconf, pbconf, sbconf):
    file = os.path.join(pbconf['dirs'][0], pbconf['setup']+'.jobscript')
    destination = sbconf['splash_defaults_dir']

    shutil.copy(file, destination)

    old_jobscript_path = os.path.join(destination, pbconf['setup']+'.jobscript')
    new_jobscript_path = os.path.join(destination, sbconf['short_name']+'.jobscript')

    # Create the jobscript file for splash
    with open(old_jobscript_path, 'r') as f:
        with open(new_jobscript_path, 'w') as g:
            num_lines = 0
            for line in f:
                num_lines += 1
            i = 0
            for line in f:
                #  -4 below since the last 4 lines in old_jobscript_path are the phantom specific lines
                if i < num_lines-4:
                    g.write(line)
                else:
                    break
                i += 1

    os.remove(old_jobscript_path)

    # Copy all of these jobscript files to each simulation folder
    for tmp_dir in pbconf['dirs']:
        shutil.copy(new_jobscript_path, tmp_dir)
        append_splash_jobscript(sbconf, tmp_dir)

    # Now use jobhandler.create_jobscripts to include options and names in each jobscript
    jobscripthandler.create_jobscripts(pconf, pbconf, jobscript_filename=sbconf['short_name'],
                                       jobscript_name=sbconf['short_name'])


def initialise_splash_handler(pconf, pbconf, sbconf):
    """ Initialise the splash handler. """

    log.info('Initialising splash handler..')

    suite_directory = os.path.join(pbconf['run_dir'], pbconf['name'])

    #  Check if the directory already exists
    if not os.path.exists(suite_directory):
        os.mkdir(suite_directory)

    splash_dir = os.path.join(suite_directory, 'splash')

    if not os.path.exists(splash_dir):
        os.mkdir(splash_dir)

    make_splash_defaults_dir(pconf, pbconf, sbconf)
    get_splash_command(pbconf, sbconf)
    create_jobscripts_for_splash(pconf, pbconf, sbconf)


def splash_handler(pconf, pbconf, sbconf):
    return NotImplementedError
