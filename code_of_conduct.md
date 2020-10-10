##  1. 命名
* snake_case适用于
  * variable(变量)
  * package(包)
  * module(模块)
  * function(函数)
  * method(方法)

* CamelCase适用于
  * class(类)

## 2. 对外接口
各module对外暴露的接口应显式声明于__all__,例子:

[contract模块](https://github.com/zvtvz/zvt/blob/master/zvt/contract/__init__.py)以此结尾:
```
__all__ = ['IntervalLevel', 'Mixin', 'NormalMixin', 'EntityMixin', 'NormalEntityMixin', 'zvt_context']
```

## 3. 引入接口
不要使用 from zvt.module import *,你要什么就import什么，不要污染。

## 4. 没了

No api is the best api.

Code as comment.