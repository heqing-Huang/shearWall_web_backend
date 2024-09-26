from DoubleWallDesign.models import DetailedDesignResult, DetailedDesign

from converter_dataclass import dataclass_with_converter as dataclass
from converter_dataclass import field_with_converter as field


@dataclass
class DetailedCalculationBook:
    """
        约定双皮剪力墙计算书能够拥有的参数
    """
    detailed_design_result: DetailedDesignResult

    detailed_design: DetailedDesign

    def __post_init__(self):
        if isinstance(self.detailed_design_result, dict):
            self.detailed_design_result = DetailedDesignResult(
                **self.detailed_design_result
            )
        if isinstance(self.detailed_design, dict):
            self.detailed_design = DetailedDesign(**self.detailed_design)

