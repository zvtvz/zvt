## 支持的数据
## TODO:数据上传
```
from zvt.domain import *
```
<table>
  <tr>
    <th>db</th>
    <th>schema</th>
    <th>更新方法</th>
    <th>下载地址</th>
  </tr>

  <td rowspan="9">stock_meta</td>
  
  <tr>
    <td>Stock</td>
    <td>Stock.record_data(provider='joinquant')<br>Stock.record_data(provider='eastmoney')<br></td>
    <td rowspan="9">wait...</td>
  </tr>
  <tr>
    <td>Block</td>
    <td>Block.record_data(provider='sina')<br>Block.record_data(provider='eastmoney')</td>
  </tr>

  <tr>
    <td>BlockStock</td>
    <td>BlockStock.record_data(provider='sina')<br>BlockStock.record_data(provider='eastmoney')</td>
  </tr>
  <tr>
    <td>Etf</td>
    <td>Etf.record_data(provider='joinquant')</td>
  </tr>
  <tr>
    <td>EtfStock</td>
    <td>EtfStock.record_data(provider='joinquant')</td>
  </tr>
  <tr>
    <td>Index</td>
    <td>Index.record_data</td>
  </tr>

  <tr>
    <td>IndexStock</td>
    <td>IndexStock.record_data</td>
  </tr>

  <tr>
    <td>StockDetail</td>
    <td>StockDetail.record_data(provider='eastmoney')</td>
  </tr>

</table>