""" The file contianing all the shortened keys to create directory
and jobscript submission names. """

all_names = {}

# ---------------------------------------------------------------------------
# |                            DISC PARAMETERS                              |
# ---------------------------------------------------------------------------

disc_key_dict = {'R_in': 'Rin', 'R_ref': 'Rref', 'R_out': 'Ro',
                 'disc_m': 'dm', 'pindex': 'p', 'qindex': 'q',
                'incl': 'incd', 'H_R': 'hr',  'alphaSS': 'aSS'}

# 'm2': 'm2', 'accr2': 'acr2', 'binary_i': 'i'


# ---------------------------------------------------------------------------
# |                         BINARY DISC PARAMETERS                          |
# ---------------------------------------------------------------------------
# Also includes the keys for triples

disc_names = ['binary', 'primary', 'secondary', 'triple']
short_disc_names = [disc_names[i][0] for name in disc_names]


for key in disc_key_dict:
    for i, name in enumerate(disc_names):
        disc_key_dict[key+name] = disc_key_dict[key]+short_disc_names[i]

# binary_disc_keys = { # Binary
#                     'disc_mbinary': 'dmb', 'R_inbinary': 'Rinb', 'R_refbinary': 'Rrefb', 'R_outbinary': 'Rob',
#                     'qindexbinary': 'qib', 'pindexbinary': 'pib', 'H_Rbinary': 'hrb',
#                     # Primary
#                     'disc_mprimary': 'dmp', 'R_inprimary': 'Rinp', 'R_refprimary': 'Rrefp', 'R_outprimary': 'Rop',
#                     'qindexprimary': 'qip', 'pindexprimary': 'pip',
#                     # Secondary
#                     'disc_msecondary': 'dms', 'R_insecondary': 'Rins', 'R_refsecondary': 'Rrefs',
#                     'R_outsecondary': 'Ros', 'qindexsecondary': 'qis', 'pindexsecondary': 'pis',
#                     # Triple
#                     'disc_msecondary': 'dms', 'R_insecondary': 'Rins', 'R_refsecondary': 'Rrefs',
#                     'R_outsecondary': 'Ros', 'qindexsecondary': 'qis', 'pindexsecondary': 'pis',
#                     }


# ---------------------------------------------------------------------------
# |                            PLANET PARAMETERS                            |
# ---------------------------------------------------------------------------

planet_keys = {'mplanet': 'mp', 'rplanet': 'rp', 'inclplanet': 'ip'}
