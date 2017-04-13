# 项目文档：绿色专利数统计

## 实现思路

项目需要统计2007-2014年间中国各省在工业、农林牧渔、建筑业以及交通运输业领域中的绿色专利数情况，数据来源为[中外专利信息服务平台](http://202.107.204.54:8080/cnipr/logoff.do?method=logoff) 。具体来说，最后需要呈现以下三个统计表图：

- 各年诸省绿色专利总数（2007-2014）
- 各年诸行业领域绿色专利总数（2007-2014）
- 各行业诸省绿色专利总数（2007-2014）

由于考察省份29个，且行业专利分类标签数总和达500余个，查询工作量巨大以至于无法手工完成，因此需要借助 *互联网爬虫* 模拟浏览器的查询请求来实现这一目的。每次查询，需要在[表单页面](http://202.107.204.54:8080/cnipr/main.do?method=gotoMain)填写三个表项，即 **公开公告日** （如，2008）、 **分类号或主分类号** （如，A01G23/00）以及 **国省代码** （如，上海）。

![Query_form](data/Query_form.png "Query_form")

需要注意的是：

1. 同一分类标签号（或分类标签号组合），将其填入分类号中得到的统计数总是多于将其填入主分类号中得到的统计数
2. 同一分类标签号，可以同时属于不同行业领域。如，工业、建筑业和交通运输业中都有分类标签号B63B1/36

基于以上两点，首先，每个分类标签号（或组合）需要分别填入分类号表项和主分类号表项中各做一次查询；其次，在统计 *各年诸省绿色专利总数* 时，需要首先得出四个行业的分类标签号的无重复并集，才能确保跨行业分类标签号不使统计数偏多。

爬虫的实现方式有很多种，也不乏成熟框架。鉴于本项目的要求并不复杂，决定在 *python 2* 环境下自己构建一个简易爬虫。爬虫总是在模拟浏览器重复干同样一件事情：

1. 前往首页登录，并存储cookie
2. 填写表单页中的三个表项，并提交查询请求
3. 获得查询响应的HTML文件，并从中解析统计数

一旦登录存储cookie，便一劳永逸。爬虫无需重复登录，而只是不断地重复步骤2及步骤3。

爬虫的健壮，永远离不开与网站反爬机制的斗争。尝试了以下做法，由于免费http代理服务器掉线率较高，第三条最终放弃实践。

- [x] 在http请求中加入header等信息，更接近于浏览器做出的请求
- [x] 每次解析完成后，强制爬虫休眠0.5秒
- [ ] 使用多个高匿代理服务器同时请求

统计表图的呈现，考虑导入excel并借助数据透视表来实现，这是一种比较方便快捷的做法。最终结果，参见文件 **统计报告.xlsx** 。

## 程序细节

无论是将分类标签号（或组合）填入分类号还是主分类号，是查询单个分类标签号还是行业（即特定标签号的 *or* 组合），程序均大同小异，只是将表单填写部分的表单参数稍作改动。程序原型请见附件，重要的地方都有必要注释，便于后期扩展。现就程序的各主要部分做详细说明。

#### 程序的运行

python是一种完全面向对象的语言，因此程序原型中只定义了一个名为 *Statistics* 的类。假设该类保存在名为 *crawler.py* 的文件中，则在同一目录下：

```python
import crawler
test = crawler.Statistics()
```

继而，你可以使用该类的两种方法，一是 *getPage()*，二是 *getResult()* 。前者进行单次查询，即返回特定（公开公告日、国省代码、标签号或其组合）组合的绿色专利统计数。

```python
print test.getPage('2013','江苏','A01G23/00+or+A01G25/00')
```

上面的命令将给出江苏省2013年属于 *A01G23/00* 或 *A01G25/00* 的绿色专利的总数。

**注意**  
- 作为参数传递给 *getPage()* 方法时，如果查询分类标签号组合，则各分类标签号之间用 *+or+* 连接
- 在网站手动验证查询时，如果查询分类标签号组合，则各分类标签号之间用 *or* 连接
- 各行业领域的分类标签号“or组合”，请见附件。

第二种方法 *getResult()* 则直接给出最终结果，即 *（年份 省份 行业 绿色专利数）* 的查询结果列表。

```python
test.getResult()
```

#### 分类标签号并集

- 并集初始化为空
- 遍历每个行业的每个分类标签号
  - 如果该标签号不在并集中，则新加入并集，并写入文件
  - 否则，继续遍历
- 得到所有行业标签号的无重复并集，将其构造成“or组合”字符串参数，用以检索

```python
fileList = ['data/industry.txt', 'data/agriculture.txt', 'data/construction.txt', 'data/transportation.txt']
union = []
f0 = open('union.txt', 'w')
for fileName in fileList:
    f1 = open(fileName, 'r')
    for lineInFile in f1:
        if lineInFile[:-1] not in union:
            union.append(lineInFile[:-1])
            f0.write(lineInFile)
    f1.close()
f0.close()
```

#### Cookie的使用

python的优势之一在于网络编程，这里直接使用 [urllib2, extensible library for opening URLs](https://docs.python.org/2/library/urllib2.html?highlight=urllib2#module-urllib2) 和 [cookielib, Cookie handling for HTTP clients](https://docs.python.org/2/library/cookielib.html?highlight=cookielib#module-cookielib) 这两个库。核心在于构建一个自动储存并运用Cookie的url连接器。

```python
import urllib2
import cookielib

cookies = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))  # 构建opener
opener.open(urllib2.Request(url = <url>, data = <data>, headers = <headers>))  # 使用opener
```

#### 正则表达式

之所以使用正则表达式，是因为在填写表单和解析结果时，它具有无可比拟的优越性。比如，在一堆只有机器有兴趣看的用来表示表单的url符号中，需要将特定年份插入进去，即 *“txtD=&”* （年份为空）变为 *“txtD=2008&”* （年份为2008），若使用正则表达式标准库 [re, Regular expression operations](https://docs.python.org/2/library/re.html?highlight=re#module-re) ，只需一句命令：

```python
import re
re.sub(re.compile('txtD=[^&]*&'), 'txtD='+ year +'&', queryData)
```

类似地，在解析结果时，为了在一大段HTML文件页面中得到统计数：

```python
import re
print re.findall('\d+', re.findall('本次.*\d+条', response.read())[0])[0]
```

#### 表单细节

已经提到，将标签号或其组合分别填入分类号、主分类号，结果会不同。事实上，两者提交给网站的表单参数也存在差别，不加注意，则无法得到正确结果。

在填入分类号时，分类号对应的表项为 **txtH** ，且参数 *strWhere* 中的关键字为 **sic** ：

```python
re.sub(re.compile('txtH=[^&]*&'), 'txtH='+ label +'&', queryData)
re.sub(re.compile('strWhere=[^&]*&'), 'strWhere=pd=('+year+')+and+sic=('+label+')+and+co=('+place+')'+'&', queryData)
```

在填入分类号时，分类号对应的表项为 **txtG** ，且参数 *strWhere* 中的关键字为 **pic** ：

```python
re.sub(re.compile('txtG=[^&]*&'), 'txtG='+ label +'&', queryData)
re.sub(re.compile('strWhere=[^&]*&'), 'strWhere=pd=('+year+')+and+pic=('+label+')+and+co=('+place+')'+'&', queryData)
```

## 附件

#### 各行业分类标签号的“or组合”

```
工业
A01G23/00 or A01G25/00 or A01N25/00 or A01N27/00 or A01N29/00 or A01N31/00 or A01N33/00 or A01N35/00 or A01N37/00 or A01N39/00 or A01N41/00 or A01N43/00 or A01N45/00 or A01N47/00 or A01N49/00 or A01N51/00 or A01N53/00 or A01N55/00 or A01N57/00 or A01N59/00 or A01N61/00 or A01N63/00 or A01N65/00 or A43B1/12 or A43B21/14 or A61L11/00 or A62D101/00 or A62D3/00 or A62D3/02 or B01D45/00 or B01D46/00 or B01D47/00 or B01D48/00 or B01D49/00 or B01D50/00 or B01D51/00 or B01D53 or B03B9/06 or B03C3/00 or B09B or B09C or B22F8/00 or B29B17/00 or B60K16/00 or B60K6/00 or B60K6/10 or B60K6/20 or B60K6/30 or B60K6/28 or B60L11/16 or B60L11/18 or B60L3/00 or B60L7/10 or B60L7/12 or B60L7/14 or B60L7/16 or B60L7/18 or B60L7/20 or B60L7/22 or B60L8/00 or B60L9/00 or B60W10/26 or B60W20/00 or B62D35/00 or B62D35/02 or B62D67/00 or B62K or B62M1/00 or B62M3/00 or B62M5/00 or B62M6/00 or B63B1/34 or B63B1/36 or B63B1/38 or B63B1/40 or B63B35/00 or B63B35/32 or B63H13/00 or B63H16/00 or B63H19/02 or B63H19/04 or B63H21/18 or B63H9/00 or B63J4/00 or B64G1/44 or B65F or B65G5/00 or C01B31/20 or C01B33/02 or C02F or C04B18/04 or C04B18/06 or C04B18/08 or C04B18/10 or C04B7/24 or C04B7/26 or C04B7/28 or C04B7/30 or C05F or C07C67/00 or C07C69/00 or C08J11 or C09K11/01 or C09K17/00 or C09K3/22 or C09K3/32 or C09K5/00 or C10B21/18 or C10B53/00 or C10B53/02 or C10G or C10J or C10L1/00 or C10L1/14 or C10L1/182 or C10L1/19 or C10L1/02 or C10L10/06 or C10L10/02 or C10L3/00 or C10L5/00 or C10L5/40 or C10L5/42 or C10L5/44 or C10L5/46 or C10L5/48 or C10L9/00 or C11B11/00 or C11B13/00 or C11B13/02 or C11B13/04 or C11C3/10 or C12M1/107 or C12N1/13 or C12N1/15 or C12N1/21 or C12N5/10 or C12N15/00 or C12N9/24 or C12P5/02 or C12P7/06 or C12P7/08 or C12P7/10 or C12P7/12 or C12P7/14 or C12P7/64 or C14C3/32 or C21B3/04 or C21B5/06 or C21B7/22 or C21C5/38 or C21C5/38 or C22B7/00 or C22B7/02 or C22B7/04 or C22B19/30 or C22B25/06 or C23C14/14 or C25C16/24 or C25C1/00 or C30B29/06 or D21C11/00 or D21F5/20 or D21B1/08 or D21B1/32 or D01F13/00 or D01F13/02 or D01F13/04 or D01G11/00 or D21C5/02 or E02B15/04 or E02B9/00 or E02B9/02 or E02B9/04 or E02B9/06 or E02B9/08 or E02D3/00 or E03F or E04B1/62 or E04B1/74 or E04B1/76 or E04B1/78 or E04B1/80 or E04B1/88 or E04B1/90 or E04B2/00 or E04B5/00 or E04B7/00 or E04B9/00 or E04C1/40 or E04C1/41 or E04C2/284 or E04C2/288 or E04C2/292 or E04C2/296 or E04D1/28 or E04D13/00 or E04D13/16 or E04D13/18 or E04D3/35 or E04F13/08 or E04F15/18 or E04H1/00 or E04H12/00 or E06B3/263 or E21B41/00 or E21B43/16 or E21F17/16 or F01K or F01N5/00 or F01N9/00 or F01N3 or F02B43/00 or F02B75/10 or F02C1/05 or F02C3/28 or F02C6/18 or F02G5/00 or F02G5/02 or F02G5/04 or F02M21/02 or F02M27/02 or F03B or F03C or F03D or F03G4/00 or F03G4/02 or F03G4/04 or F03G4/06 or F03G5 or F03G6/00 or F03G6/02 or F03G6/04 or F03G6/06 or F03G7/04 or F03G7/05 or F03G7/08 or F16H48/00 or F16H48/05 or F16H48/06 or F16H48/08 or F16H48/10 or F16H48/11 or F16H48/12 or F16H48/14 or F16H48/16 or F16H48/18 or F16H48/19 or F16H48/20 or F16H48/22 or F16H48/24 or F16H48/26 or F16H48/27 or F16H48/28 or F16H48/285 or F16H48/29 or F16H48/295 or F16H48/30 or F16H1/00 or F16H3/00 or F16H3/02 or F16H3/04 or F16H3/06 or F16H3/08 or F16H3/083 or F16H3/085 or F16H3/087 or F16H3/089 or F16H3/091 or F16H3/093 or F16H3/095 or F16H3/097 or F16H3/10 or F16H3/12 or F16H3/14 or F16H3/16 or F16H3/18 or F16H3/20 or F16H3/22 or F16H3/24 or F16H3/26 or F16H3/28 or F16H3/30 or F16H3/32 or F16H3/34 or F16H3/36 or F16H3/38 or F16H3/40 or F16H3/42 or F16H3/44 or F16H3/46 or F16H3/48 or F16H3/50 or F16H3/52 or F16H3/54 or F21K99/00 or F21L4/00 or F21L4/02 or F21S9/03 or F22B1/00 or F22B1/02 or F23B80/02 or F23B90/00 or F23C9/00 or F23G or F23J15/00 or F23J7/00 or F24D11/02 or F24D15/04 or F24D17/00 or F24D17/02 or F24D3/00 or F24D5/00 or F24D11/00 or F24D19/00 or F24F12/00 or F24F5/00 or F24H4/00 or F24H7/00 or F24J1/00 or F24J3/00 or F24J3/06 or F24J2 or F24J3/08 or F25B27/00 or F25B27/02 or F25B30/00 or F25B30/06 or F25J3/02 or F26B3/00 or F26B3/28 or F27B1/18 or F27B15/12 or F27D17/00 or F28D17/00 or F28D19/00 or F28D20/00 or F28D20/02 or G01R or G02B7/183 or G05F1/67 or G08B21/12 or G08G or H01G9/155 or H01G9/20 or H01J9/50 or H01J9/52 or H01L25/00 or H01L25/03 or H01L25/16 or H01L25/18 or H01L27/142 or H01L27/30 or H01L31/00 or H01L31/02 or H01L31/0203 or H01L31/0216 or H01L31/0224 or H01L31/0232 or H01L31/0236 or H01L31/024 or H01L31/0248 or H01L31/0256 or H01L31/0264 or H01L31/0272 or H01L31/028 or H01L31/0288 or H01L31/0296 or H01L31/0304 or H01L31/0312 or H01L31/032 or H01L31/0328 or H01L31/0336 or H01L31/0352 or H01L31/036 or H01L31/0368 or H01L31/0376 or H01L31/0384 or H01L31/0392 or H01L31/04 or H01L31/041 or H01L31/042 or H01L31/042 or H01L31/043 or H01L31/044 or H01L31/0443 or H01L31/0445 or H01L31/046 or H01L31/0463 or H01L31/0465 or H01L31/0468 or H01L31/047 or H01L31/0475 or H01L31/048 or H01L31/049 or H01L31/05 or H01L31/052 or H01L31/0525 or H01L31/053 or H01L31/054 or H01L31/055 or H01L31/056 or H01L31/058 or H01L31/06 or H01L31/061 or H01L31/062 or H01L31/065 or H01L31/068 or H01L31/0687 or H01L31/0693 or H01L31/07 or H01L31/072 or H01L31/0725 or H01L31/073 or H01L31/0735 or H01L31/074 or H01L31/0747 or H01L31/0749 or H01L31/075 or H01L31/076 or H01L31/077 or H01L31/078 or H01L33 or H01L51/42 or H01L51/44 or H01L51/46 or H01L51/48 or H01M10/44 or H01M10/46 or H01M12/00 or H01M12/02 or H01M12/06 or H01M12/08 or H01M14/00 or H01M2/00 or H01M2/02 or H01M2/04 or H01M4/86 or H01M4/88 or H01M4/90 or H01M4/92 or H01M4/96 or H01M4/98 or H01M6/52 or H01M10/54 or H01M8/00 or H01M8/008 or H01M8/02 or H01M8/0202 or H01M8/0204 or H01M8/0206 or H01M8/0208 or H01M8/021 or H01M8/0213 or H01M8/0215 or H01M8/0217 or H01M8/0221 or H01M8/0223 or H01M8/0226 or H01M8/0228 or H01M8/023 or H01M8/0232 or H01M8/0234 or H01M8/0236 or H01M8/0239 or H01M8/0241 or H01M8/0243 or H01M8/0245 or H01M8/0247 or H02J or H02K29/08 or H02K49/10 or H02K7/18 or H02N10/00 or H02N6/00 or H05B33/00

农林牧渔
A01G23/00 or A01G25/00 or A01H or A01N25/00 or A01N27/00 or A01N29/00 or A01N31/00 or A01N33/00 or A01N35/00 or A01N37/00 or A01N39/00 or A01N41/00 or A01N43/00 or A01N45/00 or A01N47/00 or A01N49/00 or A01N51/00 or A01N53/00 or A01N55/00 or A01N57/00 or A01N59/00 or A01N61/00 or A01N63/00 or A01N65/00 or C09K11/01 or C09K17/00 or C09K3/22 or C09K3/32 or C09K5/00 or C12N1/13 or C12N1/15 or C12N1/21 or C12N5/10 or C12N15/00 or C12N9/24

建筑业
B63B1/34 or B63B1/36 or B63B1/38 or B63B1/40 or B63B35/00 or B63B35/32 or C21B3/04 or C21B5/06 or C21B7/22 or E02B15/04 or E02B9/00 or E02B9/02 or E02B9/04 or E02B9/06 or E02B9/08 or E02D3/00 or E03C1/12 or E03F or E04D1/28 or E04D13/00 or E04D13/16 or E04D13/18 or E04D3/35 or E04F13/08 or E04F15/18 or E04H1/00 or E04H12/00 or E21F17/16 or F24D11/02 or F24D15/04 or F24D17/00 or F24D17/02 or F24D3/00 or F24D5/00 or F24D11/00 or F24D19/00 or F24F12/00 or F24F5/00

交通运输
B60K16/00 or B60K6/00 or B60K6/10 or B60K6/20 or B60K6/30 or B60K6/28 or B60L11/16 or B60L11/18 or B60L3/00 or B60L7/10 or B60L7/12 or B60L7/14 or B60L7/16 or B60L7/18 or B60L7/20 or B60L7/22 or B60L8/00 or B60L9/00 or B60W10/26 or B60W20/00 or B61 or B62D35/00 or B62D35/02 or B62D67/00 or B62K or B62M1/00 or B62M3/00 or B62M5/00 or B62M6/00 or B63B1/34 or B63B1/36 or B63B1/38 or B63B1/40 or B63B35/00 or B63B35/32 or B63H13/00 or B63H16/00 or B63H19/02 or B63H19/04 or B63H21/18 or B63H9/00 or B63J4/00 or B64G1/44 or B65F or B65G5/00
```

#### 所有分类标签号并集的“or组合”

```
A01G23/00 or A01G25/00 or A01N25/00 or A01N27/00 or A01N29/00 or A01N31/00 or A01N33/00 or A01N35/00 or A01N37/00 or A01N39/00 or A01N41/00 or A01N43/00 or A01N45/00 or A01N47/00 or A01N49/00 or A01N51/00 or A01N53/00 or A01N55/00 or A01N57/00 or A01N59/00 or A01N61/00 or A01N63/00 or A01N65/00 or A43B1/12 or A43B21/14 or A61L11/00 or A62D101/00 or A62D3/00 or A62D3/02 or B01D45/00 or B01D46/00 or B01D47/00 or B01D48/00 or B01D49/00 or B01D50/00 or B01D51/00 or B01D53 or B03B9/06 or B03C3/00 or B09B or B09C or B22F8/00 or B29B17/00 or B60K16/00 or B60K6/00 or B60K6/10 or B60K6/20 or B60K6/30 or B60K6/28 or B60L11/16 or B60L11/18 or B60L3/00 or B60L7/10 or B60L7/12 or B60L7/14 or B60L7/16 or B60L7/18 or B60L7/20 or B60L7/22 or B60L8/00 or B60L9/00 or B60W10/26 or B60W20/00 or B62D35/00 or B62D35/02 or B62D67/00 or B62K or B62M1/00 or B62M3/00 or B62M5/00 or B62M6/00 or B63B1/34 or B63B1/36 or B63B1/38 or B63B1/40 or B63B35/00 or B63B35/32 or B63H13/00 or B63H16/00 or B63H19/02 or B63H19/04 or B63H21/18 or B63H9/00 or B63J4/00 or B64G1/44 or B65F or B65G5/00 or C01B31/20 or C01B33/02 or C02F or C04B18/04 or C04B18/06 or C04B18/08 or C04B18/10 or C04B7/24 or C04B7/26 or C04B7/28 or C04B7/30 or C05F or C07C67/00 or C07C69/00 or C08J11 or C09K11/01 or C09K17/00 or C09K3/22 or C09K3/32 or C09K5/00 or C10B21/18 or C10B53/00 or C10B53/02 or C10G or C10J or C10L1/00 or C10L1/14 or C10L1/182 or C10L1/19 or C10L1/02 or C10L10/06 or C10L10/02 or C10L3/00 or C10L5/00 or C10L5/40 or C10L5/42 or C10L5/44 or C10L5/46 or C10L5/48 or C10L9/00 or C11B11/00 or C11B13/00 or C11B13/02 or C11B13/04 or C11C3/10 or C12M1/107 or C12N1/13 or C12N1/15 or C12N1/21 or C12N5/10 or C12N15/00 or C12N9/24 or C12P5/02 or C12P7/06 or C12P7/08 or C12P7/10 or C12P7/12 or C12P7/14 or C12P7/64 or C14C3/32 or C21B3/04 or C21B5/06 or C21B7/22 or C21C5/38 or C22B7/00 or C22B7/02 or C22B7/04 or C22B19/30 or C22B25/06 or C23C14/14 or C25C16/24 or C25C1/00 or C30B29/06 or D21C11/00 or D21F5/20 or D21B1/08 or D21B1/32 or D01F13/00 or D01F13/02 or D01F13/04 or D01G11/00 or D21C5/02 or E02B15/04 or E02B9/00 or E02B9/02 or E02B9/04 or E02B9/06 or E02B9/08 or E02D3/00 or E03F or E04B1/62 or E04B1/74 or E04B1/76 or E04B1/78 or E04B1/80 or E04B1/88 or E04B1/90 or E04B2/00 or E04B5/00 or E04B7/00 or E04B9/00 or E04C1/40 or E04C1/41 or E04C2/284 or E04C2/288 or E04C2/292 or E04C2/296 or E04D1/28 or E04D13/00 or E04D13/16 or E04D13/18 or E04D3/35 or E04F13/08 or E04F15/18 or E04H1/00 or E04H12/00 or E06B3/263 or E21B41/00 or E21B43/16 or E21F17/16 or F01K or F01N5/00 or F01N9/00 or F01N3 or F02B43/00 or F02B75/10 or F02C1/05 or F02C3/28 or F02C6/18 or F02G5/00 or F02G5/02 or F02G5/04 or F02M21/02 or F02M27/02 or F03B or F03C or F03D or F03G4/00 or F03G4/02 or F03G4/04 or F03G4/06 or F03G5 or F03G6/00 or F03G6/02 or F03G6/04 or F03G6/06 or F03G7/04 or F03G7/05 or F03G7/08 or F16H48/00 or F16H48/05 or F16H48/06 or F16H48/08 or F16H48/10 or F16H48/11 or F16H48/12 or F16H48/14 or F16H48/16 or F16H48/18 or F16H48/19 or F16H48/20 or F16H48/22 or F16H48/24 or F16H48/26 or F16H48/27 or F16H48/28 or F16H48/285 or F16H48/29 or F16H48/295 or F16H48/30 or F16H1/00 or F16H3/00 or F16H3/02 or F16H3/04 or F16H3/06 or F16H3/08 or F16H3/083 or F16H3/085 or F16H3/087 or F16H3/089 or F16H3/091 or F16H3/093 or F16H3/095 or F16H3/097 or F16H3/10 or F16H3/12 or F16H3/14 or F16H3/16 or F16H3/18 or F16H3/20 or F16H3/22 or F16H3/24 or F16H3/26 or F16H3/28 or F16H3/30 or F16H3/32 or F16H3/34 or F16H3/36 or F16H3/38 or F16H3/40 or F16H3/42 or F16H3/44 or F16H3/46 or F16H3/48 or F16H3/50 or F16H3/52 or F16H3/54 or F21K99/00 or F21L4/00 or F21L4/02 or F21S9/03 or F22B1/00 or F22B1/02 or F23B80/02 or F23B90/00 or F23C9/00 or F23G or F23J15/00 or F23J7/00 or F24D11/02 or F24D15/04 or F24D17/00 or F24D17/02 or F24D3/00 or F24D5/00 or F24D11/00 or F24D19/00 or F24F12/00 or F24F5/00 or F24H4/00 or F24H7/00 or F24J1/00 or F24J3/00 or F24J3/06 or F24J2 or F24J3/08 or F25B27/00 or F25B27/02 or F25B30/00 or F25B30/06 or F25J3/02 or F26B3/00 or F26B3/28 or F27B1/18 or F27B15/12 or F27D17/00 or F28D17/00 or F28D19/00 or F28D20/00 or F28D20/02 or G01R or G02B7/183 or G05F1/67 or G08B21/12 or G08G or H01G9/155 or H01G9/20 or H01J9/50 or H01J9/52 or H01L25/00 or H01L25/03 or H01L25/16 or H01L25/18 or H01L27/142 or H01L27/30 or H01L31/00 or H01L31/02 or H01L31/0203 or H01L31/0216 or H01L31/0224 or H01L31/0232 or H01L31/0236 or H01L31/024 or H01L31/0248 or H01L31/0256 or H01L31/0264 or H01L31/0272 or H01L31/028 or H01L31/0288 or H01L31/0296 or H01L31/0304 or H01L31/0312 or H01L31/032 or H01L31/0328 or H01L31/0336 or H01L31/0352 or H01L31/036 or H01L31/0368 or H01L31/0376 or H01L31/0384 or H01L31/0392 or H01L31/04 or H01L31/041 or H01L31/042 or H01L31/043 or H01L31/044 or H01L31/0443 or H01L31/0445 or H01L31/046 or H01L31/0463 or H01L31/0465 or H01L31/0468 or H01L31/047 or H01L31/0475 or H01L31/048 or H01L31/049 or H01L31/05 or H01L31/052 or H01L31/0525 or H01L31/053 or H01L31/054 or H01L31/055 or H01L31/056 or H01L31/058 or H01L31/06 or H01L31/061 or H01L31/062 or H01L31/065 or H01L31/068 or H01L31/0687 or H01L31/0693 or H01L31/07 or H01L31/072 or H01L31/0725 or H01L31/073 or H01L31/0735 or H01L31/074 or H01L31/0747 or H01L31/0749 or H01L31/075 or H01L31/076 or H01L31/077 or H01L31/078 or H01L33 or H01L51/42 or H01L51/44 or H01L51/46 or H01L51/48 or H01M10/44 or H01M10/46 or H01M12/00 or H01M12/02 or H01M12/06 or H01M12/08 or H01M14/00 or H01M2/00 or H01M2/02 or H01M2/04 or H01M4/86 or H01M4/88 or H01M4/90 or H01M4/92 or H01M4/96 or H01M4/98 or H01M6/52 or H01M10/54 or H01M8/00 or H01M8/008 or H01M8/02 or H01M8/0202 or H01M8/0204 or H01M8/0206 or H01M8/0208 or H01M8/021 or H01M8/0213 or H01M8/0215 or H01M8/0217 or H01M8/0221 or H01M8/0223 or H01M8/0226 or H01M8/0228 or H01M8/023 or H01M8/0232 or H01M8/0234 or H01M8/0236 or H01M8/0239 or H01M8/0241 or H01M8/0243 or H01M8/0245 or H01M8/0247 or H02J or H02K29/08 or H02K49/10 or H02K7/18 or H02N10/00 or H02N6/00 or H05B33/00 or A01H or E03C1/12 or B61
```
