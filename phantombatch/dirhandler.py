import os
import logging as log
from phantombatch import util
from phantombatch import param_keys
import phantomconfig as pc
from copy import deepcopy
import numpy as np


def loop_keys_dir(variables, setup, pbconf):
    """ A function for generating both directory names and job names for the job scripts. """
    dirs = []
    no_loop_keys = []
    setup_list = []

    print(pbconf['no_loop'], pbconf['fix_with'])

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = deepcopy(pbconf['no_loop'])
        fw_keys = deepcopy(pbconf['fix_with'])
        # Error checking...
        for key in fw_keys + nl_keys:
            print('key in fw and nl', key)
            # Assert that the parameters listed in no_loop are actually lists
            try:
                value_list = setup.config[key].value
            except KeyError:
                KeyError('Parmaeter {} is set in no_loop or fix_with, but is not in the setup file'.format(key))
            except AttributeError:
                AttributeError('Parmaeter {} is set in no_loop or fix_with, but is not a list in the setup file'.format(key))
            try:
                assert isinstance(value_list, list)
            except AssertionError:
                no_loop_or_fix_with = 'fix_with' if key in fw_keys else 'no_loop'
                log.error('You have added parameter ' + str(key) + ' to the ' + str(no_loop_or_fix_with) +
                          ' options, but ' + str(key) + ' does not contain a list.')
                util.call_exit()

        # Check if a key is specified multiple times in no_loop or fix_with
        duplicate_keys_nl = {}
        duplicate_keys_fw = {}

        # convert lists to numpy arrays
        nl_keys = np.array(nl_keys)
        fw_keys = np.array(fw_keys)

        for i, key in enumerate(nl_keys):
            indices_nl = np.where(nl_keys==key)[0]
            indices_fw = np.where(fw_keys==key)[0]
            if len(indices_nl) > 1:
                # Key is duplicated in nl_keys
                duplicate_keys_nl[key] = len(indices_nl)
            if len(indices_fw) > 0:
                # Key is also in fw_keys
                duplicate_keys_fw[key] = len(indices_fw)

        # Construct an array of keys that we will loop over to assign values
        # in directory names and setup files
        # This line won't work unless you have Python 3.7 or higher
        max_to_min_keys_nl = {key: val for key, val in sorted(duplicate_keys_nl.items(), key=lambda item: item[1])}

        # Now we have an ordering, create new lists for nl_keys and fw_keys
        nl_keys = []
        fw_keys = []
        for key in max_to_min_keys_nl:
            # Get the location of the keys that are fixed with key
            fixed_with_keys_id = np.where(np.array(pbconf['no_loop'])==key)[0]
            for i in range(max_to_min_keys_nl[key]):
                nl_keys.append(key)
                fw_keys.append(pbconf['fix_with'][fixed_with_keys_id[i]])

        # Now populate nl_keys and fw_keys with any remaining keys that aren't duplicated
        for i, key in enumerate(pbconf['no_loop']):
            if key not in nl_keys:
                nl_keys.append(key)
                fw_keys.append(pbconf['fix_with'][i])

        index = 0
        first_key_request = True
        for i, key in enumerate(nl_keys):
            # Do all the duplicated keys first and do not increase setup_list size
            # Each key that is duplicated should have its respective fix_with key values changed in
            # the directory name and setup files
            if key in max_to_min_keys_nl.keys():
                # We do not want to expand setup_list if this has been entered more than once
                if first_key_request:
                    if nl_keys[i] not in no_loop_keys:
                        dirs = keys_dir(dirs, nl_keys[i], variables, no_loop=False)
                    setup_list = setup_func(setup, setup_list, [fw_keys[i], nl_keys[i]], [variables[fw_keys[i]],
                                        variables[nl_keys[i]]], no_loop=False, fixed_pair=True, duplicate_key=False)
                    first_key_request = False
                else:
                    setup_list = setup_func(setup, setup_list, [fw_keys[i], nl_keys[i]], [variables[fw_keys[i]],
                                        variables[nl_keys[i]]], no_loop=False, fixed_pair=True, duplicate_key=True)
                no_loop_keys.append(nl_keys[i])
                no_loop_keys.append(fw_keys[i])

        for i, key in enumerate(nl_keys):
            if nl_keys[i] not in no_loop_keys:
                dirs = keys_dir(dirs, nl_keys[i], variables, no_loop=False)
                setup_list = setup_func(setup, setup_list, [fw_keys[i], nl_keys[i]], [variables[fw_keys[i]],
                                    variables[nl_keys[i]]], no_loop=False, fixed_pair=True)
                no_loop_keys.append(fw_keys[i])
                no_loop_keys.append(nl_keys[i])

    # Now do all the keys that aren't in no_loop and fix_With
    for key in variables:
        if isinstance(setup.config[key].value, list) and (key not in no_loop_keys):
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

    if key in param_keys.all_names:
        dirs = dir_func(dirs, param_keys.all_names[key], variables[key], no_loop=no_loop)
    else:
        dirs = dir_func(dirs, key, variables[key], no_loop=no_loop)

    # dirs = dir_func(dirs, key, variables[key], no_loop=no_loop)

    return dirs


def create_dirs_and_setup(variables, setup, pbconf):
    """ Create directories and save them into conf dictionary. """
    dir_names, setup_list = loop_keys_dir(variables, setup, pbconf)
    dirs = []

    for i, tmp_dir in enumerate(dir_names):
        cdir = os.path.join(pbconf['sims_dir'], tmp_dir)
        dirs.append(cdir)
        if not os.path.exists(cdir):
            os.mkdir(cdir)
            setup_filename = os.path.join(cdir, pbconf['setup']+'.setup')
            setup_list[i].write_phantom(setup_filename)
        else:
            log.debug('Directory ' + cdir + ' already exists.')

    pbconf['sim_dirs'] = dirs
    pbconf['setup_names'] = dir_names
    log.debug('Completed create_dirs.')


def setup_func(setup, setup_list, key, values, no_loop=False, fixed_pair=False, duplicate_key=False):
    # print('setup_list', setup_list)
    # print('key', key)
    # print('values', values)
    if len(setup_list) == 0:
        if fixed_pair:
            setup_list = [deepcopy(setup).change_value(key[0], values[0][i]).change_value(key[1], values[1][i]) for i in range(0, len(values[0]))]
        else:
            setup_list = [deepcopy(setup).change_value(key, val) for val in values]
        return setup_list

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        # print(setup_list)
        setup_list = [setup_list[i].change_value(key, values[i]) for i in range(0, len(setup_list))]
        # print(setup_list)
        return setup_list

    if fixed_pair:
        print(key, values)
        # for i in range(len(setup_list)):
        #     print(setup_list[i].config[key[0]].value)
        # print('setup_list length', len(setup_list))
        # print([(key[0], values[0][i], key[1], values[1][i]) for i in range(0, len(values[0])) for j in range(0, len(setup_list))])
        if duplicate_key:
            # print(key, " is a duplicate_key")
            vl = len(values[0])
            setup_list = [deepcopy(setup_list[j]).change_value(key[0], values[0][j%vl]).change_value(key[1], values[1][j%vl]) \
                                for j in range(0, len(setup_list))]
        else:
            setup_list = [deepcopy(setup_list[j]).change_value(key[0], values[0][i]).change_value(key[1], values[1][i]) \
                                for j in range(0, len(setup_list)) for i in range(0, len(values[0]))]
        # print('setup_list length', len(setup_list))
        # print(values)
        # print([(key[0], values[0][i], key[1], values[1][i]) for j in range(0, len(setup_list)) for i in range(0, len(values[0]))])
        # print("printing keys in the setup list")
        for i in range(len(setup_list)):
            print(key[0], setup_list[i].config[key[0]].value, key[1], setup_list[i].config[key[1]].value)


        # print(len([(key[0], values[0][i], key[1], values[1][i]) for j in range(0, len(setup_list)) for i in range(0, len(values[0]))]))
        return setup_list
    else:
        setup_list = [deepcopy(setup_list[j]).change_value(key, values[i]) for j in range(0, len(setup_list)) for i in range(0, len(values))]
        print(setup_list)
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
