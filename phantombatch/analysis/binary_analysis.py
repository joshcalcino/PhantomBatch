import subprocess
import os
import numpy


def find_apastron():
    return NotImplementedError


def find_periastron():
    return NotImplementedError


#
# for edir in eccentricity_filenames:
#     for bdir in binary_ratio_filenames:
#         cdir = os.path.join(edir, bdir, 'gas_only_hr/')
#         output = subprocess.check_output('cp phantomanalysis ' + cdir, stderr=subprocess.STDOUT,
#                                 universal_newlines=True, shell=True)
#         print(output)
#         os.chdir(cdir)
#         print('cd ' + cdir)
#         output = subprocess.check_output('ls', stderr=subprocess.STDOUT,
#                                 universal_newlines=True, shell=True)
#
#         print(output)
#         output = subprocess.check_output('./phantomanalysis gas_only_hr_0*', stderr=subprocess.STDOUT,
#                                universal_newlines=True, shell=True)
#         print(output)
#         sink1 = numpy.genfromtxt('sinkpositions_1.dat', dtype=None)
#         sink2 = numpy.genfromtxt('sinkpositions_2.dat')
#         # print(sink1)
#         dumpfile = []
#         xs = []
#         ys = []
#         zs = []
#
#         xc = []
#         yc = []
#         zc = []
#
#         for i in range(0, len(sink1)):
#             dumpfile.append(sink1[i][0])
#             xs.append(sink1[i][2])
#             ys.append(sink1[i][3])
#             zs.append(sink1[i][4])
#
#             xc.append(sink2[i][2])
#             yc.append(sink2[i][3])
#             zc.append(sink2[i][4])
#
#         xyzs = numpy.array([xs, ys, zs])
#         xyzc = numpy.array([xc, yc, zc])
#
#         product = []
#         for i in range(0, len(zc)):
#             product.append(numpy.dot([xs[i], ys[i], zs[i]], [xc[i], yc[i], zc[i]]))
#
#         # print(xyzs)
#         # product = xyzc @ xyzs
#         print(numpy.min(product))
#         print(numpy.max(product))
#         print(dumpfile[int(numpy.argmin(product))])
#         print(dumpfile[int(numpy.argmax(product))])
#         with open('aphelion_perihelion.txt', 'w') as f:
#             f.write('aphelion in file ' + str(dumpfile[int(numpy.argmin(product))]) + '\n')
#             f.write('perihelion in file ' + str(dumpfile[int(numpy.argmax(product))]) + '\n')
#         # print(sink1[:][2])
#         os.chdir('../../../')
#         # exit()