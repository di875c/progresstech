# -*- coding: utf-8 -*-
import numpy as np


def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
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
            nodes[cbars[idx]] = [cbars[snd_number], cbars[2], cbars[5:8]]
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
    grids[line_list[1]] = dict([('coord', line_list[2:6]), ('property_number', []), ('thickness', [])])
    return grids


def cshell_read(line, grids):
    """
    :param line - text line from data file
    'CQUAD4','63014493','       1','64014677','64014678','64014684','64014680'
    :param grids - list of ends nodes for column creation
    :return '64012638': {'coord': [.......], 'property_number': ['     1','    3',....]]
    """
    line_list = [item for item in chunks(line, 8)]
    # print(line_list)
    for node in line_list[3:]:
        if node in grids: grids[node]['property_number'].append(line_list[2])
    # [grids[node].append(('property_number', line_list[2])) for node in line_list[3:] if node in grids]
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


def len_grip_calculate(node, grids):
    try:
        if grids[node]['thickness']:
            return max(grids[node]['thickness'])/2 + 5.0
        else:
            return 5.0
    except:
        return 5.0


def nc_generate(file_source, new_file, pshell_thick_check, *args, **kwargs):
    with open(file_source, 'r', encoding='utf-8') as infile:
        bars = {}
        nodes = {}
        grids = {}
        nodes_nuse = {}
        for line in infile:
            if line.startswith('CBAR'):
                nodes, nodes_nuse = bars_read(line, nodes, nodes_nuse)
            elif line.startswith('GRID'):
                grids = nodes_read(line, grids)
            elif line.startswith('CQUAD4') or line.startswith('CTRIA'):
                grids = cshell_read(line, grids)
            elif line.startswith('PSHELL'):
                grids = pshell_read(line, grids)

    # print(nodes, grids, sep='\n')
    print(pshell_thick_check, type(pshell_thick_check))
    idx = 0
    node_lines = []
    cbeam_lines = []
    for node, node_list in nodes.items():
        idx += 1
        vector = np.sum(
            [np.array(grids[node]['coord'][1:4], dtype=float), -np.array(grids[node_list[0]]['coord'][1:4], dtype=float)], axis=0)
        len_grip = 5 if pshell_thick_check == 0 else len_grip_calculate(node, grids)
        coords = np.sum(
            [np.array(grids[node]['coord'][1:4], dtype=float), vector / (np.linalg.norm(vector) / len_grip)], axis=0)
        node_line = ['GRID', str(idx), grids[node]['coord'][0]]
        [node_line.append('{0:.2f}'.format(coord)) for coord in coords]
        node_lines.append(node_line)
        cbeam_line = ['CBAR', str(idx + 10000), node_list[1], node, str(idx), *node_list[2]]
        cbeam_lines.append(cbeam_line)

    with open(new_file, 'w') as outfile:
        for line in node_lines:
            outfile.write(','.join(line) + '\n')
        for line in cbeam_lines:
            outfile.write(','.join(line) + '\n')


if __name__ == '__main__':
    file_source = "F:/PT/test_task/connectors/connectors0.bdf"
    new_file = "F:/PT/test_task/connectors/connectors11.bdf"
    nc_generate(file_source, new_file)