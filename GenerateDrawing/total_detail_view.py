"""
开始绘制视图
"""

from GenerateDrawing.model_data import DoubleShearWallViewData
from GenerateDrawing.special_function import adjust_drawing_scale
from GenerateDrawing.single_detail_view import DoubleWallFormFrontView,DoubleWallFormRightView,DoubleWallFormTopView,\
        DoubleWallFormThreeDView,DoubleWallReinforcementDView,ReinforcementOneToOneSectionView,\
    ReinforcementTwoToTwoSectionView,TrussRebarDetailView,TrussRebarDetailRebarView,HoistEmbeddedPartDetailView,\
    TotalDesignInfoTable


class DoubleShearWallTotalView(object):
    """
    双皮剪力墙视图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.scale = 1/100  # 缩放比例
        self.create_total_dxf_view()  # 创建所有dxf视图

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.model_space = self.dxf_doc.modelspace()  # 创建模型空间

    def create_total_dxf_view(self):
        """
        创建所有dxf视图
        :return:
        """
        self.form_front_view = DoubleWallFormFrontView(self.dxf_doc,self.model_transform_data)
        self.form_right_view = DoubleWallFormRightView(self.dxf_doc,self.model_transform_data)
        self.form_top_view = DoubleWallFormTopView(self.dxf_doc,self.model_transform_data)
        self.form_three_dim_view = DoubleWallFormThreeDView(self.dxf_doc,self.model_transform_data)
        self.rebar_reinforcement_view = DoubleWallReinforcementDView(self.dxf_doc,self.model_transform_data)
        self.reinforcement_one_section_view = ReinforcementOneToOneSectionView(self.dxf_doc,self.model_transform_data)
        self.reinforcement_two_section_view = ReinforcementTwoToTwoSectionView(self.dxf_doc,self.model_transform_data)
        self.truss_rebar_detail_view = TrussRebarDetailView(self.dxf_doc,self.model_transform_data)
        self.truss_rebar_detail_rebar_view = TrussRebarDetailRebarView(self.dxf_doc,self.model_transform_data)
        self.hoist_embedded_part_view = HoistEmbeddedPartDetailView(self.dxf_doc,self.model_transform_data)
        self.total_design_info_table = TotalDesignInfoTable(self.dxf_doc,self.model_transform_data)

    def place_form_front_view_block_position(self):
        """
        放置模板主视图块位置
        :return:
        """
        block_loc = (0,2000,0)
        # 添加图块
        self.model_space.add_blockref("form_front_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_front_view_top_rebar_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_front_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_front_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_form_right_view_block_position(self):
        """
        放置模板右视图块位置
        :return:
        """
        block_loc = (2500,2000,0)
        # 添加图块
        self.model_space.add_blockref("form_right_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_right_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_right_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_form_top_view_block_position(self):
        """
        放置模板俯视图块位置
        :return:
        """
        block_loc = (0,1000,0)
        # 添加图块
        self.model_space.add_blockref("form_top_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_top_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_top_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_form_three_dim_view_block_position(self):
        """
        放置3D视图块位置
        :return:
        """
        block_loc = (3000,3000,0)
        # 添加图块
        self.model_space.add_blockref("form_three_dim_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("form_three_dim_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_rebar_reinforcement_view_block_position(self):
        """
        放置配筋图块位置
        :return:
        """
        block_loc = (4000,2000,0)
        # 添加图块
        self.model_space.add_blockref("rebar_reinforcement_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("rebar_reinforcement_view_top_rebar_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("rebar_reinforcement_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("rebar_reinforcement_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

        self.model_space.add_blockref("rebar_reinforcement_view_cut_line_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("rebar_reinforcement_view_outline_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_rebar_reinforcement_one_section_view_block_position(self):
        """
        放置1-1剖切图块位置
        :return:
        """
        block_loc = (4000,1000,0)
        # 添加图块
        self.model_space.add_blockref("reinforce_section_one_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_one_view_rebar_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_one_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_one_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_one_view_outline_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_rebar_reinforcement_two_section_view_block_position(self):
        """
        放置2-2剖切图块位置
        :return:
        """
        block_loc = (6500,2000,0)
        # 添加图块
        self.model_space.add_blockref("reinforce_section_two_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_two_view_rebar_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_two_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_two_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("reinforce_section_two_view_outline_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_truss_rebar_detail_view_block_position(self):
        """
        桁架钢筋细部图图块位置
        :return:
        """
        block_loc = (9000,4200,0)
        # 添加图块
        self.model_space.add_blockref("truss_rebar_detail_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_view_rebar_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_view_outline_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_truss_rebar_detail_rebar_view_block_position(self):
        """
        桁架钢筋细部钢筋图图块位置
        :return:
        """
        block_loc = (10000,4200,0)
        # 添加图块
        self.model_space.add_blockref("truss_rebar_detail_rebar_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_rebar_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_rebar_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("truss_rebar_detail_rebar_view_outline_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_hoist_embedded_part_view_block_position(self):
        """
        桁架吊装预埋件视图图块位置
        :return:
        """
        block_loc = (11000,4200,0)
        # 添加图块
        self.model_space.add_blockref("hoist_embedded_part_view_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("hoist_embedded_part_view_dimension_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("hoist_embedded_part_view_text_block", block_loc,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def place_total_table_view_block_position(self):
        """
        所有表格位置块放置
        :return:
        """
        block_loc_1 = (9000,1000,0)
        block_loc_2 = (9000,2200,0)
        block_loc_3 = (9000,2700,0)
        # 添加图块
        self.model_space.add_blockref("rebar_material_view_block", block_loc_1,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("rebar_material_table_text_block", block_loc_1,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        # 添加预制构件材料表
        self.model_space.add_blockref("component_material_view_block", block_loc_2,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("component_material_table_text_block", block_loc_2,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

        # 添加埋件材料表
        self.model_space.add_blockref("embedded_material_view_block", block_loc_3,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度
        self.model_space.add_blockref("embedded_material_table_text_block", block_loc_3,
                                      dxfattribs={  # 插入块，插入块参考点---块中所有实体都发生局部坐标到全局坐标的转变，块属性
                                          'xscale': 1,  # 缩放比例
                                          'yscale': 1,  # 缩放比例
                                          'rotation': 0})  # 逆时针旋转0度

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        # 创建模板主视图
        self.form_front_view.main_run_process()  # 绘制图形
        self.place_form_front_view_block_position()  # 在模型空间放置块
        self.form_right_view.main_run_process()  # 绘制右视图图形
        self.place_form_right_view_block_position()  # 在模型空间放置块
        self.form_top_view.main_run_process()
        self.place_form_top_view_block_position()
        # self.form_three_dim_view.main_run_process()
        # self.place_form_three_dim_view_block_position()
        self.rebar_reinforcement_view.main_run_process()
        self.place_rebar_reinforcement_view_block_position()
        self.reinforcement_one_section_view.main_run_process()
        self.place_rebar_reinforcement_one_section_view_block_position()
        self.reinforcement_two_section_view.main_run_process()
        self.place_rebar_reinforcement_two_section_view_block_position()
        self.truss_rebar_detail_view.main_run_process()
        self.place_truss_rebar_detail_view_block_position()
        self.truss_rebar_detail_rebar_view.main_run_process()
        self.place_truss_rebar_detail_rebar_view_block_position()
        self.hoist_embedded_part_view.main_run_process()
        self.place_hoist_embedded_part_view_block_position()
        self.total_design_info_table.main_run_process()
        self.place_total_table_view_block_position()
        self.dxf_doc.saveas("tmp/double_shear_wall_detail_view.dxf")


