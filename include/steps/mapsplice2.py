import os
from logging import getLogger
from abstract_step import AbstractStep

logger = getLogger('uap_logger')


class Mapsplice2(AbstractStep):
    '''
    Mapsplice2
    '''

    def __init__(self, pipeline):
        super(Mapsplice2, self).__init__(pipeline)

        # input connections
        self.add_connection('in/first_read')
        self.add_connection('in/second_read')

        # output connections
        self.add_connection('out/alignments')
        self.add_connection('out/deletions')
        self.add_connection('out/insertions')
        self.add_connection('out/junctions')
        self.add_connection('out/stats')
        self.add_connection('out/log_stdout')
        self.add_connection('out/log_stderr')

        self.dir_files = {
            'alignment_handler_remap.err': 'logs',
            'alignment_handler_remap.log': 'logs',
            'best_junction_semi_non_canon_remained_ROC.log': 'logs',
            'bowtie_build.log': 'logs',
            'bowtie_refnames': 'logs',
            'check_reads_format.log': 'logs',
            'collectstats.log': 'logs',
            'junc_db.log': 'logs',
            'mapsplice_original.log': 'logs',
            'mapsplice_remap.log': 'logs',
            'ori.all_junctions_filtered_by_min_mis_lpq.log': 'logs',
            'read_chromo_sizes.log': 'logs',
            'remap_unmapped.1_2sam.log': 'logs',
            'remap_unmapped.2_2sam.log': 'logs',
            'sam2junc_ori.all_junctions.log': 'logs',
            'SetUnmappedBitFlag.log': 'logs',
        }

        for dir_file in self.dir_files:
            self.add_connection('out/' + dir_file)

        # required tools
        self.require_tool('mapsplice2')
        self.require_tool('mkdir')
        self.require_tool('mv')
        self.require_tool('rm')

        # options
        self.add_option('cores', int, optional=True, default=1,
                        description="workaround to specify cores for grid \
                                     engine and threads ie")

        self.add_option('c', str, optional=False, default=None,
                        description="reference sequence directory")

        self.add_option('x', str, optional=False, default=None,
                        description="path and prefix of bowtie index")

        self.add_option('p', int, optional=True, default=1,
                        description="number of threads, default: 1")

    def runs(self, run_ids_connections_files):
        self.set_cores(self.get_option('cores'))

        for run_id in run_ids_connections_files.keys():
            with self.declare_run(run_id) as run:
                input_fileset = []
                r1 = run_ids_connections_files[run_id]['in/first_read'][0]
                input_fileset.append(r1)

                r2 = None
                if 'in/second_read' in run_ids_connections_files[run_id]:
                    r2 = \
                    run_ids_connections_files[run_id]['in/second_read'][0]

                input_fileset.append(r2)

                # create tmp directory for output
                with run.new_exec_group() as mapsplice_eg:
                    temp_dir = run.add_temporary_directory('mapsplice2-out')
                    mkdir = [self.get_tool('mkdir'), temp_dir]
                    mapsplice_eg.add_command(mkdir)

                    mapsplice = [' '.join(self.get_tool('mapsplice2'))]

                    if self.is_option_set_in_config('p'):
                        mapsplice.extend(['-p', str(self.get_option('p'))])

                    mapsplice.extend(['-c', self.get_option('c')])
                    mapsplice.extend(['-c', self.get_option('x')])
                    mapsplice.extend(['-o', temp_dir])
                    mapsplice.extend(['-1', r1])
                    (r2 is not None) and (mapsplice.extend(['-2', r2]))

                    stderr_file = "%s-mapsplice2-log_stderr.txt" % (run_id)
                    log_stderr = run.add_output_file("log_stderr",
                                                     stderr_file, input_fileset)
                    stdout_file = "%s-mapsplice2-log_stdout.txt" % (run_id)
                    log_stdout = run.add_output_file("log_stdout",
                                                     stdout_file, input_fileset)

                mapsplice_eg.add_command(mapsplice, stdout_path=log_stdout,
                                         stderr_path=log_stderr)

                result_files = dict()
                result_files["alignments.sam"] = run.add_output_file(
                    "alignments", "alignments.sam", input_fileset)
                result_files["deletions.txt"] = run.add_output_file(
                    "deletions", "deletions.txt", input_fileset)
                result_files["insertions.txt"] = run.add_output_file(
                    "insertions", "insertions.txt", input_fileset)
                result_files["junctions.txt"] = run.add_output_file(
                    "junctions", "junctions.txt", input_fileset)
                result_files["stats.txt"] = run.add_output_file(
                    "stats", "stats.txt", input_fileset)

                for dir_file in self.dir_files:
                    result_files[dir_file] = run.add_output_file(
                        dir_file, dir_file, input_fileset)

                # move file from temp directory to expected position
                with run.new_exec_group() as mv_exec_group:
                    for orig, dest_path in result_files.iteritems():
                        orig_path = os.path.join(temp_dir, orig)
                        if orig in self.dir_files:
                            orig_path = os.path.join(temp_dir,
                                                     self.dir_files[orig],
                                                     orig)
                            # TODO: how to modify dest_path?
                        mv = [self.get_tool('mv'), orig_path, dest_path]
                        mv_exec_group.add_command(mv)

                # remove directories in temp
                rm_exec_group = run.new_exec_group()
                rm = [self.get_tool('rm'), '-r']
                rm.append(temp_dir + '/logs')
                rm_exec_group.add_command(rm)