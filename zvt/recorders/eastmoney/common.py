# -*- coding: utf-8 -*-
import logging

import requests

from zvt.contract.api import get_data_count, get_data
from zvt.contract.recorder import TimestampsDataRecorder, TimeSeriesDataRecorder
from zvt.utils.time_utils import to_pd_timestamp
from zvt.domain import CompanyType, Stock, StockDetail

logger = logging.getLogger(__name__)


class ApiWrapper(object):
    def request(self, url=None, method='post', param=None, path_fields=None):
        raise NotImplementedError


def get_fc(security_item):
    if security_item.exchange == 'sh':
        fc = "{}01".format(security_item.code)
    if security_item.exchange == 'sz':
        fc = "{}02".format(security_item.code)

    return fc


def get_company_type(stock_domain: StockDetail):
    industries = stock_domain.industries.split(',')
    if ('银行' in industries) or ('信托' in industries):
        return CompanyType.yinhang
    if '保险' in industries:
        return CompanyType.baoxian
    if '证券' in industries:
        return CompanyType.quanshang
    return CompanyType.qiye


def company_type_flag(security_item):
    try:
        company_type = get_company_type(security_item)

        if company_type == CompanyType.qiye:
            return "4"
        if company_type == CompanyType.quanshang:
            return "1"
        if company_type == CompanyType.baoxian:
            return "2"
        if company_type == CompanyType.yinhang:
            return "3"
    except Exception as e:
        logger.warning(e)

    param = {
        "color": "w",
        "fc": get_fc(security_item)
    }

    resp = requests.post('https://emh5.eastmoney.com/api/CaiWuFenXi/GetCompanyType', json=param)

    ct = resp.json().get('Result').get('CompanyType')

    logger.warning("{} not catching company type:{}".format(security_item, ct))

    return ct


def call_eastmoney_api(url=None, method='post', param=None, path_fields=None):
    if method == 'post':
        resp = requests.post(url, json=param)

    resp.encoding = 'utf8'

    try:
        origin_result = resp.json().get('Result')
    except Exception as e:
        logger.exception('code:{},content:{}'.format(resp.status_code, resp.text))
        raise e

    if path_fields:
        the_data = get_from_path_fields(origin_result, path_fields)
        if not the_data:
            logger.warning(
                "url:{},param:{},origin_result:{},could not get data for nested_fields:{}".format(url, param,
                                                                                                  origin_result,
                                                                                                  path_fields))
        return the_data

    return origin_result


def get_from_path_fields(the_json, path_fields):
    the_data = the_json.get(path_fields[0])
    if the_data:
        for field in path_fields[1:]:
            the_data = the_data.get(field)
            if not the_data:
                return None
    return the_data


class EastmoneyApiWrapper(ApiWrapper):
    def request(self, url=None, method='post', param=None, path_fields=None):
        return call_eastmoney_api(url=url, method=method, param=param, path_fields=path_fields)


class BaseEastmoneyRecorder(object):
    request_method = 'post'
    path_fields = None
    api_wrapper = EastmoneyApiWrapper()

    def generate_request_param(self, security_item, start, end, size, timestamp):
        raise NotImplementedError

    def record(self, entity_item, start, end, size, timestamps):
        if timestamps:
            original_list = []
            for the_timestamp in timestamps:
                param = self.generate_request_param(entity_item, start, end, size, the_timestamp)
                tmp_list = self.api_wrapper.request(url=self.url, param=param, method=self.request_method,
                                                    path_fields=self.path_fields)
                self.logger.info(
                    "record {} for entity_id:{},timestamp:{}".format(
                        self.data_schema, entity_item.id, the_timestamp))
                # fill timestamp field
                for tmp in tmp_list:
                    tmp[self.get_evaluated_time_field()] = the_timestamp
                original_list += tmp_list
                if len(original_list) == self.batch_size:
                    break
            return original_list

        else:
            param = self.generate_request_param(entity_item, start, end, size, None)
            return self.api_wrapper.request(url=self.url, param=param, method=self.request_method,
                                            path_fields=self.path_fields)


class EastmoneyTimestampsDataRecorder(BaseEastmoneyRecorder, TimestampsDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail

    provider = 'eastmoney'

    timestamps_fetching_url = None
    timestamp_list_path_fields = None
    timestamp_path_fields = None

    def init_timestamps(self, entity):
        param = {
            "color": "w",
            "fc": get_fc(entity)
        }

        timestamp_json_list = call_eastmoney_api(url=self.timestamps_fetching_url,
                                                 path_fields=self.timestamp_list_path_fields,
                                                 param=param)

        if self.timestamp_path_fields and timestamp_json_list:
            timestamps = [get_from_path_fields(data, self.timestamp_path_fields) for data in timestamp_json_list]
            return [to_pd_timestamp(t) for t in timestamps]
        return []


class EastmoneyPageabeDataRecorder(BaseEastmoneyRecorder, TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail

    provider = 'eastmoney'

    page_url = None

    def get_remote_count(self, security_item):
        param = {
            "color": "w",
            "fc": get_fc(security_item),
            "pageNum": 1,
            "pageSize": 1
        }
        return call_eastmoney_api(self.page_url, param=param, path_fields=['TotalCount'])

    def evaluate_start_end_size_timestamps(self, entity):
        remote_count = self.get_remote_count(entity)

        if remote_count == 0:
            return None, None, 0, None

        # get local count
        local_count = get_data_count(data_schema=self.data_schema, session=self.session,
                                     filters=[self.data_schema.entity_id == entity.id])
        # FIXME:the > case
        if local_count >= remote_count:
            return None, None, 0, None

        return None, None, remote_count - local_count, None

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return {
            "color": "w",
            "fc": get_fc(security_item),
            'pageNum': 1,
            # just get more for some fixed data
            'pageSize': size + 10
        }


class EastmoneyMoreDataRecorder(BaseEastmoneyRecorder, TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail

    provider = 'eastmoney'

    def get_remote_latest_record(self, security_item):
        param = {
            "color": "w",
            "fc": get_fc(security_item),
            "pageNum": 1,
            "pageSize": 1
        }
        results = call_eastmoney_api(self.url, param=param, path_fields=self.path_fields)
        _, result = self.generate_domain(security_item, results[0])
        return result

    def evaluate_start_end_size_timestamps(self, entity):
        # get latest record
        latest_record = get_data(entity_id=entity.id,
                                 provider=self.provider,
                                 data_schema=self.data_schema,
                                 order=self.data_schema.timestamp.desc(), limit=1,
                                 return_type='domain',
                                 session=self.session)
        if latest_record:
            remote_record = self.get_remote_latest_record(entity)
            if not remote_record or (
                    latest_record[0].id == remote_record.id):
                return None, None, 0, None
            else:
                return None, None, 10, None

        return None, None, 1000, None

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return {
            "color": "w",
            "fc": get_fc(security_item),
            'pageNum': 1,
            'pageSize': size
        }
