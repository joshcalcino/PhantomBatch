import os
import logging as log
import subprocess
import time
from phantombatch import util
import glob


def decipher_slurm_output(slurm_output, pbconf):
    """ This function deciphers the output from executing 'qstat' in the terminal so that we have a usable list
    of all jobs currently running on the cluster.

    There is an issue here this this doesn't work if there are no jobs running on a cluster in order for the function to
    decipher the output.. Will need to figure a way around this, but may be an issue with things further down the
    pipeline.
    """

    tally = 0
    tally_arr = []
    found_char = False

    for char in slurm_output:
        """ Check each character in the slurm output to determine the output column widths. """
        if char.isspace() and not found_char:
            tally += 1

        elif char.isalpha() or char == '(':
            tally += 1
            found_char = True

        elif char.isspace() and found_char:
            tally += 1
            tally_arr.append(tally)
            tally = 0
            found_char = False

        elif char == ')' and found_char:
            tally += 1
            tally_arr.append(tally)
            break

    job_id_len, queue_len, name_len, username_len = tally_arr[0], tally_arr[1], tally_arr[2], tally_arr[3]
    status_len, time_len, nodes_len, node_len = tally_arr[4], tally_arr[5], tally_arr[6], tally_arr[7]

    line_length = sum(tally_arr)
    slurm_lines = []

    for i in range(0, int(len(slurm_output)/line_length)):
        slurm_lines.append(slurm_output[i*line_length:(i+1)*line_length])

    my_jobs = []

    found_user = False

    for line in slurm_lines:
        if pbconf['user'] in line:
            found_user = True
            if 'C' not in line:
                job_id = line[0:
                              job_id_len].strip()

                queue = line[job_id_len:
                             job_id_len + queue_len].strip()

                job_name = line[queue_len + job_id_len:
                                queue_len + job_id_len + name_len].strip()

                username = line[job_id_len + name_len + queue_len:
                                job_id_len + queue_len + username_len + name_len].strip()

                status = line[job_id_len + queue_len + name_len + username_len:
                              job_id_len + queue_len + name_len + username_len + status_len].strip()

                run_time = line[job_id_len + queue_len + name_len + username_len + status_len:
                                job_id_len + queue_len + name_len + username_len + status_len + time_len].strip()

                nodes = line[job_id_len + queue_len + name_len + username_len + status_len + time_len:
                             job_id_len + queue_len + name_len + username_len + status_len + time_len + nodes_len]\
                    .strip()

                node = line[job_id_len + queue_len + name_len + username_len + status_len + time_len + nodes_len:
                            line_length].strip()

                line_array = [job_id, job_name, username, run_time, status, queue, nodes, node]
                my_jobs.append(line_array)

    if not found_user:
        log.error('Unable to find any jobs associated with user specified in PhantomBatch config.')

    return my_jobs


def get_pbs_jobs():

    columns = ['Job Id: ', 'Job_Name = ', 'Job_Owner = ', 'resources_used.walltime = ', 'job_state = ']

    tmp_jobs = [['']]*len(columns)

    i = 0
    for column in columns:
        output = str(subprocess.check_output('qstat -f | grep \'' + column + '\'',
                                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                     ).split('\n')[:-1]  # since the last value is an empty string

        # output = str(output).split('\n')
        # output = copy.deepcopy(output[:-1]) # since the last value is an empty string

        stripped_output = [out.replace(str(column), '').strip() for out in output]

        if column == 'Job_Owner = ':
            ind = stripped_output[0].index('@')
            stripped_output = [out[:ind] for out in stripped_output]

        tmp_jobs[i] = stripped_output

        i += 1

    my_jobs = [[str(i)]*len(tmp_jobs) for i in range(len(tmp_jobs[0]))]

    for i in range(0, len(tmp_jobs)):
        for j in range(0, len(tmp_jobs[i])):
            my_jobs[j][i] = tmp_jobs[i][j]

    return my_jobs


def check_running_jobs(pbconf):
    log.info('Checking jobs currently running..')

    my_pb_jobs = []
    my_jobs = []

    if pbconf['job_scheduler'] == 'slurm':
        jobs = subprocess.check_output('squeue -u ' + pbconf['user'] +
                                       ' -o  "%.18i %.9P %.40j %.8u %.2t %.14M %.6D %.15R"',
                                       stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

        my_jobs = decipher_slurm_output(jobs, pbconf)
        log.debug(my_jobs)

    elif pbconf['job_scheduler'] == 'pbs':
        my_jobs = get_pbs_jobs()

    else:
        log.error('Job scheduler not recognised!')

    for line in my_jobs:
        if any([job in line[1] for job in pbconf['job_names']]):  # line[1] holds the name of the job in my_job
            log.debug('Adding in a new line to my_pb_jobs..')
            my_pb_jobs.append(line)

    log.debug('Printing phantombatch jobs..')
    log.debug(my_pb_jobs)
    return my_pb_jobs


def submit_job(pbconf, directory, jobscript_name):
    """ Submit a job to the cluster. Both SLURM and PBS job schedulers are supported. """

    log.debug('Attempting to submit job in directory ' + directory)

    os.chdir(directory)

    job_number = None

    if pbconf['job_scheduler'] == 'slurm':
        log.debug('Attempting to submit SLURM job..')
        output = subprocess.check_output('sbatch ' + jobscript_name, stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True).strip()
        log.info(output)
        len_slurm_output = len('Submitted batch job ')  # Change this string if your slurm prints something else out
        job_number = output[len_slurm_output:].strip()

    elif pbconf['job_scheduler'] == 'pbs':
        log.debug('Attempting to submit PBS job..')
        output = str(subprocess.check_output('qsub ' + jobscript_name, stderr=subprocess.STDOUT,
                                             universal_newlines=True, shell=True))
        log.info(output.strip())
        output = output.split('\n')[:-1]  # remove last line since it is empty

        #  Want to get the line that contains the job number and ignore other lines
        for line in output:
            if line[0].isdigit():
                job_number = line.strip()
        log.debug('Printing job_number from submit_job')
        log.debug(job_number)
    else:
        log.error('Job scheduler not recognised, cannot submit jobs!')
        log.info('Please use a known job scheduler, or add in your own.')
        exit()

    os.chdir(os.environ['PHANTOM_DATA'])

    if job_number is None:
        log.error('Unable to submit job.')
        exit()
    else:
        return job_number


def cancel_job(pbconf, job_number):
    """ Cancel a single job. """
    log.info('Cancelling job ' + str(job_number))

    if pbconf['job_scheduler'] == 'slurm':
        output = subprocess.check_output('scancel ' + str(job_number), stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True)
        log.debug(output.strip())
        # util.

    elif pbconf['job_scheduler'] == 'pbs':
        output = subprocess.check_output('qdel ' + str(job_number), stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True)
        log.debug(output.strip())


def cancel_all_submitted_jobs(pbconf):
    """ This function will cancel all of the jobs submitted by PhantomBatch for pbconf['name']. """

    log.debug('Cancelling all submitted jobs.')
    current_jobs = check_running_jobs(pbconf)

    for job_number in pbconf['submitted_job_numbers']:
        if any(job_number in cjob for cjob in current_jobs):
            cancel_job(pbconf, job_number)

    log.debug('All submitted jobs have been cancelled.')


def run_batch_jobs(pbconf):
    """ This function will attempt to submit all of the jobs in pbconf['job_names'] and pbconf['sim_dirs']. """

    if 'submitted_job_numbers' not in pbconf:
        pbconf['submitted_job_numbers'] = []

    if 'submitted_job_names' not in pbconf:
        pbconf['submitted_job_names'] = []

    i = 0
    time.sleep(1)
    for job in pbconf['job_names']:
        log.debug('Looking to submit ' + job)
        current_jobs = check_running_jobs(pbconf)
        if not any(job in cjob for cjob in current_jobs) and \
                ('job_limit' in pbconf and (len(current_jobs) <= pbconf['job_limit'])):

            if job in pbconf['submitted_job_names'] and any(job in cjob for cjob in current_jobs):
                pass

            else:
                log.debug('Printing job name that is being submitted')
                log.debug(job)
                job_number = submit_job(pbconf, pbconf['sim_dirs'][i], pbconf['setup'] + '.jobscript')

                pbconf['submitted_job_numbers'].append(str(job_number))
                pbconf['submitted_job_names'].append(job)

                log.debug('Printing submitted_job_numbers after append')
                log.debug(pbconf['submitted_job_numbers'])

                log.debug('Printing submitted_job_names after append')
                log.debug(pbconf['submitted_job_names'])

        elif 'job_limit' in pbconf and (len(current_jobs) <= pbconf['job_limit']):
            log.debug('Hit maximum number of allowed jobs.')
            break

        i += 1

    util.save_config(pbconf)


def check_completed_jobs(pbconf):
    """ Check if any jobs have been completed. """
    log.debug('Checking for any completed jobs..')

    current_jobs = check_running_jobs(pbconf)

    if len(current_jobs) == 0:
        log.info('Could not find any running jobs for user ' + pbconf['user']+'.')

    if 'completed_jobs' not in pbconf:
        pbconf['completed_jobs'] = []

    if 'job_num_dumps' not in pbconf:
        pbconf['job_num_dumps'] = [0]*len(pbconf['job_names'])

    log.debug('Printing pbconf[\'completed_jobs\'] in check_completed_jobs')
    log.debug(pbconf['completed_jobs'])

    i = 0
    for job in pbconf['job_names']:

        if util.check_pbconf_sim_dir_consistency(job, pbconf['sim_dirs'][i], pbconf):
            #  This check makes sure that we keep ordering in place. Currently, pbconf['sim_dirs'][i] corrosponds to
            #  the directory that stores pbconf['job_names'][i]

            #  Make a list of all of the dump files in the simulation directory
            job_list = glob.glob(pbconf['sim_dirs'][i] + '/' + pbconf['setup'] + '_*')

            pbconf['job_num_dumps'][i] = len(job_list)

            if 'num_dumps' in pbconf and (len(job_list) >= pbconf['num_dumps'] + 1):  # + 1 for _0000 dump
                #  Check if the number of dumps in the given directory is at least as many as the requested
                #  number of dump files for each simulation, and if so, save the job name in the completed list

                log.info('Job ' + job + ' has reached the desired number of dump files.')
                log.debug('Printing current_jobs in check_completed_jobs')
                log.debug(current_jobs)
                if any(job in cjob for cjob in current_jobs):
                    log.debug('Cancelling ' + job + ' since it has reached the desired number of dump files.')

                    assert any(job and pbconf['submitted_job_numbers'][i] in cjob for cjob in current_jobs)

                    cancel_job(pbconf, pbconf['submitted_job_numbers'][i])

                    if 'completed_jobs' in pbconf:
                        pbconf['completed_jobs'].append(job)

            if 'num_dumps' not in pbconf:
                log.warning('You have not specified the number of dump files you would like for each simulation. '
                            'Please specify this in your .config file with the \'num_dumps\' key.')

        i += 1

    log.info('--------------------------------------')
    log.info('|          PHANTOM JOB INFO          |')
    log.info('--------------------------------------')

    for i in range(0, len(pbconf['job_names'])):
        log.info(pbconf['job_names'][i] + ' has ' + str(pbconf['job_num_dumps'][i]) + ' out of ' +
                 str(pbconf['num_dumps']) + ' dumps completed.')

    log.info('There are now ' + str(len(current_jobs)) + ' jobs still running.')
    log.info('There are now ' + str(len(pbconf['completed_jobs'])) + ' jobs finished.')
    log.info('There are now ' + str(len(pbconf['job_names']) - len(pbconf['submitted_job_names'])) +
             ' jobs to be started.')

    util.save_config(pbconf)
