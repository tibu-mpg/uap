#!./python_env/bin/python

# usage: ./monitor-disk-io.py ./run-locally.py [task ID]

import sys
import copy
import subprocess
import re
import yaml

if len(sys.argv) > 1:
    args = ["strace", "-f", "-o", '/dev/stderr']
    args.extend(sys.argv[1:])
    p = subprocess.Popen(args, stderr = subprocess.PIPE)
    strace_out = p.stderr
    with open('strace-out.txt', 'w') as f:
        for line in strace_out:
            f.write(line)
    exit(0)

strace_out = open('strace-out.txt', 'r')

path_for_pid_and_fd = {}
stats = {}

def handle_line(pid, line):
    m = re.search('^(\w+)\((.*)\)\s+=\s+(.+)$', line)
    if m:
        command = str(m.group(1))
        args = str(m.group(2)).strip()
        retval = str(m.group(3))
        if command == 'clone':
            #print(pid + ' ' + command + ' ' + args + ' ' + retval)
            for _ in path_for_pid_and_fd[pid].keys():
                if not retval in path_for_pid_and_fd:
                    path_for_pid_and_fd[retval] = {}
                path_for_pid_and_fd[retval][_] = copy.copy(path_for_pid_and_fd[pid][_])
                #if retval == '17893':
                    #print('------')
                    #print(yaml.dump(path_for_pid_and_fd[retval], default_flow_style = False))
                    #print('------')
        if command == 'dup2':
            #print(pid + ' ' + command + ' ' + args + ' ' + retval)
            fds = [_.strip() for _ in args.split(',')]
            try:
                path_for_pid_and_fd[pid][fds[1]] = path_for_pid_and_fd[pid][fds[0]]
            except:
                path_for_pid_and_fd[pid][fds[1]] = '[unknown path]'

        if command == 'open':
            #print(pid + ' ' + command + ' ' + args + ' ' + retval)
            if not pid in path_for_pid_and_fd:
                path_for_pid_and_fd[pid] = {}
            path_for_pid_and_fd[pid][retval] = re.search("^\\\"([^\\\"]+)\\\"", args).group(1)
        if command == 'read' or command == 'write':
            #print(pid + ' ' + command + ' ' + args + ' ' + retval)
            fd = None
            size = None
            m = re.search("^(\d+),", args)
            if m:
                fd = m.group(1)
            m = re.search("\s+(\d+)$", args)
            if m:
                size = m.group(1)
            if fd and size:
                sizek = int(size) / 1024
                path = '[unknown path]'
                if fd == '0':
                    path = 'stdin'
                elif fd == '1':
                    path = 'stdout'
                elif fd == '2':
                    path = 'stderr'
                else:
                    try:
                        path = path_for_pid_and_fd[pid][fd]
                    except:
                        pass
                if not path in stats:
                    stats[path] = {'read': {}, 'write': {}}
                if not sizek in stats[path][command]:
                    stats[path][command][sizek] = 0
                stats[path][command][sizek] += 1
                #print(path + ": " + command + " " + str(sizek) + " k")
                #exit(1)

def size_to_cat(s):
    if s < 32:
        return (0, '< 32k ')
    elif s < 128:
        return (1, '< 128k ')
    elif s < 1024:
        return (2, '< 1024k ')
    elif s < 4096:
        return (3, '< 4096k ')
    else:
        return (4, '4096k+')

line_buffer = {}
for line in strace_out:
    line = line.strip()
    pid = str(re.search('^(\d+)\s', line).group(1))
    line = line[line.index(' ') + 1:]
    if 'resumed>' in line:
        line = re.sub(r'\<.+\>', '', line)
        line_buffer[pid] += line
        handle_line(pid, line_buffer[pid])
    else:
        if '<unfinished' in line:
            line = re.sub(r'\<.+\>', '', line)
            line_buffer[pid] = line
        else:
            line_buffer[pid] = line
            handle_line(pid, line_buffer[pid])

for path in stats.keys():
    cancel = False
    for _ in ['.pyc', 'stdin', 'stdout', 'stderr']:
        if _ in path:
            cancel = True
            continue
    if cancel:
        continue
    printed_path = False
    for mode in ['read', 'write']:
        printed_mode = False
        hist = {}
        mod_size = {}
        for _, count in stats[path][mode].items():
            mod_size[size_to_cat(_)] = count
        for key in sorted(mod_size.keys(), reverse=True):
            size = key[1]
            if key[0] == 0:
                continue
            if not printed_path:
                print(path)
                printed_path = True
            if not printed_mode:
                print(mode.upper() + 'S:')
                printed_mode = True
            print('{:>8} {:>5}x'.format(str(size), str(mod_size[key])))