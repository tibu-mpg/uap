import sys
from abstract_step import *
import glob
import misc
import process_pool
import yaml
import os

from logging import getLogger

logger=getLogger('uap_logger')

class CuffCompare(AbstractStep):

    '''
    CuffCompare is part of the 'Cufflinks suite of tools' for
    differential expr. analysis of RNA-Seq data and their
    visualisation. This step compares a cufflinks assembly to 
    known annotation. For details about cuffcompare we refer to
    the author's webpage:

    http://cole-trapnell-lab.github.io/cufflinks/cuffcompare/

    '''

    def __init__(self, pipeline):
        super(CuffCompare, self).__init__(pipeline)

        self.set_cores(1)

        self.add_connection('in/features')    # cuffmerge output
        self.add_connection('out/features')   # *.combined.gft
        self.add_connection('out/loci')       # *.loci
        self.add_connection('out/stats')      # *.stats
        self.add_connection('out/tracking')   # *.tracking
        self.add_connection('out/log_stderr')

        self.require_tool('cuffcompare')

        self.add_option('ref-gtf', str, optional=True,
                        description='A "reference" annotation GTF. The input assemblies are merged together with the reference GTF and included in the final output.')

    def runs(self, run_ids_connections_files):
        
        for run_id in run_ids_connections_files.keys():
            
            with self.declare_run(run_id) as run:
                input_paths = run_ids_connections_files[run_id]['in/features']
                if not input_paths:
                    raise StandardError("No input files for run %s" % (run_id))
                    
                # check whether there's exactly one feature file
                if len(input_paths) != 1:
                    raise StandardError("Expected exactly one feature file.")

                in_file = input_paths[0]
                cuffcompare_out_directory = run.add_temporary_directory('%s.cuffcompare-out' % run_id)

                #features_file = run.add_output_file('features',
                #                                        '%s.combined.gtf' % run_id,
                #                                    input_paths)
                #loci_file     = run.add_output_file('loci',
                #                                    '%s.loci' % run_id,
                #                                    input_paths)
                #stats_file    = run.add_output_file('stats',
                #                                    '%s.stats' % run_id,
                #                                    input_paths)
                #tracking_file = run.add_output_file('tracking',
                #                                    '%s.tracking' % run_id,
                #                                    input_paths)
                log_err_file  = run.add_output_file('log_stderr',
                                                    '%s-cuffcompare-log_stderr.txt' % run_id,
                                                    input_paths)

                with process_pool.ProcessPool(self) as pool:
                    cuffcompare = [self.get_tool('cuffcompare'), '-R', '-o', run_id,
                                   '-r', str(self.get_option('ref-gtf')),
                                   in_file]
                    print(cuffcompare)

                    try:
                        os.mkdir(cuffcompare_out_directory)
                    except OSError:
                        pass
                    
                    os.chdir(cuffcompare_out_directory)
                        
                    pool.launch(cuffcompare,
                                stderr_path = log_err_file
                                #stderr_path = run.get_single_output_file_for_annotation('log_stderr')
                    )

                try:
                    os.rename(os.path.join(cuffcompare_out_directory, '%s.combined.gtf' % run_id),
                              run.get_single_output_file_for_annotation('features'))
                except OSError:
                    raise StandardError('No file: %s' % os.path.join(cuffcompare_out_directory,
                                                                     '%s.combined.gtf' % run_id))

                try:
                    os.rename(os.path.join(cuffcompare_out_directory, '%s.loci' % run_id), 
                              run.get_single_output_file_for_annotation('loci'))
                except OSError:
                    raise StandardError('No file: %s' % os.path.join(cuffcompare_out_directory, 
                                                                     '%s.loci' % run_id))
                                                                    
                try:
                    os.rename(os.path.join(cuffcompare_out_directory, '%s.stats' % run_id), 
                              run.get_single_output_file_for_annotation('stats'))
                except OSError:
                    raise StandardError('No file: %s' % os.path.join(cuffcompare_out_directory, 
                                                                     '%s.stats' % run_id))
                
                try:
                    os.rename(os.path.join(cuffcompare_out_directory, '%s.tracking' % run_id), 
                              run.get_single_output_file_for_annotation('tracking'))
                except OSError:
                    raise StandardError('No file: %s' % os.path.join(cuffcompare_out_directory, 
                                                                     '%s.tracking' % run_id))

                        
#                with run.new_exec_group() as cc_exec_group:
#
#                    features_file = run.add_output_file('features',
#                                                        '%s.combined.gtf' % run_id,
#                                                        input_paths)
#                    loci_file     = run.add_output_file('loci',
#                                                        '%s.loci' % run_id,
#                                                        input_paths)
#                    stats_file    = run.add_output_file('stats',
#                                                        '%s.stats' % run_id,
#                                                        input_paths)
#                    tracking_file = run.add_output_file('tracking',
#                                                        '%s.tracking' % run_id,
#                                                        input_paths)
#                    log_err_file  = run.add_output_file('log_stderr',
#                                                        '%s-cuffcompare-log_stderr.txt' % run_id,
#                                                        input_paths)
#
#                    cuffcompare = [self.get_tool('cuffcompare'), '-R', '-o', run_id,
#                                   '-r', str(self.get_option('ref-gtf')),
#                                   input_paths[0]]
#
#                    cc_exec_group.add_command(cuffcompare, stderr_path = log_err_file)
