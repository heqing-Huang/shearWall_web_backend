"""
# File       : layout_opt.py
# Time       ：2023/3/25 9:25
# Author     ：CR_X
# version    ：python 3.8
# Description：
"""

import numpy as np
from copy import deepcopy

from DoubleWallDesign.models import DetailedDesignResult
from RebarLayout.tools import get_truss_layout

def fitness(solution):
    '''
    最优位置适应度函数
    :return:
    '''
    x_round = deepcopy(solution)
    x_round = np.round(x_round)
    NY = np.size(x_round, 0) + 3
    position2 = [[]] * NY

    for i in range(NY):
        if i == 0:
            position2[0] += int(x_round[0])
        elif i == 1:
            position2[1] += int(x_round[1])
        elif i == 2:
            position2[2] = position2[2]
        elif i == 3:
            position2[3] = position2[3]
        elif i == 4:
            position2[4] += int(x_round[2])
        elif i == 5:
            position2[5] += int(x_round[3])
        elif i == 6:
            position2[6] += int(x_round[4])
        elif i == 7:
            position2[7] += int(x_round[5])
        elif i == 8:
            position2[8] = position2[8]
        elif i == 9:
            position2[9] += int(x_round[6])
        elif i == 10:
            position2[10] += int(x_round[7])
        elif i == 11:
            position2[11] += int(x_round[8])

    spac = np.array([])
    for i in range(1, len(position2)):
        spac = np.append(spac, [(position2[i] - position2[i - 1])])
    spac_sum = np.sum(spac)
    spac_mean = spac_sum / (NY - 1)

    deviation = np.sqrt(np.sum(np.power((spac - spac_mean), 2)) / (NY - 1))
    value = deviation
    return value

    return 1


def layout_opt(fcl_model, detailed_design_result: DetailedDesignResult) -> list:
    """
    桁架与预埋件排布优化
    :param detailed_design_result:  深化设计结果
    :return: 返回桁架钢筋的位置
    """


    action_1 = [1, 0, 0]
    action_2 = [-1, 0, 0]

    # check_rebar = deepcopy(1)
    # rebar_fcls = fcl_model.new_rebar_fcl(check_rebar, detailed_design_result.horizontal_rebars[0].diameter)
    # rebar_objs = fcl_model.new_obj(rebar_fcls)
    # check_ob = fcl_model.collision_check_add(rebar_objs)

    truss_spacing = [160, 320, 330, 350, 310, 330, 150]
    truss_lengths_plan = [2500, 2500, 2500, 2500, 2600, 2500]

    truss_layout = get_truss_layout(detailed_design_result,truss_spacing,truss_lengths_plan)

    return truss_layout
