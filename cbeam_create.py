# -*- coding: utf-8 -*-
import numpy as np


def log_file(func):
    def _wrapper(*args, **kwargs):
        _log_file = args[2]
        with open(_log_file, 'a') as outfile:
            _node, _grids = args[0], args[1]
            _offset = max(_grids[_node]['offset']) if _grids[_node]['offset'] else 0
            if _offset > 0:
                outfile.write('For node id {} offset {} found and not taken into account\n'.format(_node, _offset))
                if _offset + max(_grids[_node]['thickness'])/2 > 5.0:
                    outfile.write('Warning! For node id {} offset + thick/2 > 5.0. '
                                  'The connected element has to be revised!\n'.format(_node))
        return func(*args, **kwargs)
    return _wrapper


def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    s = s.replace('\n', '')
    for start in range(0, len(s), n):
        yield s[start:start+n]


def bars_read(line, nodes, nodes_nuse):
    """add to global dictionary 'nodes' new item as example below:
    '64012638': ['74000033', '      13', ['     0.0', '     1.0', '     0.0']]
    """
    cbars = [item for item in chunks(line, 8)]
    for idx in range(3, 5):
        #             print('node: {} in nodes {}'.format(cbars[idx], cbars[idx] in nodes))
        if cbars[idx] not in nodes or cbars[idx] in nodes_nuse:
            snd_number = 4 if idx == 3 else 3
            nodes[cbars[idx]] = [cbars[snd_number], cbars[2], cbars[5:8], idx]
        elif cbars[idx] not in nodes_nuse:
            del nodes[cbars[idx]]
            nodes_nuse[cbars[idx]] = True
    return nodes, nodes_nuse


def nodes_read(line, grids):
    """add to global dictionary 'grids' new item as example below:
        '64012638': ['        ', '33844.58', ' -461.39', '2445.076']
        :return '64012638': {'coord': ['        ', '33844.58', ' -461.39', '2445.076'], 'property_number': [],
        'thickness':[]}
    """
    line_list = [item for item in chunks(line, 8)]
    grids[line_list[1]] = dict([('coord', line_list[2:6]), ('property_number', []), ('thickness', []), ('offset', [])])
    return grids


def cshell_read(line, grids):
    """
    :param line - text line from data file
    'CQUAD4','63014493','       1','64014677','64014678','64014684','64014680', 'Theta ', ' Z_OFF'
    :param grids - list of ends nodes for column creation
    :return '64012638': {'coord': [.......], 'property_number': ['     1','    3',....], 'offset': ['     1','    3',.]]
    """
    line_list = [item for item in chunks(line, 8)]
    # print(line_list)
    for node in line_list[3:]:
        if node in grids:
            grids[node]['property_number'].append(line_list[2])
            if len(line_list) > 7: # check that offset is in element card
                grids[node]['offset'].append(abs(float(line_list[-1])))
    return grids


def pshell_read(line, grids):
    """
    :param line - text line from data file
    'CQUAD4','63014493','       1','64014677','64014678','64014684','64014680'
    :param grids - list of ends nodes for column creation
    :return '64012638': {'coord': [.......], 'property_number': [....], 'thickness': [1.3, 2.4, 3.0, ....]]
    """
    line_list = [item for item in chunks(line, 8)]
    # print(line_list)
    for node, nlist in grids.items():
        for property_n in nlist['property_number']:
            if property_n == line_list[1]: nlist['thickness'].append(float(line_list[3]))
    return grids


@log_file
def len_grip_calculate(node, grids, *args, **kwargs):
    try:
        if grids[node]['thickness']:
            return max(grids[node]['thickness'])/2 + 5.0
        else:
            return 5.0
    except:
        return 5.0


def nc_generate(file_source, new_file, pshell_thick_check, chaos_check=False, *args, **kwargs):
    log_file_name = new_file[:-4] + ".log"
    nodes = {}
    grids = {}
    nodes_nuse = {}
    if chaos_check:
        with open(file_source, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('CBAR'):
                    nodes, nodes_nuse = bars_read(line, nodes, nodes_nuse)
                elif line.startswith('GRID'):
                    grids = nodes_read(line, grids)
                elif line.startswith('CQUAD4') or line.startswith('CTRIA'):
                    grids = cshell_read(line, grids)
                elif line.startswith('PSHELL'):
                    grids = pshell_read(line, grids)
    else:
        with open(file_source, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('CBAR'):
                    nodes, nodes_nuse = bars_read(line, nodes, nodes_nuse)
        with open(file_source, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('GRID'):
                    grids = nodes_read(line, grids)
        with open(file_source, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('CQUAD4') or line.startswith('CTRIA'):
                    grids = cshell_read(line, grids)
        with open(file_source, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line.startswith('PSHELL'):
                    grids = pshell_read(line, grids)
    with open(log_file_name, 'w') as outfile:
        outfile.write('Total cbars created {}\n'.format(len(nodes)))
    idx = 0
    node_lines = []
    cbeam_lines = []
    number_more_5 = 0
    for node, node_list in nodes.items():
        idx += 1
        vector = np.sum(
            [np.array(grids[node]['coord'][1:4], dtype=float), -np.array(grids[node_list[0]]['coord'][1:4], dtype=float)], axis=0)
        len_grip = 5 if pshell_thick_check == 0 else len_grip_calculate(node, grids, log_file_name)
        if len_grip > 5: number_more_5 += 1
        coords = np.sum(
            [np.array(grids[node]['coord'][1:4], dtype=float), vector / (np.linalg.norm(vector) / len_grip)], axis=0)
        node_line = ['GRID', str(idx), grids[node]['coord'][0]]
        [node_line.append('{0:.2f}'.format(coord)) for coord in coords]
        node_lines.append(node_line)
        if node_list[3] != 3: #правильный обход узлов
            cbeam_line = ['CBAR', str(idx + 10000), node_list[1], node, str(idx), *node_list[2]]
        else:
            cbeam_line = ['CBAR', str(idx + 10000), node_list[1], str(idx), node, *node_list[2]]
        cbeam_lines.append(cbeam_line)

    with open(new_file, 'w') as outfile:
        for line in node_lines:
            outfile.write(','.join(line) + '\n')
        for line in cbeam_lines:
            outfile.write(','.join(line) + '\n')

    with open(log_file_name, 'a') as outfile:
        outfile.write('Number cbars with length more than 5: {}'.format(number_more_5))


if __name__ == '__main__':
    file_source = "F:/PT/script_test/test_2.bdf"
    new_file = "F:/PT/script_test/assembly_shell_for_pen_add.bdf"
    nc_generate(file_source, new_file, True, False)