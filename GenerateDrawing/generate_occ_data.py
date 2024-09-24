import copy

from GenerateDrawing.tool import transform_cartesian_to_point,form_truss_stirrup_shape_data
import math

def generate_double_wall_geometry(ifc_file,entity_name,double_wall_geo):
    """
    :param ifc_file: IFC文件
    :param entity_name: 实体名称
    :param double_wall_geo: 双皮剪力墙实体
    :return:
    """
    double_wall_set = ifc_file.by_type(entity_name)
    double_wall = double_wall_set[0]  # 获取单个双皮剪力墙
    geometry_sets = double_wall.Representation.Representations[0]
    double_wall_geo.inner_side_wall_height = geometry_sets.Items[0].Depth
    double_wall_geo.outer_side_wall_height = geometry_sets.Items[1].Depth
    inner_area_profile = transform_cartesian_to_point(geometry_sets.Items[0].SweptArea.OuterCurve.Points)
    outer_area_profile = transform_cartesian_to_point(geometry_sets.Items[1].SweptArea.OuterCurve.Points)
    double_wall_geo.inner_side_wall_width = inner_area_profile[1][0]
    double_wall_geo.inner_side_wall_thick = inner_area_profile[2][1]
    double_wall_geo.outer_side_wall_width = outer_area_profile[1][0]
    double_wall_geo.outer_side_wall_thick = outer_area_profile[2][1]
    # 获取双皮剪力墙的厚度
    inner_position = geometry_sets.Items[0].Position.Location[0]
    outer_position = geometry_sets.Items[1].Position.Location[0]
    double_wall_geo.inner_hole_thick = outer_position[1]-double_wall_geo.inner_side_wall_thick # 双皮剪力墙孔洞厚度
    return double_wall_geo


class OCCData(object):
    """
    获取OCC数据
    """
    def __init__(self,ifc_file,double_wall_geo):
        self.ifc_file = ifc_file
        self.double_wall_geo = double_wall_geo
    def get_ifc_solid_element(self,entity_name):
        """
        获取IFC文件实体元素
        :param file: IFC文件
        :param name: 实体名称
        :return:
        """
        solid_info = []
        double_wall_set = self.ifc_file.by_type(entity_name)
        double_wall = double_wall_set[0]  # 获取单个双皮剪力墙
        geometry_sets = double_wall.Representation.Representations[0]
        for num in range(len(geometry_sets.Items)):
            geometry = geometry_sets.Items[num]
            geometry_info = {}
            geometry_info["position"] = geometry.Position.Location[0] # 获取轴心点
            geometry_info["height"] = geometry.Depth  # 获取实体拉伸方向长度
            geometry_info["profile"] = transform_cartesian_to_point(geometry.SweptArea.OuterCurve.Points)  # 封闭轮廓平面坐标
            geometry_info["direction"] = geometry.ExtrudedDirection.DirectionRatios  # 拉伸方向
            solid_info.append(geometry_info)
        return solid_info


    def get_ifc_construct_horizon_rebar(self,entity_name,name):
        """
        获取IFC文件构造水平钢筋信息
        :param file: IFC文件
        :param entity_name: IFC实体名称
        :param name:  名称
        :return:
        """
        construct_rebar = self.ifc_file.by_type(entity_name)
        profile_sets = []
        geometry_info = {}
        for special_rebar in construct_rebar:
            if special_rebar.Name == name:
                geometry_set = special_rebar.Representation.Representations[0].Items[0]
                curve_points = geometry_set.Directrix.Points.CoordList
                start_point = curve_points[0]
                end_point = curve_points[1]
                if start_point[1]==end_point[1] and start_point[2]==end_point[2]: # 判断为水平钢筋
                    geometry_info["Radius"] = geometry_set.Radius
                    profile_sets.append(list(curve_points))
        geometry_info["profile"] = profile_sets
        return geometry_info

    def get_ifc_construct_vertical_rebar(self,entity_name,name):
        """
        获取IFC文件构造竖向钢筋信息
        :param file: IFC文件
        :param entity_name: IFC实体名称
        :param name:  名称
        :return:
        """
        construct_rebar = self.ifc_file.by_type(entity_name)
        profile_sets = []
        geometry_info = {}
        for special_rebar in construct_rebar:
            if special_rebar.Name == name:
                geometry_set = special_rebar.Representation.Representations[0].Items[0]
                curve_points = geometry_set.Directrix.Points.CoordList
                start_point = curve_points[0]
                end_point = curve_points[1]
                if start_point[0]==end_point[0] and start_point[1]==end_point[1]: # 判断为水平钢筋
                    geometry_info["Radius"] = geometry_set.Radius
                    profile_sets.append(list(curve_points))
        geometry_info["profile"] = profile_sets
        return geometry_info

    def get_ifc_truss_rebar(self,entity_name,name):
        """
        获取IFC文件桁架钢筋信息
        :param file: IFC文件
        :param entity_name: IFC实体名称
        :param name:  名称
        :return:
        """
        truss_rebar = self.ifc_file.by_type(entity_name)
        profile_sets = []  # 所有线段点
        geometry_info = {}
        for special_rebar in truss_rebar:
            # 单榀桁架筋
            if special_rebar.Name == name:
                single_profile = []
                geometry_set_length = len(special_rebar.Representation.Representations)
                geometry_info["Radius"] = special_rebar.Representation.Representations[0].Items[0].Radius
                for num_i in range(geometry_set_length):  # 对单榀中每一类钢筋进行判断
                    geometry_set = special_rebar.Representation.Representations[num_i].Items[0]
                    # 获取所有线段点
                    current_profile = geometry_set.Directrix.Points.CoordList
                    if len(current_profile)>2:  # 为桁架筋，按照桁架筋的方法取数据
                        current_profile = form_truss_stirrup_shape_data(current_profile)
                    single_profile.append(list(current_profile))
                profile_sets.append(single_profile)

        geometry_info["profile"] = profile_sets
        # profile_sets_1 = []  # 所有线段点
        # geometry_info_1 = {}
        # for special_rebar in truss_rebar:
        #     if special_rebar.Name == name:
        #         geometry_set = special_rebar.Representation.Representations[0].Items[0]
        #         geometry_info_1["Radius"] = geometry_set.Radius
        #         geometry_representation = special_rebar.Representation.Representations
        #         single_profile = []
        #         # 获取所有线段点
        #         for num in range(len(geometry_representation)):
        #             single_geometry = geometry_representation[num]
        #             current_profile = single_geometry.Items[0].Directrix.Points.CoordList
        #             single_profile.append(list(current_profile))
        #         profile_sets_1.append(single_profile)
        # geometry_info_1["profile"] = profile_sets_1
        return geometry_info


    def get_ifc_truss_top_long_rebar(self,entity_name,name):
        """
        获取IFC桁架筋上弦纵筋数据
        :param entity_name:
        :param name:
        :return:
        """
        geometry_info = self.get_ifc_truss_rebar(entity_name,name)
        # 筛选出上弦和下弦钢筋
        total_truss_long_rebar_info = {}
        total_truss_long_rebar_info["Radius"] = geometry_info["Radius"]
        total_truss_long_rebar_profile = geometry_info["profile"]
        total_profile_points = []
        mean_y = 0
        for single_truss in total_truss_long_rebar_profile:
            for rebar in single_truss:
                if len(rebar) == 2:
                    curr_rebar = copy.deepcopy(rebar)
                    total_profile_points.append(curr_rebar)
                    mean_y += curr_rebar[0][1]
        # 筛选上弦钢筋
        top_truss_long_rebar_points = []
        mean_y = mean_y/len(total_profile_points)
        for rebar in total_profile_points:
            if rebar[0][1] > mean_y:
                top_truss_long_rebar_points.append(copy.deepcopy(rebar))
        total_truss_long_rebar_info["profile"] = top_truss_long_rebar_points
        return total_truss_long_rebar_info

    def get_ifc_truss_bottom_long_rebar(self,entity_name,name):
        """
        获取IFC桁架筋下弦纵筋数据
        :param entity_name:
        :param name:
        :return:
        """
        geometry_info = self.get_ifc_truss_rebar(entity_name,name)
        # 筛选出上弦和下弦钢筋
        total_truss_long_rebar_info = {}
        total_truss_long_rebar_info["Radius"] = geometry_info["Radius"]
        total_truss_long_rebar_profile = geometry_info["profile"]
        total_profile_points = []
        mean_y = 0
        for single_truss in total_truss_long_rebar_profile:
            for rebar in single_truss:
                if len(rebar) == 2:
                    curr_rebar = copy.deepcopy(rebar)
                    total_profile_points.append(curr_rebar)
                    mean_y += curr_rebar[0][1]
        # 筛选下弦钢筋
        bottom_truss_long_rebar_points = []
        mean_y = mean_y/len(total_profile_points)
        for rebar in total_profile_points:
            if rebar[0][1] < mean_y:
                bottom_truss_long_rebar_points.append(copy.deepcopy(rebar))
        total_truss_long_rebar_info["profile"] = bottom_truss_long_rebar_points
        return total_truss_long_rebar_info

    def get_ifc_truss_stirrup_rebar(self,entity_name,name):
        """
        获取IFC桁架筋马镫筋数据
        :param entity_name:
        :param name:
        :return:
        """
        geometry_info = self.get_ifc_truss_rebar(entity_name,name)
        truss_info = {}
        truss_info["Radius"] = geometry_info["Radius"]
        geometry_profile = geometry_info["profile"]
        total_profile = []
        for single_truss in geometry_profile:
            curr_truss = []
            for curr_rebar in single_truss:
                if len(curr_rebar)>2:
                    curr_truss.append(copy.deepcopy(curr_rebar))
            total_profile.append(curr_truss)
        truss_info["profile"] = total_profile
        return truss_info

    def get_ifc_support_bolt_info(self):
        """
        获取斜撑螺栓信息：在内墙
        :return:
        """
        support_bolt_info = {}

        plate_width = 50  # 锚板宽度
        plate_height = 50  # 锚板高度
        plate_thick = 5  # 锚板厚度
        bolt_inner_radius = 8  # 锚栓内径
        bolt_outer_radius = 12  # 锚栓外径
        bolt_length = 30  # 锚栓长度
        stretch_dir = (0,1,0)  # 拉伸方向
        name = "预埋螺母套筒"
        number = 4
        notes = "M"+str(bolt_inner_radius*2)+"x"+str(bolt_length)+"端头带锚板"
        number_list = "MJ2"
        left_edge_distance = 220
        right_edge_distance = self.double_wall_geo.inner_side_wall_width-left_edge_distance
        bottom_height = 500
        top_height = self.double_wall_geo.inner_side_wall_height*2/3
        bolt_loc = [[left_edge_distance,0,bottom_height],[right_edge_distance,0,bottom_height],[left_edge_distance,0,top_height],[right_edge_distance,0,top_height]]
        bolt_profile = [(0,0,0),(0,bolt_length,0)]
        plate_shape = [(-plate_width/2,bolt_length,-plate_height/2),(plate_width/2,bolt_length,-plate_height/2),
                           (plate_width/2,bolt_length,plate_height/2),
                           (-plate_width/2,bolt_length,plate_height/2),(-plate_width/2,bolt_length,-plate_height/2)]
        plate_profile = [(0,bolt_length,0),(0,bolt_length+plate_thick,0)]
        support_bolt_info["plate_width"] = plate_width
        support_bolt_info["plate_height"] = plate_height
        support_bolt_info["plate_thick"] = plate_thick
        support_bolt_info["plate_shape"] = plate_shape
        support_bolt_info["plate_profile"] = plate_profile
        support_bolt_info["bolt_inner_radius"] = bolt_inner_radius
        support_bolt_info["bolt_outer_radius"] = bolt_outer_radius
        support_bolt_info["bolt_profile"] = bolt_profile
        support_bolt_info["bolt_length"] = bolt_length
        support_bolt_info["bolt_loc"] = bolt_loc
        support_bolt_info["stretch_dir"] = stretch_dir
        support_bolt_info["name"] = name
        support_bolt_info["number"] = number
        support_bolt_info["notes"] = notes
        support_bolt_info["number_list"] = number_list

        return support_bolt_info

    def get_ifc_pvc_hole_info(self):
        """
        从IFC中获取PVC管道孔洞信息
        :return:
        """
        pvc_hole_info = {}
        hole_diam = 20  # 孔洞直径
        hole_length = 250  # 孔洞长度
        direction = (0,1,0) # 拉伸方向
        left_edge_distance = 70
        right_edge_distance = self.double_wall_geo.inner_side_wall_width-left_edge_distance
        hole_loc = [[left_edge_distance,0,150],[left_edge_distance,0,600],[left_edge_distance,0,1050],[left_edge_distance,0,1520],
                    [left_edge_distance,0,1950],[left_edge_distance,0,2400],\
                    [right_edge_distance,0,150],[right_edge_distance,0,600],[right_edge_distance,0,1050],[right_edge_distance,0,1520],
                    [right_edge_distance,0,1950],[right_edge_distance,0,2400]]
        hole_profile = [[(0,0,0),(0,hole_length,0)]]
        name = "预埋PVC管"
        number = len(hole_loc)
        notes = "D="+str(hole_diam)
        number_list = "LK1"
        pvc_hole_info["hole_diam"] = hole_diam
        pvc_hole_info["hole_length"] = hole_length
        pvc_hole_info["hole_profile"] = hole_profile
        pvc_hole_info["hole_loc"] = hole_loc
        pvc_hole_info["direction"] = direction
        pvc_hole_info["name"] = name
        pvc_hole_info["number"] = number
        pvc_hole_info["notes"] = notes
        pvc_hole_info["number_list"] = number_list
        return pvc_hole_info

    def get_ifc_hoist_embedded_part_info(self):
        """
        从IFC中获取吊装预埋件信息:d---一级钢,D----二级钢,e----三级钢,E----四级钢
        """
        hoist_embedded_info = {}
        name = "吊环"
        number = 2
        diam = 16
        left_project_length = 669  # 左侧投影总长度
        left_line_length = 560  # 左侧直线长度
        top_project_width = 200 # 竖向投影宽度
        left_edge = 300  # 吊装预埋件左侧边距
        right_edge = 300
        horizon_height_1 = -(left_project_length-(320+diam/2))
        horizon_height_2 = -(left_project_length-(520+diam/2))
        notes = "D"+str(diam)+"钢筋"
        number_list = "MJ1"
        arc_radius = 40
        # 吊件中心到两边圆弧中心的距离
        edge_h = top_project_width/2-(arc_radius+diam)
        edge_v = (left_project_length-left_line_length)
        # 左侧圆弧角度
        left_arc_angle_1 = math.pi*7/9
        left_arc_angle_2 = math.pi*8/9
        left_arc_angle_3 = math.pi
        # 中部圆弧角度
        middle_arc_angle_1 = math.pi*2/9
        middle_arc_angle_2 = math.pi/2
        middle_arc_angle_3 = math.pi*7/9
        # 右侧圆弧角度
        right_arc_angle_1 = 0
        right_arc_angle_2 = math.pi/9
        right_arc_angle_3 = math.pi*2/9
        # 获取轴线段---注意cos的正负
        left_seg = [(0,-(top_project_width-diam)/2,-left_project_length),(0,-(top_project_width-diam)/2,-(left_project_length-left_line_length))]
        radius_rebar_radius = diam/2 + arc_radius
        left_arc = [(0,-(top_project_width-diam)/2,-(left_project_length-left_line_length)),
                    (0,-edge_h+radius_rebar_radius*math.cos(left_arc_angle_2),-edge_v+radius_rebar_radius*math.sin(left_arc_angle_2)),
                    (0,-edge_h+radius_rebar_radius*math.cos(left_arc_angle_1),-edge_v+radius_rebar_radius*math.sin(left_arc_angle_1))]
        left_arc_line = [left_arc[-1],
                         (0,(arc_radius+diam/2)*math.cos(middle_arc_angle_3),-(arc_radius+diam-(arc_radius+diam/2)*math.sin(middle_arc_angle_3)))]
        middle_arc = [left_arc_line[-1],(0,0,-diam/2),
                      (0,(arc_radius+diam/2)*math.cos(middle_arc_angle_1),-(arc_radius+diam-(arc_radius+diam/2)*math.sin(middle_arc_angle_1)))]
        right_arc_line = [middle_arc[-1],(0,(edge_h+radius_rebar_radius*math.cos(right_arc_angle_3)),-edge_v+radius_rebar_radius*math.sin(right_arc_angle_3))]
        right_arc = [right_arc_line[-1],(0,(edge_h+radius_rebar_radius*math.cos(right_arc_angle_2)),-edge_v+radius_rebar_radius*math.sin(right_arc_angle_2)),
                     (0,(top_project_width-diam)/2,-(left_project_length-left_line_length))]
        middle_seg = [(0,-(top_project_width-diam)/2,-(left_project_length-left_line_length)),(0,0,0),
                      (0,(top_project_width-diam)/2,-(left_project_length-left_line_length))]
        right_seg = [(0,(top_project_width-diam)/2,-(left_project_length-left_line_length)),
                     (0,(top_project_width-diam)/2,-left_project_length)]
        exterior_seg = [(0,-(top_project_width-diam)/2,-left_project_length),(0,-(top_project_width-diam)/2,-(left_project_length-left_line_length)),
                        (0, 0, 0),(0, (top_project_width - diam) / 2, -(left_project_length - left_line_length)),(0,(top_project_width-diam)/2,-left_project_length)
        ]
        horizon_seg_1 = [(0,-(top_project_width-2*diam)/2,horizon_height_1),(0,(top_project_width-2*diam)/2,horizon_height_1)]
        horizon_seg_2 = [(0,-(top_project_width-2*diam)/2,horizon_height_2),(0,(top_project_width-2*diam)/2,horizon_height_2)]
        hoist_loc = [[left_edge,self.double_wall_geo.total_wall_thick/2,self.double_wall_geo.inner_side_wall_height+50],
                     [self.double_wall_geo.inner_side_wall_width-right_edge,self.double_wall_geo.total_wall_thick/2,self.double_wall_geo.inner_side_wall_height+50]]

        total_profile = [left_seg,left_arc,left_arc_line,middle_arc,right_arc_line,right_arc,right_seg]
        hoist_embedded_info["name"] = name
        hoist_embedded_info["number"] = number
        hoist_embedded_info["notes"] = notes
        hoist_embedded_info["number_list"] = number_list
        hoist_embedded_info["left_seg"] = left_seg
        hoist_embedded_info["middle_seg"] = middle_seg
        hoist_embedded_info["right_seg"] = right_seg
        hoist_embedded_info["exterior_seg"] = exterior_seg
        hoist_embedded_info["horizon_seg_1"] = horizon_seg_1
        hoist_embedded_info["horizon_seg_2"] = horizon_seg_2
        hoist_embedded_info["hoist_loc"] = hoist_loc
        hoist_embedded_info["diam"] = diam
        hoist_embedded_info["left_edge"] = left_edge
        hoist_embedded_info["right_edge"] = right_edge
        hoist_embedded_info["left_project_length"] = left_project_length
        hoist_embedded_info["bottom_line_length"] = left_line_length
        hoist_embedded_info["top_project_width"] = top_project_width
        hoist_embedded_info["horizon_height_1"] = horizon_height_1
        hoist_embedded_info["horizon_height_2"] = horizon_height_2
        hoist_embedded_info["total_profile"] = total_profile
        return hoist_embedded_info








