import datetime
import logging
import sys
import time
from margin.base import MarginBase
from margin.configs import LOCAL, FIRST

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SzGener(MarginBase):
    def __init__(self):
        self.juyuan_table_name = 'MT_TargetSecurities'
        self.target_table_name = 'stk_mttargetsecurities'
        # 爬虫库
        self.inner_code_map = self.get_inner_code_map()
        self.sz_history_table_name = 'sz_margin_history' 

        # 深交所的公告页
        self.announcemen_web = 'http://www.szse.cn/disclosure/margin/business/index.html'
        # 深交所的公告接口  TODO
        self.announcemen_web_api = 'http://www.szse.cn/api/search/content?random=0.5530111979175076'
        '''
        post 请求 
        接口数据： 
        keyword: 融资融券
        time: 0
        range: title
        channelCode[]: business_news
        currentPage: 1
        pageSize: 20
        '''

    def load_juyuan(self):
        """将聚源已有的数据导入"""
        select_fields = ['SecuMarket', 'InnerCode', 'InDate', 'OutDate', 'TargetCategory', 'TargetFlag', 'ChangeReasonDesc',
                         'UpdateTime',
                         # 'JSID',
                         ]
        select_str = ",".join(select_fields).rstrip(",")
        juyuan = self._init_pool(self.juyuan_cfg)
        sql = '''select {} from {};'''.format(select_str, self.juyuan_table_name)
        ret = juyuan.select_all(sql)
        juyuan.dispose()

        update_fields = ['SecuMarket', 'InnerCode', 'InDate', 'OutDate', 'TargetCategory', 'TargetFlag', 'ChangeReasonDesc', 'UpdateTime']
        target = self._init_pool(self.product_cfg)
        for item in ret:
            self._save(target, item, self.target_table_name, update_fields)

        try:
            target.dispose()
        except Exception as e:
            logger.warning(f"dispose error: {e}")

    def _create_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS `{}` (
          `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'ID',
          `SecuMarket` int(11) DEFAULT NULL COMMENT '证券市场',
          `InnerCode` int(11) NOT NULL COMMENT '证券内部编码',
          `InDate` datetime NOT NULL COMMENT '调入日期',
          `OutDate` datetime DEFAULT NULL COMMENT '调出日期',
          `TargetCategory` int(11) NOT NULL COMMENT '标的类别',
          `TargetFlag` int(11) DEFAULT NULL COMMENT '标的状态',
          `ChangeReasonDesc` varchar(2000) DEFAULT NULL COMMENT '变更原因描述',
          `UpdateTime` datetime NOT NULL COMMENT '数据源更新时间',
          `CREATETIMEJZ` datetime DEFAULT CURRENT_TIMESTAMP,
          `UPDATETIMEJZ` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `IX_MT_TargetSecurities` (`SecuMarket`, `InnerCode`,`TargetCategory`,`InDate`,`TargetFlag`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='融资融券标的证券变更记录';
        '''.format(self.target_table_name)
        target = self._init_pool(self.product_cfg)
        target.insert(sql)
        target.dispose()
        logger.info("尝试建表")

    def parse_announcemen_byhuman(self):
        """从公告中提取更改信息 """
        base_sql = '''update {} set OutDate = '{}', TargetFlag = 2 where SecuMarket = 90 and InnerCode = {}\
        and TargetCategory in (10, 20) and TargetFlag = 1; '''

        target = self._init_pool(self.product_cfg)

        # # (1) http://www.szse.cn/disclosure/notice/general/t20200415_575996.html
        # # 本所于2020年4月16日起将 南京华东电子信息科技股份有限公司股票（证券代码：000727）  调出融资融券标的证券名单
        # inner_code = self.get_inner_code('000727')
        # print(inner_code)    # 401

        # (2） http://www.szse.cn/disclosure/notice/general/t20200428_576534.html
        # 本所于2020年4月29日起将 华映科技（集团）股份有限公司股票（证券代码：000536）  调出融资融券标的证券名单
        inner_code = self.get_inner_code("000536")   # 220
        dt = datetime.datetime(2020, 4, 29)
        sql = '''update {} set OutDate = '{}', TargetFlag = 2 where SecuMarket = 90 and InnerCode = {}\
 and TargetCategory in (10, 20) and TargetFlag = 1; '''.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)

        # (3) http://www.szse.cn/disclosure/notice/general/t20200429_576571.html
        # 本所于2020年4月30日起将 苏州胜利精密制造科技股份有限公司股票（证券代码：002426） 调出融资融券标的证券名单。
        inner_code = self.get_inner_code('002426')
        # print(inner_code)   # 10476
        dt = datetime.datetime(2020, 4, 30)
        sql = '''update {} set OutDate = '{}', TargetFlag = 2 where SecuMarket = 90 and InnerCode = {}\
        and TargetCategory in (10, 20) and TargetFlag = 1; '''.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)
        print(ret)

        # (4) http://www.szse.cn/disclosure/notice/general/t20200429_576572.html
        # 本所于2020年4月30日起将  江西特种电机股份有限公司股票（证券代码：002176） 调出融资融券标的证券名单
        dt = datetime.datetime(2020, 4, 30)
        inner_code = self.get_inner_code('002176')
        # print(inner_code)   # 6139
        sql = '''update {} set OutDate = '{}', TargetFlag = 2 where SecuMarket = 90 and InnerCode = {}\
        and TargetCategory in (10, 20) and TargetFlag = 1; '''.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)
        print(ret)

        # # (5) http://www.szse.cn/disclosure/notice/general/t20200430_576649.html
        # # 本所于2020年5月6日起将  深圳市奋达科技股份有限公司股票（证券代码：002681）  调出融资融券标的证券名单。
        dt = datetime.datetime(2020, 5, 6)
        inner_code = self.get_inner_code('002681')
        # print(inner_code)   # 16668
        sql = '''update {} set OutDate = '{}', TargetFlag = 2 where SecuMarket = 90 and InnerCode = {}\
        and TargetCategory in (10, 20) and TargetFlag = 1; '''.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)
        print(ret)

        # # (6) http://www.szse.cn/disclosure/notice/general/t20200430_576648.html
        # # 本所于2020年5月6日起将 大连晨鑫网络科技股份有限公司股票（证券代码：002447） 调出融资融券标的证券名单
        dt = datetime.datetime(2020, 5, 6)
        inner_code = self.get_inner_code("002447")
        # print(inner_code)   # 10493
        sql = base_sql.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)
        print(ret)

        # (7) http://www.szse.cn/disclosure/notice/general/t20200430_576646.html
        # 本所于2020年5月6日起将 藏格控股股份有限公司股票（证券代码：000408） 调出融资融券标的证券名单。
        dt = datetime.datetime(2020, 5, 6)
        inner_code = self.get_inner_code("000408")
        # print(inner_code)   # 155
        sql = base_sql.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)
        print(ret)

        # (8) http://www.szse.cn/disclosure/notice/general/t20200430_576647.html
        # 本所于2020年5月6日起将该 深圳市同洲电子股份有限公司股票（证券代码：002052） 调出融资融券标的证券名单。
        dt = datetime.datetime(2020, 5, 6)
        inner_code = self.get_inner_code("002052")
        # print(inner_code)  # 4347
        sql = base_sql.format(self.target_table_name, dt, inner_code)
        ret = target.update(sql)
        print(ret)

        target.dispose()
        
    def dt_datas(self, dt1):
        """获取爬虫库中某一天的历史数据"""
        spider = self._init_pool(self.spider_cfg)
        sql_dt = '''select max(ListDate) as mx from {} where ListDate <= '{}'; '''.format(self.sz_history_table_name, dt1)
        dt1_ = spider.select_one(sql_dt).get("mx")
        sql = '''select InnerCode from {} where ListDate = '{}' and  FinanceBool = 1; '''.format(self.sz_history_table_name, dt1_)  # TODO and FinanceBuyToday = 1
        ret1 = spider.select_all(sql)
        ret1 = sorted(set([r.get("InnerCode") for r in ret1]))
        return ret1
        
    def history_diff(self, dt1, dt2):
        """
        将历史数据中某两天的数据进行 diff
        dt1 是变更发生的时间 
        dt2 是变更发生的前一天 
        """
        
        data1 = self.dt_datas(dt1)
        data1 = set(sorted(data1))

        data2 = self.dt_datas(dt2)
        data2 = set(sorted(data2))
        
        to_add_set = data1 - data2 
        to_delete_set = data2 - data1 
        
        logger.info("要增加的标的: {}".format(to_add_set))
        logger.info("要剔除的标的: {}".format(to_delete_set))
        
        return to_add_set, to_delete_set
    
    def gene_records(self, dt1, dt2):
        """
        生成数据库的一条变更记录
        dt1 是较大的时间点
        dt2 是较小的时间点 是 dt1 的前一天
        """
        #  id | SecuMarket | InnerCode | InDate              | OutDate | TargetCategory | TargetFlag | ChangeReasonDesc | UpdateTime          | CREATETIMEJZ        | UPDATETIMEJZ
        fields = ["SecuMarket", "InnerCode", "InDate", "OutDate", "TargetCategory", "TargetFlag", "ChangeReasonDesc"]

        item = {"SecuMarket": 90,
                # "InnerCode": '',
                # "InDate": '',
                # 'OutDate': '',
                # 'TargetCategory': '',   # 10 和 20
                # 'TargetFlag': '',
                'ChangeReasonDesc': '',
                'UpdateTime': datetime.datetime.now(),
                }

        target = self._init_pool(self.product_cfg)

        to_add_set, to_delete_set = self.history_diff(dt1, dt2)
        logger.info("{} 和 {} 的 diff 结果: add: {} , delete: {}".format(dt1, dt2, to_add_set, to_delete_set))
        local_str = "本地" if LOCAL else "远程"
        msg = "{}: 融资融券标的变更记录生成: {} 和 {} 的 diff 结果: add: {} , delete: {}".format(local_str, dt1, dt2, to_add_set, to_delete_set)
        self.ding(msg)
        if to_add_set:
            for inner_code in to_add_set:
                # 在 dt1 增加 2 条 in 的记录
                item1 = {
                    "SecuMarket": 90,
                    "InnerCode": inner_code,
                    "InDate": dt1,
                    'TargetCategory': 10,
                    'TargetFlag': 1,
                    'ChangeReasonDesc': '',
                    'UpdateTime': datetime.datetime.now(),
                }

                item2 = {
                    "SecuMarket": 90,
                    "InnerCode": inner_code,
                    "InDate": dt1,
                    'TargetCategory': 20,
                    'TargetFlag': 1,
                    'ChangeReasonDesc': '',
                    'UpdateTime': datetime.datetime.now(),
                }

                self._save(target, item1, self.target_table_name, fields)
                self._save(target, item2, self.target_table_name, fields)

        base_sql = '''update {} set OutDate = '{}', TargetFlag = 2 where SecuMarket = 90 and InnerCode = {}\
        and TargetCategory in (10, 20) and TargetFlag = 1; '''

        if to_delete_set:
            for inner_code in to_delete_set:
                # 在 dt1 update 进 2 条 out 的记录
                sql = base_sql.format(self.target_table_name, dt1, inner_code)
                ret = target.update(sql)
                logger.info("更新的记录条数是 {}".format(ret))

        try:
            target.dispose()
        except:
            logger.warning("dispose error")
            raise

    def start(self):
        # 建表[远程没有建表的权限]
        if LOCAL:
            self._create_table()

        # 将聚源数据库的数据导出
        if FIRST:
            self.load_juyuan()
            logger.info("已经导出聚源数据库") 
            self.parse_announcemen_byhuman()

        _today = datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)
        _yester_day = _today - datetime.timedelta(days=1)
        _before_yester_day = _today - datetime.timedelta(days=2)

        # print(_yester_day)
        # print(_before_yester_day)

        self.gene_records(_yester_day, _before_yester_day)


if __name__ == "__main__":
    now = lambda: time.time()
    start_time = now()
    SzGener().start()
    logger.info(f"用时: {now() - start_time} 秒")    # (end)大概是 80s (dispose)大概是 425s
