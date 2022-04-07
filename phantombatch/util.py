import json
import logging as log
import pickle
import os


def load_init_config(filename):
    """ Load in the json configuration file. """

    with open(filename) as f:
        d = json.load(f)
    f.close()
    return d


def save_pbconfig(pbconf):
    """ Save the phantombatch config file to disk. """

    log.debug('Saving PhantomBatch config to disk.')

    with open(pbconf['name'] + '/' + pbconf['name'] + '_pbconf.pkl', 'wb') as f:
        pickle.dump(pbconf, f, pickle.HIGHEST_PROTOCOL)


def load_config(pbconf):
    """ Load a saved copy of phantombatch config. Note that this function takes the initial json phantombatch config
    file as an argument. This will get overwritten. """

    log.debug('Loading in a saved copy of PhantomBatch config..')

    filename = os.path.join(pbconf['name'], pbconf['name'] + '_pbconf.pkl')

    if os.path.isfile(filename):
        print(filename)
        with open(pbconf['name'] + '/' + pbconf['name'] + '_pbconf.pkl', 'rb') as f:
            pbconf = pickle.load(f)

    return pbconf


def check_for_phantom_warnings(output, exit_at_error=False):
    """ Check for any warnings and errors in the phantom routines. """

    log.debug('Checking for warnings and errors in phantom output..')

    ignore_lines = ['please check output', 'Check output for warnings and errors', 'max relative error',
                    'subroutine check_velocity_error']

    error = False

    output = output.split('\n')
    for line in output:
        if 'warning' in line.lower():
            if all([ignore_line not in line for ignore_line in ignore_lines]):
                log.warning('Phantom warning found: ' + line)

        if 'error' in line.lower():
            if all([ignore_line not in line for ignore_line in ignore_lines]):
                log.error('Phantom error found: ' + line)
                error = True

    if exit_at_error:
        if error:
            call_exit()


def check_pbconf_sim_dir_consistency(job_name, sim_dir, pbconf):
    """ Check to make sure that job_name corresponds to the correct sim_dir """

    short_sim_dir = os.path.basename(sim_dir)

    if job_name.startswith(pbconf['name']):
        return short_sim_dir.startswith(job_name[len(pbconf['name'])+1:])  # +1 since there is an underscore in the name

    elif job_name.startswith(pbconf['short_name']):
        return short_sim_dir.startswith(job_name[len(pbconf['short_name'])+1:])

    else:
        log.error('NAME INCONSISTENCY FOUND')
        return False


def save_phantom_output(output, pbconf, run_dir):
    """ Save the output from phantom into a separate file. """

    output_filename = os.path.join(run_dir, pbconf['name'], 'phantom_output')

    if os.path.exists(output_filename):
        with open(output_filename, 'a') as f:
            # pickle.load(f)
            f.write(output)

    else:
        with open(output_filename, 'w') as f:
            f.write(output)


def check_config_key_change(conf, conf_tmp, key_change):
    for key in conf:
        if key in conf_tmp and (conf_tmp[key] != conf[key]):
            conf_tmp[key] = conf[key]
            log.warning(
                'key ' + key + ' has changed since your last run of PhantomBatch.')
            key_change = True
        elif key not in conf_tmp:
            conf_tmp[key] = conf[key]

    return conf_tmp, key_change


def call_exit():
    log.info('PhantomBatch will now exit')
    exit()
