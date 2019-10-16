import json

from sqlalchemy.sql.elements import BinaryExpression

from zvt.sedes import CustomJsonEncoder, CustomJsonDecoder
from zvt.domain import Stock1dKdata


def test_json_codec():
    filter_str = json.dumps([Stock1dKdata.timestamp == '2017-01-01', Stock1dKdata.name == 'abcd'],
                            cls=CustomJsonEncoder)
    assert isinstance(filter_str, str)

    filter = json.loads(filter_str, cls=CustomJsonDecoder)

    assert isinstance(filter[0], BinaryExpression)
