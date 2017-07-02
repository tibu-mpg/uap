import sys
from abstract_step import *
import glob
import misc
import process_pool
import yaml
import os

from logging import getLogger

logger=getLogger('uap_logger')

class StringtieMerge(AbstractStep):

    '''
    # stringtie --merge <gtf.list> > outputpat/outputname
    '''

    def __init__(self, pipeline):
        super(StringtieMerge, self).__init__(pipeline)

        self.set_cores(2)

        # all .gft assemblies from all samples that have been produced with stringtie
        self.add_connection('in/assembling')
        # merged assembly 'merged.gft'
        self.add_connection('out/assembling') # merged.gtf
        self.add_connection('out/assemblies') # input assemblies txt file
        self.add_connection('out/log_stderr')
        self.add_connection('out/run_log')

        self.require_tool('stringtie')
        self.require_tool('printf')
        self.require_tool('mkdir')
        self.require_tool('mv')


        self.add_option('G', str, optional=True,
                        description='reference annotation to include in the merging (GTF/GFF3)')
        self.add_option('m', int, optional=True,
                        description='minimum input transcript length to include in the merge (default: 50)')
        self.add_option('c', int, optional=True,
                        description='minimum input transcript coverage to include in the merge (default: 0)')
        self.add_option('F', float, optional=True,
                        description='minimum input transcript FPKM to include in the merge (default: 1.0)')
        self.add_option('T', float, optional=True,
                        description='minimum input transcript TPM to include in the merge (default: 1.0)')
        self.add_option('f', float, optional=True,
                        description='minimum isoform fraction (default: 0.01)')
        self.add_option('g', int, optional=True,
                        description='gap between transcripts to merge together (default: 250)')
        self.add_option('l', str, optional=True,
                        description='name prefix for output transcripts (default: MSTRG)')


    def runs(self, run_ids_connections_files):
        
        # compile list of options
        options=['G', 'm', 'c', 'F', 'T', 'f', 'g', 'l']

        set_options = [option for option in options if \
                       self.is_option_set_in_config(option)]

        option_list = list()
        for option in set_options:
            if isinstance(self.get_option(option), bool):
                if self.get_option(option):
                    option_list.append('-%s' % option)
            else:
                option_list.append('-%s' % option)
                option_list.append(str(self.get_option(option)))

        # get all paths to the stringtie assemblies from each sample
        stringtie_sample_gtf = []
        for run_id in run_ids_connections_files.keys():
            stringtie_sample_gtf.append(run_ids_connections_files[run_id]['in/assembling'][0])

#        print '\n'.join(stringtie_sample_gtf)

        run_id = "merge"
        with self.declare_run(run_id) as run:
            
            # create the filename of the assemblies.txt file
            assemblies = [self.get_tool('printf'), '\n'.join(stringtie_sample_gtf)]
            # print assemblies
            
            assemblies_file = run.add_output_file('assemblies', '%s-stringtieMerge-assemblies.txt' % run_id, stringtie_sample_gtf)
           
            # print assemblies_file

            # 1. create assemblies file
            with run.new_exec_group() as exec_group:
                exec_group.add_command(assemblies, stdout_path = assemblies_file)
                with exec_group.add_pipeline() as stringtie_pipe:
                    res = run.add_output_file('assembling', '%s-stringtieMerge-merged.gtf' % run_id, stringtie_sample_gtf)
                    # print res
                    log_err_file = run.add_output_file('log_stderr', '%s-stringtieMerge-log_stderr.txt' % run_id, stringtie_sample_gtf)


                    # print assemblies_file
                    # res = run.add_output_file('unmapped', '%s-sstringtieMerge-merged.gtf' % run_id,
                    #     input_paths)
 
                    # 1. Create temporary directory for stringtie in- and output
                    # stringtieMerge_out_path = run.add_temporary_directory('stringtieMerge-out')
                    # with run.new_exec_group() as dir_exec_group:
                    #     mkdir = [self.get_tool('mkdir'), stringtieMerge_out_path]
                    #     dir_exec_group.add_command(mkdir)


                    stringtieMerge = [self.get_tool('stringtie'), '--merge']
                    stringtieMerge.extend(option_list)
                    stringtieMerge.append(assemblies_file)                        
                    stringtie_pipe.add_command(stringtieMerge, stderr_path = log_err_file, stdout_path = res)

            
            # # 1. create assemblies file
            # with run.new_exec_group() as as_exec_group:
            #     as_exec_group.add_command(assemblies, stdout_path = assemblies_file)

            # # assembling_file = run.add_output_file('assembling', '%s-stringtieMerge-merged.gtf' % run_id, stringtie_sample_gtf)

            # # print assembling_file
            # run_log_file = run.add_output_file('run_log', '%s-stringtieMerge-run.log' % run_id, stringtie_sample_gtf)
            # log_err_file = run.add_output_file('log_stderr', '%s-stringtieMerge-log_stderr.txt' % run_id, stringtie_sample_gtf)

            # stringtieMerge_out_path = run.add_temporary_directory('stringtieMerge-out')
            # stringtieMerge = [self.get_tool('stringtie'), '--merge']

            # stringtieMerge.append(">")
            # assembling_file = stringtieMerge_out_path + "/stringtieMerge-merged.gtf"
            # stringtieMerge.append(assembling_file)


            # # 2. Create temporary directory for stringtie in- and output
            # with run.new_exec_group() as dir_exec_group:
            #     mkdir = [self.get_tool('mkdir'), stringtieMerge_out_path]
            #     dir_exec_group.add_command(mkdir)

            # # 3. run stringtieMerge
            # with run.new_exec_group() as cm_exec_group:
            #     # stringtieMerge.append(assemblies_file)
            #     print(stringtieMerge)             
            #     cm_exec_group.add_command(stringtieMerge, stderr_path = log_err_file)

            # result_files = {
            #     'merged.gtf': assembling_file,
            #     'logs/run.log': run_log_file,
            # }
            
            # # 4. mv output files from temp dir to final location            
            # with run.new_exec_group() as mv_exec_group:
            #     for orig, dest_path in result_files.iteritems():
            #          orig_path = os.path.join(stringtieMerge_out_path, orig)
            #          mv = [self.get_tool('mv'), orig_path, dest_path]
            #          mv_exec_group.add_command(mv)
