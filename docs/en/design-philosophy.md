## 统一性(Unity)
统一性使你能够愉快的思考  

比如投资标的的唯一标识,zvt里面定义如下
```
{security_type}_{exchange}_{code}
```
很自然的,你就知道stock_sz_000338,coin_binance_EOS/USDT代表什么.

比如Recorder,其对所有标的的记录提供了统一的抽象.  
比如get_kdata,其对所有的标的的使用方式都是一致的.  
比如TechnicalFactor,其对所有标的,所有级别的操作都是一致的.  
比如回测和实时交易,Trader提供了一致的处理方式.

## 分层(Layer)

分层的核心在于不同层次之间的协议,整个系统的稳定性在于协议的稳定性.
<p align="center"><img src='./imgs/architecture.png'/></p>

## 扩展性(Scalable)

- 很容易的在系统中添加数据,并自动获得其他模块的能力.
- 很容易实现自己的factor
- 很容易的扩展自己的trader