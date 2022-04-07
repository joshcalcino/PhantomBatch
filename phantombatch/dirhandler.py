import os
import logging as log
from phantombatch import util
from phantombatch import param_keys
import phantomconfig as pc
from copy import deepcopy


def loop_keys_dir(variables, setup, pbconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    no_loop_keys = []
    setup_list = []

    print(pbconf['no_loop'], pbconf['fix_with'])

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = pbconf['no_loop']
        fw_keys = pbconf['fix_with']

        # Error checking...
        for key in fw_keys + nl_keys:
            print('key in fw and nl', key)
            # Assert that the parameters listed in no_loop are actually lists
            try:
                value_list = setup.config[key].value
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

        for i in range(0, len(nl_keys)):
            if nl_keys[i] not in no_loop_keys:
                key = fw_keys[i]
                dirs = keys_dir(dirs, key, variables, no_loop=False)
                setup_list = setup_func(setup, setup_list, [fw_keys[i], nl_keys[i]], [variables[fw_keys[i]],
                                    variables[nl_keys[i]]], no_loop=False, fixed_pair=True)
                no_loop_keys.append(fw_keys[i])
                no_loop_keys.append(nl_keys[i])

    for key in variables:
        if isinstance(setup.config[key].value, list) and (key not in no_loop_keys):
            print(key)
            dirs = keys_dir(dirs, key, variables, no_loop=False)
            setup_list = setup_func(setup, setup_list, key, variables[key], no_loop=False)

    return dirs, setup_list


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


def create_dirs_and_setup(variables, setup, pbconf):
    """ Create directories and save them into conf dictionary. """
    print(variables)
    print(setup)

    dir_names, setup_list = loop_keys_dir(variables, setup, pbconf)
    dirs = []

    for i, tmp_dir in enumerate(dir_names):
        cdir = os.path.join(pbconf['sims_dir'], tmp_dir)
        dirs.append(cdir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)
            setup_filename = os.path.join(cdir, pbconf['name']+'.setup')
            setup_list[i].write_phantom(setup_filename)
        else:
            log.debug('Directory ' + cdir + ' already exists.')

    pbconf['sim_dirs'] = dirs
    log.debug('Completed create_dirs.')


def setup_func(setup, setup_list, key, values, no_loop=False, fixed_pair=False):
    print('setup_list', setup_list)
    print('key', key)
    print('values', values)
    if len(setup_list) == 0:
        if fixed_pair:
            setup_list = [deepcopy(setup).change_value(key[0], values[0][i]).change_value(key[1], values[0][i]) for i in range(0, len(values[0]))]
        else:
            setup_list = [deepcopy(setup).change_value(key, val) for val in values]
        return setup_list

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        setup_list = [setup_list[i].change_value(key, values[i]) for i in range(0, len(setup_list))]
        return setup_list

    if fixed_pair:
        setup_list = [deepcopy(setup_list[j].change_value(key[0], values[0][i]).change_value(key[1], values[1][i])) \
                            for i in range(0, len(values[0])) for j in range(0, len(setup_list)) ]
    else:
        setup_list = [setup_list[j].change_value(key, values[i]) for j in range(0, len(setup_list)) for i in range(0, len(values))]
    return setup_list


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
