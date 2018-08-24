import logging as log


def write_to_setup(new_setup, ref_setup, setup_strings, pconf, index):
    """ Write to the setup file. """

    for line in ref_setup:
        key_added = False
        if line.startswith('# '):
            new_setup.write(line)
        else:
            for key in pconf:
                if isinstance(pconf[key], list):
                    for string in setup_strings[index]:  # loop over the strings that need to be written into setup file
                        # print(string)
                        if (key in line) and (key in string):
                            log.debug('Writing to setup file..')
                            key_added = True
                            new_setup.write(string + '\n')

                else:
                    if key in line:
                        new_setup.write(key + ' = ' + str(pconf[key]) + '\n')
                        key_added = True

            if not key_added:
                # print(line)
                new_setup.write(line)


def setup_from_array(setup_strings, string, dict_arr):
    """ Create strings for the parameter arrays provided in pconf. """

    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    tmp_setup_strings = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])

    if isinstance(setup_strings[0], list):
        setup_strings = setup_strings * len(dict_arr)
        setup_strings = [setup_strings[i] + [tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]

    else:
        setup_strings = [[setup_strings[i], tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]
    return setup_strings


def edit_setup_file(new_setup, line, setup_strings, pconf, index):

    for key in pconf:
        if isinstance(pconf[key], list):
            for string in setup_strings[index]:  # loop over the strings that need to be written into setup file
                if (key in line) and (key in string):
                    log.debug('Editing setup file..')
                    new_setup.write(string + '\n')

        else:
            if key in line:
                new_setup.write(key + ' = ' + str(pconf[key]) + '\n')


def get_setup_strings(pconf):
    """ This function creates the directory names for each simulation. """

    setup_strings = []
    for key in pconf:
        if isinstance(pconf[key], list):
            if key == 'binary_e':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_a':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'm2':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'binary_i':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

            if key == 'alphaSS':
                setup_strings = setup_from_array(setup_strings, key, pconf[key])

    return setup_strings
