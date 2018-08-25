import os
import logging as log
import subprocess
import time
from phantombatch import util
import glob


def decipher_slurm_output(slurm_output, pbconf):
    """ This function deciphers the output from executing 'qstat' in the terminal so that we have a usable list
    of all jobs currently running on the cluster. """

    tally = 0
    tally_arr = []
    found_dash = False

    for char in slurm_output:
        """ Check each character in the slurm output to determine the output column widths. """
        if char == '-':
            tally += 1
            found_dash = True
        elif char == ' ' and found_dash:
            tally += 1
            tally_arr.append(tally)
            tally = 0
        elif char == '_' and found_dash:
            tally += 1
            tally_arr.append(tally)
            tally = 0
        elif char.isdigit():
            tally += 1
            tally_arr.append(tally)
            break

    job_id_len, name_len, username_len = tally_arr[0], tally_arr[1], tally_arr[2]
    time_len, status_len, queue_len = tally_arr[3], tally_arr[4], tally_arr[5]

    line_length = job_id_len + name_len + username_len + time_len + status_len + queue_len
    slurm_lines = []

    for i in range(0, int(len(slurm_output)/line_length)):
        slurm_lines.append(slurm_output[i*line_length:(i+1)*line_length])

    my_jobs = []
    for line in slurm_lines:
        if pbconf['user'] in line:
            if 'C' not in line:
                job_id = line[0:job_id_len].rstrip()
                job_name = line[job_id_len:job_id_len+name_len].rstrip()
                username = line[job_id_len+name_len:job_id_len+name_len+username_len].rstrip()
                run_time = line[job_id_len+name_len+username_len:
                                job_id_len+name_len+username_len+time_len].rstrip()
                status = line[job_id_len+name_len+username_len+time_len:
                              job_id_len+name_len+username_len+time_len+status_len].rstrip()
                queue = line[job_id_len+name_len+username_len+time_len+status_len:line_length].rstrip()
                line_array = [job_id, job_name, username, run_time, status, queue]
                my_jobs.append(line_array)

    return my_jobs


def decipher_pbs_output(pbs_output, pbconf):
    """ This function deciphers the output from pbs in the terminal """

    tally = 0
    tally_arr = []
    found_dash = False

    for char in pbs_output:
        #  Check each character in the pbs output to determine the output column widths
        if char == '-':
            tally += 1
            found_dash = True
        elif char == ' ' and found_dash:
            tally += 1
            tally_arr.append(tally)
            tally = 0
        elif char == '_' and found_dash:
            tally += 1
            tally_arr.append(tally)
            tally = 0
        elif char.isdigit():
            tally += 1
            tally_arr.append(tally)
            break

    job_id_len, name_len, username_len = tally_arr[0], tally_arr[1], tally_arr[2]
    time_len, status_len, queue_len = tally_arr[3], tally_arr[4], tally_arr[5]

    line_length = job_id_len + name_len + username_len + time_len + status_len + queue_len
    slurm_lines = []

    for i in range(0, int(len(pbs_output)/line_length)):
        slurm_lines.append(pbs_output[i*line_length:(i+1)*line_length])

    my_jobs = []
    for line in slurm_lines:
        if pbconf['user'] in line:
            if 'C' not in line:
                job_id = line[0:job_id_len].rstrip()
                job_name = line[job_id_len:job_id_len+name_len].rstrip()
                username = line[job_id_len+name_len:job_id_len+name_len+username_len].rstrip()
                run_time = line[job_id_len+name_len+username_len:
                                job_id_len+name_len+username_len+time_len].rstrip()
                status = line[job_id_len+name_len+username_len+time_len:
                              job_id_len+name_len+username_len+time_len+status_len].rstrip()
                queue = line[job_id_len+name_len+username_len+time_len+status_len:line_length].rstrip()
                line_array = [job_id, job_name, username, run_time, status, queue]
                my_jobs.append(line_array)

    return my_jobs


def check_running_jobs(pbconf):
    log.info('Checking jobs currently running..')

    my_pb_jobs = []
    my_jobs = []

    if pbconf['job_scheduler'] == 'slurm':
        jobs = subprocess.check_output('qstat', stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
        my_jobs = decipher_slurm_output(jobs, pbconf)

    elif pbconf['job_scheduler'] == 'pbs':
        jobs = subprocess.check_output('qstat', stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
        my_jobs = decipher_pbs_output(jobs, pbconf)

    else:
        log.error('Job scheduler not recognised!')

    for line in my_jobs:
        if any([job in line[1] for job in pbconf['job_names']]):  # line[1] holds the name of the job in my_job
            my_pb_jobs.append(line)

    # print(my_pb_jobs)
    return my_pb_jobs


def submit_job(pbconf, directory, jobscript_name):
    """ Submit a job to the cluster. Both SLURM and PBS job schedulers are supported. """

    log.debug('Attempting to submit job in directory ' + directory)

    os.chdir(directory)

    job_number = None

    if pbconf['job_scheduler'] == 'slurm':
        log.debug('Attempting to submit job..')
        output = subprocess.check_output('sbatch ' + jobscript_name, stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True).rstrip()
        log.info(output)
        len_slurm_output = len('Submitted batch job ')  # Change this string if your slurm prints something else out
        job_number = output[len_slurm_output:].rstrip()

    elif pbconf['job_scheduler'] == 'pbs':
        output = subprocess.check_output('qsub ' + jobscript_name, stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True)
        job_number = output.rstrip()
        log.info(output.rstrip())

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
        log.debug(output.rstrip())
        # util.

    elif pbconf['job_scheduler'] == 'pbs':
        output = subprocess.check_output('qdel ' + str(job_number), stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True)
        log.debug(output.rstrip())


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

    if 'submitted_jobs' not in pbconf:
        pbconf['submitted_job_number'] = []

    i = 0
    time.sleep(1)
    for job in pbconf['job_names']:
        current_jobs = check_running_jobs(pbconf)
        if not any(job in cjob for cjob in current_jobs) and \
                ('job_limit' in pbconf and (len(current_jobs) < pbconf['job_limit'])):

            if 'submitted_job_names' in pbconf and (job in pbconf['submitted_job_names']):
                pass

            else:
                job_number = submit_job(pbconf, pbconf['sim_dirs'][i], pbconf['setup'] + '.jobscript')

                if 'submitted_job_numbers' in pbconf:
                    """ Save the submitted job numbers for later reference """
                    pbconf['submitted_job_numbers'].append(str(job_number))

                else:
                    pbconf['submitted_job_numbers'] = []
                    pbconf['submitted_job_numbers'].append(str(job_number))

                if 'submitted_job_names' in pbconf:
                    pbconf['submitted_job_names'].append(job)  # As above but for the job names

                else:
                    pbconf['submitted_job_names'] = []
                    pbconf['submitted_job_names'].append(job)

        elif 'job_limit' in pbconf and (len(current_jobs) > pbconf['job_limit']):
            log.debug('Hit maximum number of allowed jobs.')
            break

        i += 1

    util.save_config(pbconf)


def check_completed_jobs(pbconf):
    """ Check if any jobs have been completed. """
    log.debug('Checking for any completed jobs..')

    current_jobs = check_running_jobs(pbconf)

    if 'completed_jobs' not in pbconf:
        pbconf['completed_jobs'] = []

    i = 0
    for job in pbconf['job_names']:

        if util.check_pbconf_sim_dir_consistency(job, pbconf['sim_dirs'][i], pbconf):
            #  This check makes sure that we keep ordering in place. Currently, pbconf['sim_dirs'][i] corrosponds to
            #  the directory that stores pbconf['job_names'][i]

            #  Make a list of all of the dump files in the simulation directory
            job_list = glob.glob(pbconf['sim_dirs'][i] + '/' + pbconf['setup'] + '_*')

            if 'num_dumps' in pbconf and (len(job_list) >= pbconf['num_dumps'] + 1):  # + 1 for _0000 dump
                #  Check if the number of dumps in the given directory is at least as many as the requested
                #  number of dump files for each simulation, and if so, save the job name in the completed list

                log.debug('Job ' + job + ' has reached the desired number of dump files.')

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

    log.info('There are now ' + str(len(current_jobs)) + ' jobs still running.')
    log.info('There are now ' + str(len(pbconf['completed_jobs'])) + ' jobs finished.')
    log.info('There are now ' + str(len(pbconf['job_names']) - len(pbconf['submitted_job_names'])) +
             ' jobs to be started.')

    util.save_config(pbconf)
