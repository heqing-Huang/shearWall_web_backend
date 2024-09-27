import os
import logging
import warnings
from dataclasses import asdict
from typing import IO, Optional, Tuple
from traceback import format_exc

from DoubleWallDesign.models import RebarforBIM
from RebarLayout.Rebar_layout import rebar_layout

from DoubleWallDesign.detailed_design import detailed_design, to_word_detailed
from DoubleWallDesign.models import (
    DetailedDesignResult,
    DetailedDesign,
)

from DoubleWallDesign.tools import DetailedCalculationBook

# from stair_for_bvbs.data_for_bvbs import data_for_bvbs

from DigitalDesign.create_bvbs import create_bvbs

# from stair_rebar_bvbs.create_JSON import create_json, make_zip_content_export

from DigitalDesign.shear_wall_ifc import shear_wall_IFC_creation

# from stair_dxf.stair_generate_dxf import stair_generate_dxf

from . import exchange
from .exchange import detailed

from . import models
from .exchange.detailed import detail_result_2_model_result
# from . import layers

from .models import (
    WallDetailedData,
    WallDetailedResult,
)

# from .exchange.detailed import (
#     ConstructionResultSerializer,
#     SerializerFromModelDetailedResultToCalculationBookDetailed,
#     detail_result_2_model_result,
#     MDResultToDCResult,
# )

from DoubleWallDesign.detailed_design import detailed_design


Detailed = DetailedDesign
DetailedResult = DetailedDesignResult

def call_detailed_design(detailed_row: WallDetailedData) -> Optional[DetailedDesignResult]:
    """
    双皮剪力墙深化设计调用函数
    """
    detailed_serializer = detailed.DetailedDataSerializer(instance=detailed_row)

    detailed_parameter = Detailed(
        **dict(detailed_serializer.data)
    )

    result = detailed_design(detailed_parameter)[0]

    return result

def call_detailed_design_by_model(
    detail_row: WallDetailedData,
) -> Optional[WallDetailedResult]:
    """
    传入表模型,返回表模型,封装深化设计调用过程
    """
    detailed_design_result: DetailedDesignResult = call_detailed_design(detail_row)
    result: WallDetailedResult = detail_result_2_model_result(
        detailed_design_result, detail_row
    )
    return result