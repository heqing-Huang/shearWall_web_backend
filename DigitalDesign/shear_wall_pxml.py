from DigitalDesign.ifc_core import IfcDocument
from DigitalDesign.get_data import ShearWallData
from DoubleWallDesign.models import RebarforBIM


def shear_wall_pxml_creation(ifc_doc: IfcDocument, rebar_data: RebarforBIM, shear_wall_data: ShearWallData):
    detailed_design = shear_wall_data.detailed_design_result.detailed_design
    detailed_design_result = shear_wall_data.detailed_design_result
