import sys
import os
from logging import getLogger
from abstract_step import AbstractStep

logger=getLogger('uap_logger')

class Samtools_Merge(AbstractStep):
    '''
    bla bla
    '''
    
    
    def __init__(self, pipeline):
        super(Samtools_Merge, self).__init__(pipeline)
        
        self.set_cores(8)
        
        self.add_connection('in/alignments')
        self.add_connection('out/log_stderr')
        self.add_connection('out/alignments')
        
        self.require_tool('samtools')
        self.require_tool('cat')
        self.require_tool('pigz')
        

    def runs(self, run_ids_connections_files):
    
        for run_id in run_ids_connections_files.keys():
      
            with self.declare_run(run_id) as run:

                input_paths = run_ids_connections_files[run_id]['in/alignments']

                if input_paths == [None]:
                    run.add_empty_output_connection("alignments")
                    
                else:    
                    with run.new_exec_group() as exec_group:
                        
                        alignments = run.add_output_file(
                            'alignments',
                            '%s-merged.bam' % run_id,
                            input_paths)
                        log_stderr = run.add_output_file(
                            'log_stderr',
                            '%s-log_stderr.txt' % run_id,
                            input_paths)
                        
                        with exec_group.add_pipeline() as pipe:
                        
                            samtools_merge = [self.get_tool('samtools'), 'merge', '-n', '-']
                            for f in input_paths:
                                samtools_merge.append(f)                       
                            pipe.add_command(samtools_merge, stderr_path=log_stderr)
                            
                            samtools_sort = [self.get_tool('samtools'), 'sort', '-O', 'bam']
                            samtools_merge.append(alignments)
                            samtools_merge.extend(['-@', '6'])                
                            pipe.add_command(samtools_sort, stdout_path=alignments)
                            
                            # samtools_merge = [self.get_tool('samtools'), 'merge', '-n']
                            # samtools_merge.append(alignments)                        
                            # for f in input_paths:
                            #     samtools_merge.append(f)                       
                            # pipe.add_command(samtools_merge, stdout_path=alignments, stderr_path=log_stderr)
