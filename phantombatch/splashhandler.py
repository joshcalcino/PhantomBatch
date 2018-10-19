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
        os.mkdir('splash_defaults')

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


def get_full_splash_config(sbconf, pbconf):
    """ Insert needed information into sbconf that is contained in pbconf. """

    defaults = {'job_scheduler': None, 'user': None, 'no_email': False}
    for key in defaults:
        if key in pbconf and key not in sbconf:
            sbconf[key] = pbconf[key]
        elif key not in pbconf:
            log.warning('Attempting to set key ' + key + ' in splash batch config file, but ' + key + ' is not defined'
                        'in your PhantomBatch config. Setting ' + key + ' as ' + str(defaults[key]))
            sbconf[key] = defaults[key]

    fixed_settings = {'name': 'splash', 'short_name': 'splash'}
    for key in fixed_settings:
        sbconf[key] = fixed_settings[key]

    return sbconf


def get_splash_command(sbconf, pbconf):
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

        f.write(sbconf['splash_command'])


def create_jobscripts_for_splash(pconf, sbconf, pbconf):
    file = os.path.join(pbconf['dirs'][0], pbconf['name'], '.jobscript')
    destination = sbconf['splash_defaults_dir']

    shutil.copy(file, destination)

    old_jobscript_path = os.path.join(destination, pbconf['name'], '.jobscript')
    new_jobscript_path = os.path.join(destination, sbconf['name'], '.jobscript')

    # Create the jobscript file for splash
    with open(old_jobscript_path, 'r') as f:
        with open(new_jobscript_path, 'w') as g:
            num_lines = sum(1 for tmp in f)
            i = 0
            for line in f:
                #  -4 below since the last 4 lines in old_jobscript_path are the phantom specific lines
                if i < num_lines-4:
                    g.write(line)
                else:
                    break
                i += 1

    os.remove(old_jobscript_path)
    append_splash_jobscript(sbconf, new_jobscript_path)

    # Copy all of these jobscript files to each simulation folder
    for tmp_dir in pbconf['dirs']:
        shutil.copy(new_jobscript_path, tmp_dir)

    # Now use jobhandler.create_jobscripts to include options and names in each jobscript
    jobscripthandler.create_jobscripts(pconf, pbconf, jobscript_filename=sbconf['name'], jobscript_name=sbconf['name'])


def initialise_splash_handler(pconf, pbconf, sbconf):
    """ Initialise the splash handler. """

    log.info('Initialising splash handler..')

    make_splash_defaults_dir(pconf, sbconf, pbconf)
    get_splash_command(sbconf, pbconf)
    create_jobscripts_for_splash(pconf, sbconf, pbconf)


def splash_handler(pconf, pbconf, sbconf):
    return NotImplementedError