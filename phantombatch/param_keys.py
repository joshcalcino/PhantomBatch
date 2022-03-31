""" The file contianing all the shortened keys to create directory
and jobscript submission names. """

from copy import deepcopy

all_names = {}


# ---------------------------------------------------------------------------
# |                            DISC PARAMETERS                              |
# ---------------------------------------------------------------------------

disc_key_dict = {'R_in': 'Rin', 'R_ref': 'Rref', 'R_out': 'Ro',
                 'disc_m': 'dm', 'pindex': 'p', 'qindex': 'q',
                'incl': 'incd', 'H_R': 'hr',  'alphaSS': 'aSS'}

# ---------------------------------------------------------------------------
# |                         BINARY DISC PARAMETERS                          |
# ---------------------------------------------------------------------------
# Also includes the keys for triples

disc_names = ['binary', 'primary', 'secondary', 'triple']
short_disc_names = [name[0] for name in disc_names]

disc_key_dict_tmp = deepcopy(disc_key_dict)

for key in disc_key_dict_tmp.keys():
    for i, name in enumerate(disc_names):
        disc_key_dict[key+name] = disc_key_dict[key]+short_disc_names[i]

for key in disc_key_dict.keys():
    all_names[key] = disc_key_dict[key]

# ---------------------------------------------------------------------------
# |                            STAR ORBIT KEYS                              |
# ---------------------------------------------------------------------------

orbits = { 'm2': 'm2', 'accr2': 'acr2', 'binary_i': 'i' }

for key in orbits.keys():
    all_names[key] = orbits[key]

# ---------------------------------------------------------------------------
# |                            PLANET PARAMETERS                            |
# ---------------------------------------------------------------------------

planet_keys = {'mplanet': 'mp', 'rplanet': 'rp', 'inclplanet': 'ip'}

for key in planet_keys.keys():
    all_names[key] = planet_keys[key]
