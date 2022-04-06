import os
import logging as log
import phantomconfig as pc


def setup_from_array_noloop(setup_strings, string, dict_arr, loop=False):
    """ Create strings for the parameter arrays provided in pconf. """
    print('Printing setup_string!!!!!!')
    print(setup_strings)

    tmp_setup_strings = [''] * len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])

    if loop:
        if isinstance(setup_strings[0], list):
            setup_strings = setup_strings * len(dict_arr)

            setup_strings = [setup_strings[i] + [tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                             for j in range(0, len(tmp_setup_strings))]
            # log.debug('Printing setup_strings')
            # log.debug(setup_strings)

        else:
            setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                             for j in range(0, len(tmp_setup_strings))]

    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    else:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        print('Printing setup_string[0]')
        print(setup_strings[0])
        print('Printing tmp_setup_strings')
        print(tmp_setup_strings)
        if isinstance(setup_strings[0], list):
            setup_strings = [setup_strings[i].append(tmp_setup_strings[i % len(dict_arr)])
                             for i in range(0, len(setup_strings))]

        else:
            setup_strings = [[tmp_setup_strings[i % len(dict_arr)], setup_strings[i]]
                             for i in range(0, len(setup_strings))]

        return setup_strings


def get_setup_strings_noloop(pconf, pbconf):
    """ This function creates the strings to go into each simulation setup file."""

    setup_strings = []
    no_loop_keys = []
    loop = False

    if 'loop' in pbconf and len(pbconf['loop']) == 1:
        loop = True

        for key in pconf:
            if isinstance(pconf[key], list) and (key not in pbconf['loop']) and (key not in pbconf['loop_with']):
                setup_strings = setup_from_array_noloop(setup_strings, key, pconf[key])

        setup_strings = setup_from_array_noloop(setup_strings, pbconf['loop_with'][0], pconf[pbconf['loop_with'][0]])
        setup_strings = setup_from_array_noloop(setup_strings, pbconf['loop_with'][0], pconf[pbconf['loop_with'][0]],
                                                loop=True)

        for i in range(0, len(pbconf['loop'])):
            if pbconf['loop'][i] not in no_loop_keys:
                setup_strings = setup_from_array_noloop(setup_strings, pbconf['loop'][i], pconf[pbconf['loop'][i]], loop=True)

            if pbconf['loop_with'][i] not in no_loop_keys:
                setup_strings = setup_from_array_noloop(setup_strings, pbconf['loop_with'][i], pconf[pbconf['loop_with'][i]], loop=True)

        return setup_strings

    for key in pconf:
        if isinstance(pconf[key], list):
            setup_strings = setup_from_array_noloop(setup_strings, key, pconf[key])

    return setup_strings


def setup_from_array(setup_strings, string, dict_arr, no_loop=False):
    """ Create strings for the parameter arrays provided in pconf. """
    print('Printing setup_string!!!!!!')
    print(setup_strings)

    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    tmp_setup_strings = [''] * len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])

    print('Printing setup_string[0]')
    print(setup_strings[0])
    print('Printing tmp_setup_strings')
    print(tmp_setup_strings)

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        if isinstance(setup_strings[0], list):
            setup_strings = [[tmp_setup_strings[i % len(dict_arr)]] + setup_strings[i]
                             for i in range(0, len(setup_strings))]

        else:
            print('Does this ever get entered???')
            setup_strings = [[tmp_setup_strings[i % len(dict_arr)], setup_strings[i]]
                             for i in range(0, len(setup_strings))]

        return setup_strings

    if isinstance(setup_strings[0], list):
        setup_strings = [setup_strings[i] + [tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]

    else:
        setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]
    return setup_strings


def edit_setup_file(new_setup, line, setup_strings, pconf):
    """ Edit the setup file to add in setup_strings """
    log.debug('Attempting to edit setup file.')

    #  Make sure setup_strings is a list
    if not isinstance(setup_strings, list):
        setup_strings = [setup_strings]

    for key in pconf:
        if isinstance(pconf[key], list):
            for string in setup_strings:  # loop over the strings that need to be written into setup file
                if (key in line) and string.startswith(key):
                    log.debug('Editing setup file..')
                    new_setup.write(string + '\n')

        else:
            if line.strip().startswith(key):
                new_setup.write(key + ' = ' + str(pconf[key]) + '\n')


def write_setup_files(pconf, pbconf):
    """ This function creates the strings to go into each simulation setup file. This should be changed. """

    setup_strings = []
    completed_keys = []

    if 'no_loop' not in pbconf and 'fix_with' not in pbconf:
        for key in pconf:
            if isinstance(pconf[key], list) and (key not in completed_keys):
                setup_strings = setup_from_array(setup_strings, key, pconf[key], no_loop=False)
                completed_keys.append(key)

    elif 'no_loop' in pbconf and 'fix_with' in pbconf:#  len(pbconf['no_loop']) > 0:
        if not isinstance(pbconf['no_loop'], list):
            pbconf['no_loop'] = list(pbconf['no_loop'])

        if not isinstance(pbconf['fix_with'], list):
            pbconf['fix_with'] = list(pbconf['fix_with'])

        try:
            assert len(pbconf['no_loop']) == len(pbconf['fix_with'])
        except AssertionError:
            log.error('Your no_loop and fix_with lists in the PhantomBatch config file must be the same length.')

        tmp_ignore_keys = pbconf['no_loop'] + pbconf['fix_with']

        print('tmp_ignore_keysssssssssssssss')
        print(tmp_ignore_keys)

        for key in pconf:
            if isinstance(pconf[key], list) and (key not in tmp_ignore_keys):
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

        for i in range(0, len(pbconf['no_loop'])):
            if pbconf['fix_with'][i] not in pbconf['no_loop'] and (pbconf['fix_with'][i] not in completed_keys):
                setup_strings = setup_from_array(setup_strings, pbconf['fix_with'][i], pconf[pbconf['fix_with'][i]])
                completed_keys.append(pbconf['fix_with'][i])

            elif pbconf['fix_with'][i] in pbconf['no_loop'] and (pbconf['fix_with'][i] not in completed_keys):
                setup_strings = setup_from_array(setup_strings, pbconf['fix_with'][i],
                                                 pconf[pbconf['fix_with'][i]], no_loop=True)
                completed_keys.append(pbconf['fix_with'][i])

            if pbconf['no_loop'][i] not in completed_keys:
                setup_strings = setup_from_array(setup_strings, pbconf['no_loop'][i],
                                                 pconf[pbconf['no_loop'][i]], no_loop=True)
                completed_keys.append(pbconf['no_loop'][i])

                #no_loop_keys.append(nl_keys[i])
            #
            # if pbconf['fix_with'][i] not in no_loop_keys:
            #     setup_strings = setup_from_array(setup_strings, fw_keys[i], pconf[pbconf['fix_with'][i]], no_loop=True)
            #     no_loop_keys.append(fw_keys[i])
            #     print('Printing no loop keys')
            #     print(no_loop_keys)

    # print("Printing the no_loop_keys")
    # print(no_loop_keys)
    # for key in pconf:
    #     if isinstance(pconf[key], list) and (key not in completed_keys):
    #         print(key)
    #         setup_strings = setup_from_array(setup_strings, key, pconf[key], no_loop=False)
