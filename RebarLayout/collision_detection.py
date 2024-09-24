"""
# File       : collision_detection.py
# Time       ：2022/9/21 10:00
# Author     ：CR_X
# version    ：python 3.6
# Description：
"""
import copy
import math
from typing import List

import fcl
import numpy as np
from RebarLayout.fcl_models import Rebar_fcl, Box_fcl, Diagonal_fcl, Cylinder_fcl
from RebarLayout.tools import rotation_matrix_from_vectors

class ShearWallFCLModel():
    def __init__(self):
        self.geoms = []  # 几何体列表
        self.objs = []  # 对象列表

    def add_rebar(self, rebar, dia):
        objs = []
        for i in range(len(rebar) - 1):
            line = np.array([rebar[i], rebar[i + 1]])
            x = line[1][0] - line[0][0]
            y = line[1][1] - line[0][1]
            z = line[1][2] - line[0][2]
            length = np.sqrt(np.sum(np.square(np.array([x, y, z])))) - dia
            original_direction = np.array([[0, 0, 1]])
            final_direction = np.array([[x, y, z]])

            transformation = rotation_matrix_from_vectors(original_direction, final_direction)

            position = np.array([(line[1][0] + line[0][0]) / 2,
                                 (line[1][1] + line[0][1]) / 2,
                                 (line[1][2] + line[0][2]) / 2])
            obj = Rebar_fcl(diameter=dia, length=length, transformation=transformation, position=position)
            objs.append(obj)
        self.add_obj(objs)

    def add_obj(self, objs_new):
        for obj_new in objs_new:
            if obj_new.type == "Cylinder":
                geo_new = fcl.Cylinder(obj_new.radius, obj_new.length)
                T = np.array(obj_new.position)
                obj_new = fcl.CollisionObject(geo_new, fcl.Transform(T))
                self.geoms.append(geo_new)
                self.objs.append(obj_new)
            elif obj_new.type == "Box":
                geo_new = fcl.Box(obj_new.x, obj_new.y, obj_new.z)
                R = obj_new.transformation
                T = obj_new.position
                obj_new = fcl.CollisionObject(geo_new, fcl.Transform(R, T))
                self.geoms.append(geo_new)
                self.objs.append(obj_new)
            elif obj_new.type == "Rebar":
                geo_new = fcl.Cylinder(obj_new.diameter / 2, obj_new.length)
                R = obj_new.transformation
                T = obj_new.position
                obj_new = fcl.CollisionObject(geo_new, fcl.Transform(R, T))
                self.geoms.append(geo_new)
                self.objs.append(obj_new)

    def new_rebar_fcl(self, rebar, dia):
        rebar_fcls = []
        for i in range(len(rebar) - 1):
            line = np.array([rebar[i], rebar[i + 1]])
            x = line[1][0] - line[0][0]
            y = line[1][1] - line[0][1]
            z = line[1][2] - line[0][2]
            length = np.sqrt(np.sum(np.square(np.array([x, y, z])))) - dia
            original_direction = np.array([[0, 0, 1]])
            final_direction = np.array([[x, y, z]])

            transformation = rotation_matrix_from_vectors(original_direction, final_direction)

            position = np.array([(line[1][0] + line[0][0]) / 2,
                                 (line[1][1] + line[0][1]) / 2,
                                 (line[1][2] + line[0][2]) / 2])
            rebar_fcl = Rebar_fcl(diameter=dia, length=length, transformation=transformation, position=position)
            rebar_fcls.append(rebar_fcl)
        return rebar_fcls

    def new_obj(self, objs_new):
        objs = []
        for obj_new in objs_new:
            if obj_new.type == "Cylinder":
                geo_new = fcl.Cylinder(obj_new.radius, obj_new.length)
                T = np.array(obj_new.position)
                obj_new = fcl.CollisionObject(geo_new, fcl.Transform(T))
                objs.append(obj_new)
            elif obj_new.type == "Rebar":
                geo_new = fcl.Cylinder(obj_new.diameter / 2, obj_new.length)
                R = obj_new.transformation
                T = obj_new.position
                obj_new = fcl.CollisionObject(geo_new, fcl.Transform(R, T))
                objs.append(obj_new)
            elif obj_new.type == "Box":
                geo_new = fcl.Box(obj_new.x, obj_new.y, obj_new.z)
                T = obj_new.position
                R = obj_new.transformation
                obj_new = fcl.CollisionObject(geo_new, fcl.Transform(R, T))
                objs.append(obj_new)
        return objs

    def collision_check_add(self, objs_new):
        '''
        :param objs_new: [obj, obj]
        :return:
        '''
        # 创建manager
        manager_orginal = fcl.DynamicAABBTreeCollisionManager()  # 实例化
        manager_new = fcl.DynamicAABBTreeCollisionManager()  # 实例化

        manager_orginal.registerObjects(self.objs)  # 注册
        manager_new.registerObjects(objs_new)  # 注册

        manager_orginal.setup()
        manager_new.setup()
        # 创建碰撞请求结构
        crequest = fcl.CollisionRequest(num_max_contacts=10000, enable_contact=True)
        cresult = fcl.CollisionResult()
        cdata = fcl.CollisionData(crequest, cresult)

        # 运行碰撞请求
        manager_orginal.collide(manager_new, cdata, fcl.defaultCollisionCallback)

        if len(cdata.result.contacts) != 0:
            for contact in cdata.result.contacts:
                # 提取contacts中的碰撞几何
                coll_geom_0 = contact.o1  # 碰撞是成对出现的所有是o1,o2
                coll_geom_1 = contact.o2
                # print(coll_geom_0, coll_geom_1, contact.pos)
            return True
        else:
            return False
    def collision_agent_rebar(self, agent):
        # 增加智能体
        objs_new = []
        for i in range(len(agent.points) - 1):
            line = np.array([agent.points[i], agent.points[i + 1]])
            x = line[1][0] - line[0][0]
            y = line[1][1] - line[0][1]
            z = line[1][2] - line[0][2]
            length = np.sqrt(np.sum(np.square(np.array([x, y, z])))) - agent.size
            original_direction = np.array([[0, 0, 1]])
            final_direction = np.array([[x, y, z]])

            R = rotation_matrix_from_vectors(original_direction, final_direction)
            T  = np.array([(line[1][0] + line[0][0]) / 2,
                                 (line[1][1] + line[0][1]) / 2,
                                 (line[1][2] + line[0][2]) / 2])
            geom = fcl.Sphere(math.ceil(agent.size / 2))
            geo_new = fcl.Cylinder(math.ceil(agent.size / 2), length)
            obj = fcl.CollisionObject(geo_new, fcl.Transform(R, T))
            objs_new.append(obj)

        # 创建manager
        manager_orginal = fcl.DynamicAABBTreeCollisionManager()  # 实例化
        manager_new = fcl.DynamicAABBTreeCollisionManager()  # 实例化

        manager_orginal.registerObjects(self.objs)  # 注册
        manager_new.registerObjects(objs_new)  # 注册

        manager_orginal.setup()
        manager_new.setup()
        # 创建碰撞请求结构
        crequest = fcl.CollisionRequest(num_max_contacts=10000, enable_contact=True)
        cdata = fcl.CollisionData(crequest, fcl.CollisionResult())

        # 运行碰撞请求
        manager_orginal.collide(manager_new, cdata, fcl.defaultCollisionCallback)

        if len(cdata.result.contacts) != 0:
            for contact in cdata.result.contacts:
                # 提取contacts中的碰撞几何
                coll_geom_0 = contact.o1  # 碰撞是成对出现的所有是o1,o2
                coll_geom_1 = contact.o2
                # print(coll_geom_0, coll_geom_1, contact.pos)
            return True
        else:
            return False
