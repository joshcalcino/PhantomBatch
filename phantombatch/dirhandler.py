import os
import logging as log
from phantombatch import util
from phantombatch import param_keys
import phantomconfig as pc


def loop_keys_dir(variables, setup, pbconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    no_loop_keys = []

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = pbconf['no_loop']
        fw_keys = pbconf['fix_with']

        for key in fw_keys + nl_keys:
            print('key in fw and nl', key)
            # Assert that the parameters listed in no_loop are actually lists
            try:
                value_list = util.extract_string_list_values(setup.config[key].value)
            except KeyError:
                log.error('Parmaeter {} is set in no_loop or fix_with, but is not in the setup file'.format(key))
                util.call_exit()
            except AttributeError:
                log.error('Parmaeter {} is set in no_loop or fix_with, but is not a list in the setup file'.format(key))
                util.call_exit()

            try:
                assert isinstance(value_list, list)
                # type(pconf[key]) isinstance() type(list())
            except AssertionError:
                no_loop_or_fix_with = 'fix_with' if key in fw_keys else 'no_loop'
                log.error('You have added parameter ' + str(key) + ' to the ' + str(no_loop_or_fix_with) +
                          ' options, but ' + str(key) + ' does not contain a list.')
                util.call_exit()

        for i in range(0, len(pbconf['no_loop'])):
            if pbconf['no_loop'][i] not in no_loop_keys:
                dirs = keys_dir(dirs, fw_keys[i], variables, no_loop=False)
                no_loop_keys.append(fw_keys[i])
                no_loop_keys.append(nl_keys[i])

    for key in variables:
        if isinstance(setup.config[key].value, list) and (key not in no_loop_keys):
            print(key)
            dirs = keys_dir(dirs, key, variables, no_loop=False)

    return dirs


def keys_dir(dirs, key, variables, no_loop=False):
    # print()
    #
    # if key == 'binary_a':
    #     # Build array of a's, which are rounded, to get rid of unnecessary decimal places
    #     dict_arr = [round(i, 1) for i in variables[key]]
    #     dirs = dir_func(dirs, 'a', dict_arr, no_loop=no_loop)
    #
    # if key == 'binary_e':
    #     # Build up an array of e's that isn't too long and disregard the '0.'
    #     dict_arr = [format(i, '.2f')[2:] for i in variables[key]]
    #     dirs = dir_func(dirs, 'e', dict_arr, no_loop=no_loop)

    # if key in param_keys.all_names:
    #     dirs = dir_func(dirs, param_keys.all_names[key], variables[key], no_loop=no_loop)
    # else:
    #     dirs = dir_func(dirs, key, variables[key], no_loop=no_loop)

    dirs = dir_func(dirs, key, variables[key], no_loop=no_loop)

    return dirs


def create_dirs(variables, setup, pbconf, setup_directory):
    """ Create directories and save them into conf dictionary. """

    log.debug('Checking if ' + setup_directory + ' directory exist..')

    suite_directory = os.path.join(pbconf['run_dir'], pbconf['name'])

    dir_names = loop_keys_dir(variables, setup, pbconf)
    dirs = []

    for tmp_dir in dir_names:
        cdir = os.path.join(suite_directory, setup_directory, tmp_dir)
        dirs.append(cdir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)
        else:
            log.debug('Directory ' + cdir + ' already exists.')

    pbconf['dirs'] = dirs
    log.debug('Completed create_dirs.')


def dir_func(dirs, string, dict_arr, no_loop=False):
    if len(dirs) != 0:
        dirs = [i+'_' for i in dirs]

    else:
        dirs = [string+str(i).replace('.', '') for i in dict_arr]
        return dirs

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        dirs = [dirs[i] + string + str(dict_arr[i % len(dict_arr)]).replace('.', '')
                for i in range(0, len(dirs))]
        return dirs

    tmp_dir = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_dir[i] = string+str(dict_arr[i]).replace('.', '')

    dirs = [dirs[i] + tmp_dir[j] for i in range(0, len(dirs)) for j in range(0, len(tmp_dir))]
    return dirs
