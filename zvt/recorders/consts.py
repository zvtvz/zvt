# -*- coding: utf-8 -*-
from zvt.utils.utils import chrome_copy_header_to_dict

SSE_KDATA_HEADER = chrome_copy_header_to_dict('''
Host: yunhq.sse.com.cn:32041
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36
Accept: */*
Referer: http://www.sse.com.cn/market/price/trends/
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.8,en;q=0.6
Cookie: yfx_c_g_u_id_10000042=_ck17072000172016360411059933357; yfx_f_l_v_t_10000042=f_t_1500481040618__r_t_1507560823182__v_t_1507561607501__r_c_1; VISITED_MENU=%5B%228451%22%2C%228453%22%5D
'''
                                              )

DEFAULT_SH_HEADER = chrome_copy_header_to_dict('''
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8,en;q=0.6
Connection:keep-alive
Cookie:PHPStat_First_Time_10000011=1464572600205; PHPStat_Cookie_Global_User_Id=_ck16053009432012139947369251193; PHPStat_Main_Website_10000011=_ck16053009432012139947369251193%7C10000011%7C%7C%7C; VISITED_STOCK_CODE=%5B%22600272%22%5D; VISITED_COMPANY_CODE=%5B%22600272%22%5D; seecookie=%5B600272%5D%3A%u5F00%u5F00%u5B9E%u4E1A; PHPStat_Return_Count_10000011=3; PHPStat_Return_Time_10000011=1476152548261; _trs_uv=1j7y_532_itpgj4e2; VISITED_MENU=%5B%228482%22%2C%228530%22%2C%228529%22%2C%228453%22%2C%228454%22%2C%228464%22%2C%228466%22%2C%228469%22%2C%228451%22%2C%228528%22%5D
Host:query.sse.com.cn
Referer:http://www.sse.com.cn/assortment/stock/list/share/
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36
''')

DEFAULT_SZ_HEADER = chrome_copy_header_to_dict('''
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8,en;q=0.6
Connection:keep-alive
Host:www.szse.cn
Referer:http://www.szse.cn/main/marketdata/jypz/colist/
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36
''')

DEFAULT_TICK_HEADER = chrome_copy_header_to_dict('''
Host: market.finance.sina.com.cn
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding: gzip, deflate, sdch
Accept-Language: zh-CN,zh;q=0.8,en;q=0.6
Cookie: U_TRS1=000000b3.fffc2f53.566f784b.2900c0a6; UOR=www.baidu.com,blog.sina.com.cn,; SINAGLOBAL=182.139.185.185_1450145868.176138; vjuids=-fde6fe2f2.151a36dec26.0.113c0d8; SGUID=1450145869010_36029656; Apache=182.139.185.132_1457087046.693218; ULV=1457087047846:3:2:2:182.139.185.132_1457087046.693218:1457087047557; U_TRS2=0000009f.95a9161b.57038c9e.11b3a69f; SessionID=e2ajs2t3k4emag633adfjho861; SINA_FINANCE_SELECT_TYPE=stock; SCF=AhFAeZgjMw_ozKbe2MXZtX2fG8ZrLemvX24bd57wciL98hfpOY_4hN8aYqvvaxZDbINdQq3XqZSrS-ubJo-5VUI.; sso_info=v02m6alo5qztbaYloWum6akpp2WpaSPk4S1jpOYsYyjlLONg5DA; SUP=cv%3D1%26bt%3D1470117772%26et%3D1470204172%26d%3D40c3%26i%3De2a8%26us%3D0%26vf%3D0%26vt%3D0%26ac%3D2%26st%3D0%26lt%3D7%26uid%3D1596125344%26user%3Djackofxuan%2540gmail.com%26ag%3D4%26name%3Djackofxuan%2540gmail.com%26nick%3Dvaanni%26sex%3D%26ps%3D0%26email%3D%26dob%3D%26ln%3D%26os%3D%26fmp%3D%26lcp%3D2011-12-26%252017%253A00%253A23; __utma=269849203.900451459.1468839849.1468839849.1471431141.2; __utmc=269849203; __utmz=269849203.1471431141.2.2.utmcsr=finance.sina.com.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; SINABLOGNUINFO=1596125344.5f22f0a0.vannii; SINA_FINANCE=%3A1596125344%3A4; hk_visited_stocks=02338; WEB2_APACHE2_GD=1401fbd37fe42dfbc571af9dacb5e317; _s_upa=25; lxlrtst=1475225080_o; SR_SEL=1_511; SINA_PORTFOLIO=sh601600%2Csh600089%2Csz000528%2Csh600150%2Csz000338%2Csh600031%2Csh600199%2Csh000001%2Csz399001%2Csz000778%2Csh600315%2Csh600570%2Csh601608%2Csz000099%2Csh600439%2Csz000521%2Csz300276%2Csz000783%2Csh600396%2Csz300336%2Csz000751%2Csz000848%2Csh600711%2Csh600880%2Csh600362%2Csh600060%2Csz000680%2Csz002051; ArtiFSize=14; visited_uss=gb_goog%7Cgb_sina%7Cgb_.dji; FINA_DMHQ=0; hqEtagMode=1; VISITED_FUTURE=hf_CL_0%2Chf_GC_0%2Chf_SI_0%2Chf_CAD_0%2CCF1609_1%2CRB0_1%2Chf_DJS_0%2CCFF_RE_IF1606_2%2CCFF_RE_IF1510_2%2CCFF_RE_IC1606_2%2CRM0_1%2CRB1610_1; lxlrttp=1476092678; FINA_V5_HQ=0; SUB=_2A251BPWoDeTxGedL4lQQ8ivPzziIHXVWcGBgrDV_PUNbm9BeLXLzkW8iLp81bNoV5si_9RFc9X4XY1wBcg..; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5J7vXaOMNYJQ0d27EZPWIF5NHD95QpSK.ceKzfe0BXWs4Dqcj.i--fi-zRiKnEi--fiKLhi-iWi--Xi-isi-88i--Ri-2piKyh; ALF=1507965304; FIN_ALL_VISITED=sz000338%2Csh000001%2Csz000680%2Csz399006%2Csh600028%2Csh600315%2Csh600031%2Csh601608%2Csh601038%2Csh601628%2CCL%2Csh600150%2Csz300369%2Csz300079%2CAGTD%2Csz300336%2Csz300276%2Cgoog%2Csina%2CGC%2CSI%2Csh600004%2Csh600000%2Csz300374%2Csh600199%2Csh600439%2Csz000783%2Csz000912%2CCAD%2Csz002628%2Csh600362%2Csz002051%2Csz000930%2Csz000528%2Csh603568%2Csh600060%2Csh600635%2Csz150266%2Csz000651%2Csz000099%2Csh600570%2Csz000002%2Csh600048%2Csz000839%2Csz002223%2Csh600880%2Csz000521%2Csz000878%2Csz399001%2Csh600396%2Csz000751%2Csh600016%2Csz000915%2Csh600779%2Csh600497%2Csh601600%2Csh600111%2Csh600550%2Csz000426%2Csz002237; FINA_LV2_S_2=1596125344; FINA_LV2_S_2_B=0; rotatecount=1; vjlast=1476433318; FINA_V_S_2=sz000338,sh000001,sz000680,sz399006,sh600028,sh600315,sh600031,sh601608,sh601038,sh601628,sh600150,sz300369,sz300079,sz300336,sz300276,sh600004,sh600000,sz300374,sh600199,sh600439
Referer:market.finance.sina.com.cn
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36
''')

DEFAULT_KDATA_HEADER = chrome_copy_header_to_dict('''
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8,en;q=0.6
Cache-Control:max-age=0
Connection:keep-alive
Host:vip.stock.finance.sina.com.cn
Referer:vip.stock.finance.sina.com.cn
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36
''')

TONGHUASHUN_GN_HEADER = chrome_copy_header_to_dict('''
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8,en;q=0.6
Cache-Control:max-age=0
Connection:keep-alive
Cookie:Hm_lvt_ab89213e83c551bf095446c08bf64988=1477116434; Hm_lpvt_ab89213e83c551bf095446c08bf64988=1477116434; historystock=600126; spversion=20130314; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1477105757,1477116434; Hm_lpvt_78c58f01938e4d85eaf619eae71b4ed1=1477362626
Host:q.10jqka.com.cn
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36
''')

TONGHUASHUN_KDATA_HEADER = chrome_copy_header_to_dict('''
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.8,en;q=0.6
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36
Accept: */*
Referer: http://stockpage.10jqka.com.cn/HQ_v4.html
Cookie: __utma=156575163.1843700306.1488352720.1499234323.1502172029.4; __utmc=156575163; __utmz=156575163.1488352720.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); spversion=20130314; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1507300869; Hm_lpvt_78c58f01938e4d85eaf619eae71b4ed1=1508464591; historystock=603189%7C*%7C300295%7C*%7C600839%7C*%7C000338%7C*%7C002194; log=; v=AREjaxfGLPcJoUDd5wHRp1QiKRaufoSAL_MpD_OlDDL35T_CO86VwL9CPa2D
Connection: keep-alive
''')

DEFAULT_BALANCE_SHEET_HEADER = chrome_copy_header_to_dict('''
Host: money.finance.sina.com.cn
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://vip.stock.finance.sina.com.cn/corp/go.php/vFD_CashFlow/stockid/000338/ctrl/part/displaytype/4.phtml
Cookie: U_TRS1=000000be.c95848c3.59817e10.a54886e2; U_TRS2=000000be.c96a48c3.59817e10.a91795e2; UOR=,vip.stock.finance.sina.com.cn,; ULV=1501658645426:2:2:2:182.148.114.190_1501658642.469995:1501658642409; SINAGLOBAL=182.148.114.190_1501658642.469991; Apache=182.148.114.190_1501658642.469995; _s_upa=1; SUB=_2A250hQ5nDeRhGedL4lQQ8ivPzziIHXVX83ivrDV_PUNbm9BeLXigkW8-niaOks2yNkw8lYo-TvoqGk6nRA..; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5J7vXaOMNYJQ0d27EZPWIF5NHD95QpSK.ceKzfe0BXWs4Dqcj.i--fi-zRiKnEi--fiKLhi-iWi--Xi-isi-88i--Ri-2piKyh; SCF=At4whqZZyjTBTvcLfR0tyqIpfHUX2VOK-qvBVHkbyahiCVcr4-8NjJQGHwCaTtkQJ0SPmrzvZARwtEkL1I_46z8.; ALF=1533194679; sso_info=v02m6alo5qztbaYloWum6akpp2WpaSPk4S1jpOYsYyjlLONg5DA; FINANCE2=f7634b1d12920e2763ffc0dc463ef6bb
Connection: keep-alive
Upgrade-Insecure-Requests: 1
''')

DEFAULT_SH_SUMMARY_HEADER = chrome_copy_header_to_dict('''
Host: query.sse.com.cn
Connection: keep-alive
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36
Accept: */*
Referer: http://www.sse.com.cn/market/stockdata/overview/day/
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.8,en;q=0.6
Cookie: yfx_c_g_u_id_10000042=_ck17122009304714819234313401740; VISITED_COMPANY_CODE=%5B%22000016%22%5D; VISITED_INDEX_CODE=%5B%22000016%22%5D; yfx_f_l_v_t_10000042=f_t_1513733447386__r_t_1515716891222__v_t_1515721033042__r_c_3; VISITED_MENU=%5B%228464%22%2C%229666%22%2C%229668%22%2C%229669%22%2C%228454%22%2C%228460%22%2C%229665%22%2C%228459%22%2C%229692%22%2C%228451%22%2C%228466%22%5D
''')

DEFAULT_SH_ETF_LIST_HEADER = chrome_copy_header_to_dict('''
Host: query.sse.com.cn
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
Accept: */*
Referer: http://www.sse.com.cn/assortment/fund/etf/list/
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: yfx_c_g_u_id_10000042=_ck19062609443812815766114343798; VISITED_COMPANY_CODE=%5B%22510300%22%5D; VISITED_FUND_CODE=%5B%22510300%22%5D; VISITED_MENU=%5B%228307%22%2C%228823%22%2C%228547%22%2C%228556%22%2C%228549%22%2C%2210848%22%2C%228550%22%5D; yfx_f_l_v_t_10000042=f_t_1561513478278__r_t_1561692626758__v_t_1561695738302__r_c_1
Connection: keep-alive
''')

EASTMONEY_ETF_NET_VALUE_HEADER = chrome_copy_header_to_dict('''
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
Referer: http://fund.eastmoney.com/
''')
