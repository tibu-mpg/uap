import sys
from abstract_step import *
import glob
import misc
import process_pool
import yaml
import os

from logging import getLogger

logger=getLogger('uap_logger')

class Stringtie(AbstractStep):

    def __init__(self, pipeline):
        super(Stringtie, self).__init__(pipeline)

        self.set_cores(6)
        
        self.add_connection('in/alignments')
        self.add_connection('out/transcript')
        self.add_connection('out/log_stderr')
        
        self.require_tool('mkdir')
        self.require_tool('mv')
        self.require_tool('stringtie')

        self.add_option('G', str, optional=False,
                        description="use reference transcript annotation to guide assembly")
        self.add_option('v', bool, optional=True,
                        description='Turns on verbose mode, printing bundle processing details')

        
    def runs(self, run_ids_connections_files):

        options=['G', 'v']

        set_options = [option for option in options if \
                       self.is_option_set_in_config(option)]

        option_list = list()
        for option in set_options:
            if isinstance(self.get_option(option), bool):
                if self.get_option(option):
                    option_list.append('-%s' % option)
                else:
                    option_list.append( '-%s' % option )
                    option_list.append( str(self.get_option(option)) )

        for run_id in run_ids_connections_files.keys():

             with self.declare_run(run_id) as run:
                input_paths = run_ids_connections_files[run_id]['in/alignments']
                temp_dir = run.add_temporary_directory('stringtie_out')
                # Stringtie will den Namen der Outputfile gleich in der Uebergabe an die Methode haben
                temp_dir_filename = os.path.join(temp_dir, "transcripts.gtf")
                
                if not os.path.isfile(self.get_option('G')):
                    logger.error(
                        "The path %s provided to option 'G' is not a file."
                        % self.get_option('G') )
                    sys.exit(1)
                
                # check, if only a single input file is provided
                if len(input_paths) != 1:
                    raise StandardError("Expected exactly one alignments file., but got this %s" % input_paths)
                
                stringtie = [self.get_tool('stringtie'), input_paths[0], '-o', temp_dir_filename,
                             '-G', self.get_option('G')
                ]
                stringtie.extend(option_list)
                                           
             with run.new_exec_group() as exec_group:
                 #  Create temporary directory for stringtie output
                 mkdir = [self.get_tool('mkdir'), temp_dir]
                 exec_group.add_command(mkdir)

             with run.new_exec_group() as exec_group:
                 exec_group.add_command(stringtie,
                                        stderr_path = run.add_output_file('log_stderr',
                                                                          '%s-stringties-log.txt' % run_id,
                                                                          input_paths
                                                                          )
                                        )
                 
                 # move output to temp
             with run.new_exec_group() as mv_exec_group:
                 dest_path = run.add_output_file('transcript', '%s-transcripts.gtf' % run_id, input_paths)
                 mv = [self.get_tool('mv'), temp_dir_filename, dest_path]
                 mv_exec_group.add_command(mv)

