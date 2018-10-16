import os
import logging as log


def write_to_setup(new_setup, ref_setup, setup_strings, pconf):
    """ Write to the setup file. """

    if not isinstance(setup_strings, list):
            setup_strings = [setup_strings]

    log.debug('Printing length of setup_strings..')
    log.debug(len(setup_strings))

    for line in ref_setup:
        key_added = False
        if line.startswith('# '):
            new_setup.write(line)
        else:
            for key in pconf:
                if isinstance(pconf[key], list):
                    for string in setup_strings:  # loop over the strings that need to be written into setup file
                        if (key in line) and string.startswith(key):
                            log.debug('Writing to setup file..')
                            key_added = True
                            new_setup.write(string + '\n')

                else:
                    if line.strip().startswith(key):
                        new_setup.write(key + ' = ' + str(pconf[key]) + '\n')
                        key_added = True

            if not key_added:
                new_setup.write(line)


def setup_from_array(setup_strings, string, dict_arr, no_loop=False):
    """ Create strings for the parameter arrays provided in pconf. """

    if len(setup_strings) is 0:
        setup_strings = [string + ' = ' + str(i) for i in dict_arr]
        return setup_strings

    tmp_setup_strings = ['']*len(dict_arr)
    for i in range(0, len(dict_arr)):
        tmp_setup_strings[i] = string + ' = ' + str(dict_arr[i])

    if no_loop:
        # For now, this is only going to work if you're wanting no_loop over one set of parameters...
        if isinstance(setup_strings[0], list):
            setup_strings = [setup_strings[i] + [tmp_setup_strings[i]] for i in range(0, len(tmp_setup_strings))]

        else:
            setup_strings = [[setup_strings[i], tmp_setup_strings[i]] for i in range(0, len(tmp_setup_strings))]

        return setup_strings

    log.debug('Is setup_strings[0] a list?')
    log.debug(isinstance(setup_strings[0], list))

    if isinstance(setup_strings[0], list):
        log.debug('Entering if statement setup_from_array')
        log.debug('Printing setup_strings')
        log.debug(setup_strings)
        setup_strings = setup_strings * len(dict_arr)
        log.debug('Printing setup_strings')
        log.debug(setup_strings)
        setup_strings = [setup_strings[i] + [tmp_setup_strings[j]] for i in range(0, len(setup_strings))
                         for j in range(0, len(tmp_setup_strings))]
        log.debug('Printing setup_strings')
        log.debug(setup_strings)

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


def get_setup_strings(pconf, pbconf):
    """ This function creates the strings to go into each simulation setup file. This should be changed. """

    setup_strings = []
    no_loop_keys = []

    if 'no_loop' in pbconf and len(pbconf['no_loop']) > 0:
        nl_keys = pbconf['no_loop']
        fw_keys = pbconf['fix_with']

        for i in range(0, len(pbconf['no_loop'])):
            setup_strings = setup_from_array(setup_strings, nl_keys[i], pconf[pbconf['no_loop'][i]], no_loop=True)
            no_loop_keys.append(fw_keys[i])

            setup_strings = setup_from_array(setup_strings, fw_keys[i], pconf[pbconf['fix_with'][i]], no_loop=True)
            no_loop_keys.append(nl_keys[i])

            log.debug('Printing setup_strings')
            log.debug(setup_strings)

    for key in pconf:
        print(key)
        if isinstance(pconf[key], list) and key not in no_loop_keys:
            setup_strings = setup_from_array(setup_strings, key, pconf[key], pbconf)

    return setup_strings


def add_planet_to_setup(new_setup, planet_number, setup_strings, pconf):
    """ Add in the several lines that specify planet parameters into new_setup with the user defined values written.
     Certainly a better way to do this.
     """

    with open(os.path.join(os.environ['PHANTOMBATCH_DIR'], 'phantombatch/setups/planet.setup'), 'r') as planet_setup:
        for line in planet_setup:
            edit_setup_file(new_setup, line.replace('%', str(planet_number)), setup_strings, pconf)


def add_planets(setup_filename, setup_strings, pconf):
    """ Add planets into the setup file. """
    log.debug('Entering ' + setup_filename + ' to add in planets..')
    with open(setup_filename, 'a+') as new_setup:
        if 'nplanets' in pconf:
            new_setup.write('\n nplanets = ' + str(pconf['nplanets']) + ' ! number of planets \n')
            for planet_number in range(1, int(pconf['nplanets'])+1):
                log.debug("Trying to add in planet " + str(planet_number))
                add_planet_to_setup(new_setup, planet_number, setup_strings, pconf)

        else:
            log.debug("Trying to add in planet")
            new_setup.write('\n nplanets = 1 ! number of planets \n')
            add_planet_to_setup(new_setup, 1, setup_strings, pconf)


def add_dust(setup_filename, setup_strings, pconf):
    """ Add two dust method into the setup file. """
    log.debug('Entering ' + setup_filename + ' to add in dust..')
    with open(setup_filename, 'r+') as new_setup:
        with open(os.path.join(os.environ['PHANTOMBATCH_DIR'], 'phantombatch/setups/dust.setup'), 'r') as dust_setup:
            write_to_setup(new_setup, dust_setup, setup_strings, pconf)

        if 'profile_set_dust' in pconf and pconf['profile_set_dust'] == '1' or pconf['profile_set_dust'] == '2':
            with open('phantombatch/setups/custom_dust.setup', 'r') as custom_dust_setup:
                write_to_setup(new_setup, custom_dust_setup, setup_strings, pconf)

    #  ----- ONE FLUID DUST METHOD -----
    if ('dust_method' in pconf) and (pconf['dust_method'] == '1'):
        log.debug('Adding in options for one fluid dust.')
        with open(setup_filename, 'r+') as new_setup:
            if ('ilimitdustflux' in pconf) and (pconf['ilimitdustflux'] == 'T'):
                new_setup.write('\n ilimitdustflux = ' + str(pconf['ilimitdustflux']) + '\n')
            else:
                new_setup.write('\n ilimitdustflux = F \n')


def set_up_disc(setup_filename, setup_strings, pconf):
    """ Set up a disc. """
    log.debug('Entering ' + setup_filename + ' to set up disc..')
    with open(setup_filename, 'w') as new_setup:
        with open(os.path.join(os.environ['PHANTOMBATCH_DIR'], 'phantombatch/setups/disc.setup'), 'r') as disc_setup:
            write_to_setup(new_setup, disc_setup, setup_strings, pconf)

    #  Now loop over lines in new_setup to change any additional options
    with open(setup_filename, 'r+') as new_setup:
        for line in new_setup:
            #  ----- EXPONENTIAL TAPERING FOR THE DISC -----
            if ('itapergas' in pconf) and (pconf['itapergas'] == 'T') and ('itapergas' in line):
                log.debug('Adding in itapergas to binary setup.')
                new_setup.write('\n R_c = ' + str(pconf['R_c']) + '\n')

            # ----- DISC WARPING -----
            if ('iwarp' in pconf) and (pconf['iwarp'] == 'T') and ('iwarp' in line):
                log.debug('Adding in iwarp to binary setup.')
                new_setup.write('\n R_warp = ' + str(pconf['R_warp']) + '\n')
                new_setup.write('\n H_warp = ' + str(pconf['H_warp']) + '\n')


def set_up_binary(setup_filename, setup_strings, pconf):
    """ Set up a binary disc. """
    log.debug('Entering ' + setup_filename + ' to set up binary..')
    log.debug('Printing setup_strings..')
    log.debug(setup_strings)
    with open(setup_filename, 'w') as new_setup:
        with open(os.path.join(os.environ['PHANTOMBATCH_DIR'], 'phantombatch/setups/binary.setup'), 'r') as binary_setup:
            write_to_setup(new_setup, binary_setup, setup_strings, pconf)

        if 'use_primarydisc' in pconf and (pconf['use_primarydisc'] == 'T'):
            log.debug('Adding in a primary disc.')
            with open('phantombatch/setups/primarydisc_binary.setup', 'r') as pd_binary_setup:
                write_to_setup(new_setup, pd_binary_setup, setup_strings, pconf)

        if 'use_secondarydisc' in pconf and (pconf['use_secondarydisc'] == 'T'):
            log.debug('Adding in a secondary disc.')
            with open('phantombatch/setups/secondarydisc_binary.setup', 'r') as sd_binary_setup:
                write_to_setup(new_setup, sd_binary_setup, setup_strings, pconf)

    #  Now loop over lines in new_setup to change any additional options
    with open(setup_filename, 'r+') as new_setup:
        for line in new_setup:
            #  ----- EXPONENTIAL TAPERING FOR THE DISC -----
            if ('itapergasbinary' in pconf) and (pconf['itapergasbinary'] == 'T') and ('itapergasbinary' in line):
                log.debug('Adding in itapergasbinary to binary setup.')
                new_setup.write('\n R_cbinary = ' + str(pconf['R_cbinary']) + '\n')

            if ('itapergasprimary' in pconf) and (pconf['itapergasprimary'] == 'T') and ('itapergasprimary' in line):
                log.debug('Adding in itapergasprimary to binary setup.')
                new_setup.write('\n R_cprimary = ' + str(pconf['R_cprimary']) + '\n')

            if ('itapergassecondary' in pconf) and (pconf['itapergassecondary'] == 'T') and \
                    ('itapergassecondary' in line):
                log.debug('Adding in itapergassecondary to binary setup.')
                new_setup.write('\n R_csecondary = ' + str(pconf['R_csecondary']) + '\n')

            # ----- DISC WARPING -----
            if ('iwarpbinary' in pconf) and (pconf['iwarpbinary'] == 'T') and ('iwarpbinary' in line):
                log.debug('Adding in iwarpbinary to binary setup.')
                new_setup.write('\n R_warpbinary = ' + str(pconf['R_warpbinary']) + '\n')
                new_setup.write('\n H_warpbinary = ' + str(pconf['H_warpbinary']) + '\n')

            if ('iwarpprimary' in pconf) and (pconf['iwarpprimary'] == 'T') and ('iwarpprimary' in line):
                log.debug('Adding in iwarpprimary to binary setup.')
                new_setup.write('\n R_warpprimary = ' + str(pconf['R_warpprimary']) + '\n')
                new_setup.write('\n H_warpprimary = ' + str(pconf['H_warpprimary']) + '\n')

            if ('iwarpsecondary' in pconf) and (pconf['iwarpsecondary'] == 'T') and ('iwarpsecondary' in line):
                log.debug('Adding in iwarpsecondary to binary setup.')
                new_setup.write('\n R_warpsecondary = ' + str(pconf['R_warpsecondary']) + '\n')
                new_setup.write('\n H_warpsecondary = ' + str(pconf['H_warpsecondary']) + '\n')
