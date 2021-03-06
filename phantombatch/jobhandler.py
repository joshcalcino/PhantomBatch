import os
import logging as log
import subprocess
from phantombatch import util
import glob


def decipher_slurm_output(slurm_output, pbconf):
    """ This function deciphers the output from executing 'qstat' in the terminal so that we have a usable list
    of all jobs currently running on the cluster.

    There is an issue here this doesn't work if there are no jobs running on a cluster in order for the function to
    decipher the output.. Will need to figure a way around this, but may be an issue with things further down the
    pipeline.
    """

    tally = 0
    tally_arr = []
    found_char = False

    slurm_output = slurm_output.split('\n')[:-1]  # Since the last line should be empty

    first_line = slurm_output[0]

    if first_line.startswith('squeue: error: Invalid user:'):
        log.error('squeue Invalid user error. Make sure you entered in your cluster username correctly.')
        exit()

    for char in first_line:
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

    my_jobs = []

    found_user = False

    for line in slurm_output:
        if pbconf['user'] in line:
            found_user = True

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


def get_slurm_jobs(pbconf):
    jobs = subprocess.check_output('squeue -u ' + pbconf['user'] +
                                   ' -o  "%.18i %.12P %.40j %.12u %.2t %.14M %.6D %.20R"',
                                   stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    my_jobs = decipher_slurm_output(jobs, pbconf)
    return my_jobs


def get_pbs_jobs():

    columns = ['Job Id: ', 'Job_Name = ', 'Job_Owner = ', 'resources_used.walltime = ', 'job_state = ']

    tmp_jobs = [['']]*len(columns)

    i = 0
    for column in columns:
        try:
            output = str(subprocess.check_output('qstat -f | grep \'' + column + '\'',
                                                 stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                        ).split('\n')[:-1]  # since the last value is an empty string
        except subprocess.CalledProcessError:
            log.warning('Could not get PSB job information using qstat -f')
            return None

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
    log.debug('Checking jobs currently running..')

    my_pb_jobs = []
    my_jobs = []

    if pbconf['job_scheduler'] == 'slurm':
        my_jobs = get_slurm_jobs(pbconf)

    elif pbconf['job_scheduler'] == 'pbs':
        my_jobs = get_pbs_jobs()

    else:
        log.error('Job scheduler not recognised!')

    if my_jobs is None:
        my_jobs = []

    # log.debug('Filtering through the job scheduler output to find PhantomBatch jobs..')
    for line in my_jobs:
        # log.debug(line)
        if any([job in line[1] for job in pbconf['job_names']]) and 'C' not in line[4]:
            #  line[1] holds the name of the job in my_job
            my_pb_jobs.append(line)

    return my_pb_jobs


def submit_slurm_job(pbconf, jobscript_name):
    log.debug('Attempting to submit SLURM job..')
    job_scheduluer_call = 'sbatch '
    output = _job_submit(pbconf, job_scheduluer_call, jobscript_name)

    len_slurm_output = len('Submitted batch job ')  # Change this string if your slurm prints something else out
    job_number = output[len_slurm_output:].strip()
    log.debug('Printing job_number from submit_job')
    log.debug(job_number)

    return job_number


def submit_pbs_job(pbconf, jobscript_name):
    log.debug('Attempting to submit PBS job..')
    job_scheduluer_call = 'qsub '
    output = _job_submit(pbconf, job_scheduluer_call, jobscript_name)

    #  Want to get the line that contains the job number and ignore other lines
    # output.split(' ')
    # job_number = ''
    # number = None
    # for char in output:
    #     # log.debug(line)
    #     if char[0].isdigit():
    #         number = True
    #         job_number += char
    #     else:
    #         number = False
    job_number = output
    log.debug('Printing job_number from submit_job')
    log.debug(job_number)

    return job_number


def submit_job(pbconf, directory, jobscript_name=None):
    """ Submit a job to the cluster. Both SLURM and PBS job schedulers are supported. """

    log.debug('Attempting to submit job in directory ' + directory)

    if jobscript_name is None:
        jobscript_name = pbconf['setup'] + '.jobscript'

    os.chdir(directory)

    job_number = None
    job_scheduluer_call = None

    if pbconf['job_scheduler'] == 'slurm':
        log.debug('Attempting to submit SLURM job..')
        job_number = submit_slurm_job(pbconf, jobscript_name)

    elif pbconf['job_scheduler'] == 'pbs':
        log.debug('Attempting to submit PBS job..')
        job_number = submit_pbs_job(pbconf, jobscript_name)

    elif job_scheduluer_call is None:
        log.error('Job scheduler not recognised, cannot submit jobs!')
        log.info('Please use a known job scheduler, or add in your own.')
        util.call_exit()

    os.chdir(pbconf['run_dir'])

    if job_number is None:
        log.error('Unable to submit job.')
        exit()
    else:
        log.info('Submitted job number ' + str(job_number))
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


def cancel_job_by_name(pbconf, job_name):
    current_jobs = check_running_jobs(pbconf)

    for cjob in current_jobs:
        if job_name in cjob:
            cancel_job(pbconf, cjob[0])


def cancel_all_jobs_by_name(pbconf):
    """ This function will cancel all of the jobs with jobnames for this run of PhantomBatch """

    log.info('Cancelling all submitted jobs.')
    current_jobs = check_running_jobs(pbconf)
    log.debug('Current jobs are:')
    log.debug(current_jobs)

    for job_name in pbconf['submitted_job_names']:
        log.debug('See if ' + job_name + ' is in current submitted jobs.')
        if any(job_name in cjob for cjob in current_jobs):
            log.debug('Job number ' + job_name + ' is in current jobs, going to cancel this job now.')
            cancel_job_by_name(pbconf, job_name)

    log.info('All submitted jobs have been cancelled.')


def cancel_all_submitted_jobs(pbconf):
    """ This function will cancel all of the jobs submitted by PhantomBatch for pbconf['name']. """

    log.info('Cancelling all submitted jobs.')
    current_jobs = check_running_jobs(pbconf)
    log.debug('Current jobs are:')
    log.debug(current_jobs)

    log.debug('Submitted jobs are:')
    log.debug(pbconf['submitted_job_numbers'])

    for job_number in pbconf['submitted_job_numbers']:
        log.debug('See if ' + job_number + ' is in current submitted jobs.')
        if any(job_number in cjob for cjob in current_jobs):
            log.debug('Job number ' + job_number + ' is in current jobs, going to cancel this job now.')
            cancel_job(pbconf, job_number)

    log.info('All submitted jobs have been cancelled.')


def run_batch_jobs(pbconf):
    """ This function will attempt to submit all of the jobs in pbconf['job_names'] and pbconf['sim_dirs']. """

    if 'submitted_job_numbers' not in pbconf:
        pbconf['submitted_job_numbers'] = []

    if 'submitted_job_names' not in pbconf:
        pbconf['submitted_job_names'] = []

    i = 0

    for job in pbconf['job_names']:
        log.debug('Looking to submit ' + job)
        current_jobs = check_running_jobs(pbconf)
        # log.debug(current_jobs)

        if not any(job in cjob for cjob in current_jobs):
            if 'job_limit' in pbconf and (len(current_jobs) >= pbconf['job_limit']):
                log.info('Will not submit any more jobs since ' + str(len(current_jobs)) + ' are running'
                         ' and there is a limit of ' + str(pbconf['job_limit']) + ' jobs allowed to be submitted.')
                break

            if (job in pbconf['submitted_job_names']) and any(job in cjob for cjob in current_jobs):
                pass

            elif ('completed_jobs' in pbconf) and (job in pbconf['completed_jobs']):
                pass

            else:
                log.debug('Printing job name that is being submitted')
                log.debug(job)
                job_number = submit_job(pbconf, pbconf['sim_dirs'][i], pbconf['setup'] + '.jobscript')

                pbconf['submitted_job_numbers'].append(str(job_number))

                if job not in pbconf['submitted_job_names']:
                    log.debug('adding ' + str(job) + ' into submitted_job_names')
                    pbconf['submitted_job_names'].append(job)
                    log.debug(pbconf['submitted_job_names'])

        # elif 'job_limit' in pbconf and (len(current_jobs) >= pbconf['job_limit']):
        #     log.info('Will not submit any more jobs since ' + str(len(current_jobs)) + ' are running'
        #              ' and there is a limit of ' + str(pbconf['job_limit']) + ' jobs allowed to be submitted.')
        #     break

        i += 1

    util.save_pbconfig(pbconf)


def check_completed_jobs(pbconf):
    """ Check if any jobs have been completed. """
    log.debug('Checking for any completed jobs..')

    current_jobs = check_running_jobs(pbconf)

    current_job_names = [cjob[1] for cjob in current_jobs]

    if len(current_jobs) == 0:
        log.info('Could not find any running jobs for user ' + pbconf['user']+'.')

    if 'completed_jobs' not in pbconf:
        pbconf['completed_jobs'] = []

    if 'job_num_dumps' not in pbconf:
        pbconf['job_num_dumps'] = [0]*len(pbconf['job_names'])

    i = 0
    for job in pbconf['job_names']:
        if util.check_pbconf_sim_dir_consistency(job, pbconf['sim_dirs'][i], pbconf):
            #  This check makes sure that we keep ordering in place. Currently, pbconf['sim_dirs'][i] corrosponds to
            #  the directory that stores pbconf['job_names'][i]

            #  Make a list of all of the dump files in the simulation directory
            job_list = glob.glob(os.path.join(pbconf['sim_dirs'][i], pbconf['setup'] + '_*'))

            pbconf['job_num_dumps'][i] = len(job_list)

            if 'num_dumps' in pbconf and (len(job_list) >= pbconf['num_dumps'] + 1):  # + 1 for _0000 dump
                #  Check if the number of dumps in the given directory is at least as many as the requested
                #  number of dump files for each simulation, and if so, save the job name in the completed list

                log.info('Job ' + job + ' has reached the desired number of dump files.')

                if any(job in cjob for cjob in current_jobs):
                    log.debug('Cancelling ' + job + ' since it has reached the desired number of dump files.')

                    cancel_job_by_name(pbconf, pbconf['job_names'][i])

                    if 'completed_jobs' in pbconf and job not in pbconf['completed_jobs']:
                        pbconf['completed_jobs'].append(job)

            if 'num_dumps' not in pbconf:
                log.warning('You have not specified the number of dump files you would like for each simulation. '
                            'Please specify this in your .config file with the \'num_dumps\' key.')

        i += 1

    log.info('----------------------------------------------------------------')
    log.info('|                       PHANTOM JOB INFO                        |')
    log.info('----------------------------------------------------------------')

    for i in range(0, len(pbconf['job_names'])):
        log.info(pbconf['job_names'][i] + ' has ' + str(pbconf['job_num_dumps'][i]) + ' out of ' +
                 str(pbconf['num_dumps']) + ' dumps completed.')

    log.info('There are now ' + str(len(current_jobs)) + ' jobs still running.')
    log.info('There are now ' + str(len(pbconf['completed_jobs'])) + ' jobs finished.')
    log.info('There are now ' + str(len(pbconf['job_names']) - len(pbconf['submitted_job_names'])) +
             ' jobs to be started.')

    util.save_pbconfig(pbconf)


def _job_submit(pbconf, job_scheduluer_call, jobscript_name):
    output = None

    try:
        output = subprocess.check_output(job_scheduluer_call + jobscript_name, stderr=subprocess.STDOUT,
                                         universal_newlines=True, shell=True).strip()
    except subprocess.CalledProcessError:
        log.error('Could not submit ' + pbconf['job_scheduler'].upper() +
                  ' job. There may be something wrong in the jobscript file, or ' + pbconf['job_scheduler'].upper() +
                  ' may not be on your cluster.')

        if output is None:
            util.call_exit()

        else:
            log.info('Here is the output from my attempt to run ' + job_scheduluer_call)
            log.info(output)

    return output
